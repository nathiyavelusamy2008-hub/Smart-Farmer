import math, os, sqlite3
from functools import wraps
from flask import Flask, render_template, request, jsonify, session
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database import get_db, init_db
from services.market_service import list_market_prices
from services.recommendation_service import recommend_markets

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

def err(message, status=400): return jsonify({"error": message}), status
def get_json():
    value = request.get_json(silent=True)
    return value if isinstance(value, dict) else None
def user_now():
    uid = session.get("user_id")
    if not uid: return None
    db = get_db()
    row = db.execute("SELECT id,name,phone,role,location FROM users WHERE id=?", (uid,)).fetchone()
    db.close()
    return dict(row) if row else None
def need_login(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = user_now()
            if not user: return err("Please log in first.",401)
            if role and user["role"] != role: return err(f"This action is for {role}s only.",403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator
def positive(value):
    if isinstance(value,bool): return None
    try:
        n=float(value)
        return n if math.isfinite(n) and n>0 else None
    except (TypeError,ValueError): return None

@app.after_request
def headers(response):
    response.headers.setdefault("X-Content-Type-Options","nosniff")
    response.headers.setdefault("X-Frame-Options","DENY")
    response.headers.setdefault("Referrer-Policy","same-origin")
    return response

@app.get("/")
def home(): return render_template("index.html")
@app.get("/login")
def login_page(): return render_template("login.html")
@app.get("/register")
def register_page(): return render_template("register.html")
@app.get("/dashboard")
def dashboard_page(): return render_template("dashboard.html")

@app.get("/api/me")
def me(): return jsonify({"user":user_now()})

@app.post("/api/register")
def register():
    d=get_json()
    if not d: return err("Send valid JSON.")
    name=str(d.get("name","")).strip(); phone=str(d.get("phone","")).strip()
    password=str(d.get("password","")); role=str(d.get("role","")).lower().strip()
    location=str(d.get("location","")).strip()
    if not 2<=len(name)<=80: return err("Name must contain 2–80 characters.")
    if not phone.isdigit() or not 10<=len(phone)<=15: return err("Phone must contain 10–15 digits.")
    if len(password)<8: return err("Password must be at least 8 characters.")
    if role not in ("farmer","buyer"): return err("Choose farmer or buyer.")
    if not location or len(location)>100: return err("Enter a valid location.")
    db=get_db()
    try:
        cur=db.execute("INSERT INTO users(name,phone,password_hash,role,location) VALUES(?,?,?,?,?)",
                       (name,phone,generate_password_hash(password),role,location))
        db.commit(); session.clear(); session["user_id"]=cur.lastrowid
        return jsonify({"message":"Account created successfully.","user":user_now()}),201
    except sqlite3.IntegrityError: return err("That phone number is already registered.",409)
    finally: db.close()

@app.post("/api/login")
def login():
    d=get_json()
    if not d: return err("Send valid JSON.")
    db=get_db(); row=db.execute("SELECT id,password_hash FROM users WHERE phone=?",(str(d.get("phone","")).strip(),)).fetchone(); db.close()
    if not row or not check_password_hash(row["password_hash"],str(d.get("password",""))):
        return err("Invalid phone number or password.",401)
    session.clear(); session["user_id"]=row["id"]
    return jsonify({"message":"Login successful.","user":user_now()})

@app.post("/api/logout")
def logout(): session.clear(); return jsonify({"message":"Logged out."})

@app.get("/api/dashboard")
def dashboard():
    db=get_db()
    listings=db.execute("SELECT COUNT(*) FROM crops WHERE status='active' AND available_quantity>0").fetchone()[0]
    markets=db.execute("SELECT COUNT(*) FROM market_prices").fetchone()[0]
    recent=db.execute("SELECT c.id,c.name,c.available_quantity,c.expected_price,c.location,u.name farmer_name FROM crops c JOIN users u ON u.id=c.farmer_id WHERE c.status='active' AND c.available_quantity>0 ORDER BY c.created_at DESC LIMIT 5").fetchall()
    db.close()
    return jsonify({"active_listings":listings,"market_prices":markets,"recent_crops":[dict(r) for r in recent]})

@app.get("/api/crops")
def crops():
    crop=request.args.get("crop","").strip(); location=request.args.get("location","").strip()
    sql="SELECT c.*,u.name farmer_name FROM crops c JOIN users u ON u.id=c.farmer_id WHERE c.status='active' AND c.available_quantity>0"
    params=[]
    if crop: sql+=" AND c.name LIKE ?"; params.append(f"%{crop}%")
    if location: sql+=" AND c.location LIKE ?"; params.append(f"%{location}%")
    max_price=request.args.get("max_price","").strip()
    if max_price:
        try:
            n=float(max_price)
            if n<0: return err("Maximum price cannot be negative.")
            sql+=" AND c.expected_price<=?"; params.append(n)
        except ValueError: return err("Maximum price must be numeric.")
    sql+=" ORDER BY c.created_at DESC"
    db=get_db(); rows=db.execute(sql,params).fetchall(); db.close()
    return jsonify([dict(r) for r in rows])

@app.post("/api/crops")
@need_login("farmer")
def create_crop():
    user=user_now(); d=get_json()
    if not d: return err("Send valid JSON.")
    name=str(d.get("name","")).strip(); harvest=str(d.get("harvest_date","")).strip()
    grade=str(d.get("quality_grade","")).strip(); location=str(d.get("location",user["location"])).strip()
    description=str(d.get("description","")).strip()[:500]
    quantity=positive(d.get("quantity")); price=positive(d.get("expected_price"))
    if not name or len(name)>80 or not harvest or not grade or not location: return err("Complete all required crop fields.")
    if not quantity or not price: return err("Quantity and price must be positive numbers.")
    db=get_db()
    cur=db.execute("INSERT INTO crops(farmer_id,name,quantity,available_quantity,expected_price,harvest_date,quality_grade,location,description) VALUES(?,?,?,?,?,?,?,?,?)",
                   (user["id"],name,quantity,quantity,price,harvest,grade,location,description))
    db.commit(); cid=cur.lastrowid; db.close()
    return jsonify({"message":"Crop listing created.","listing_id":cid}),201

@app.get("/api/markets")
def markets(): return jsonify(list_market_prices(request.args.get("crop","").strip()))

@app.post("/api/offers")
@need_login("buyer")
def create_offer():
    user=user_now(); d=get_json()
    if not d: return err("Send valid JSON.")
    try: crop_id=int(d.get("crop_id"))
    except (TypeError,ValueError): return err("Valid crop listing ID required.")
    price=positive(d.get("offered_price")); quantity=positive(d.get("quantity"))
    if not price or not quantity: return err("Offer price and quantity must be positive.")
    db=get_db(); crop=db.execute("SELECT * FROM crops WHERE id=? AND status='active'",(crop_id,)).fetchone()
    if not crop: db.close(); return err("Crop listing not found.",404)
    if crop["farmer_id"]==user["id"]: db.close(); return err("Cannot offer on your own listing.",403)
    if quantity>crop["available_quantity"]: db.close(); return err("Quantity exceeds current availability.")
    cur=db.execute("INSERT INTO offers(crop_id,buyer_id,offered_price,quantity) VALUES(?,?,?,?)",(crop_id,user["id"],price,quantity))
    db.commit(); oid=cur.lastrowid; db.close()
    return jsonify({"message":"Offer submitted.","offer_id":oid}),201

@app.get("/api/offers")
@need_login()
def offers():
    u=user_now(); db=get_db()
    if u["role"]=="buyer":
        rows=db.execute("SELECT o.*,c.name crop_name,c.location,u.name farmer_name FROM offers o JOIN crops c ON c.id=o.crop_id JOIN users u ON u.id=c.farmer_id WHERE o.buyer_id=? ORDER BY o.created_at DESC",(u["id"],)).fetchall()
    else:
        rows=db.execute("SELECT o.*,c.name crop_name,u.name buyer_name FROM offers o JOIN crops c ON c.id=o.crop_id JOIN users u ON u.id=o.buyer_id WHERE c.farmer_id=? ORDER BY o.created_at DESC",(u["id"],)).fetchall()
    db.close(); return jsonify([dict(r) for r in rows])

@app.patch("/api/offers/<int:offer_id>")
@need_login("farmer")
def update_offer(offer_id):
    u=user_now(); d=get_json() or {}; status=str(d.get("status","")).lower()
    if status not in ("accepted","rejected"): return err("Status must be accepted or rejected.")
    db=get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        o=db.execute("SELECT o.*,c.farmer_id,c.available_quantity,c.status crop_status FROM offers o JOIN crops c ON c.id=o.crop_id WHERE o.id=?",(offer_id,)).fetchone()
        if not o: db.rollback(); return err("Offer not found.",404)
        if o["farmer_id"]!=u["id"]: db.rollback(); return err("You cannot manage this offer.",403)
        if o["status"]!="pending": db.rollback(); return err("Offer already processed.",409)
        if status=="accepted":
            if o["crop_status"]!="active" or o["quantity"]>o["available_quantity"]:
                db.rollback(); return err("Not enough quantity remains.",409)
            db.execute("UPDATE crops SET available_quantity=available_quantity-?,status=CASE WHEN available_quantity-?<=0 THEN 'sold' ELSE status END WHERE id=?",(o["quantity"],o["quantity"],o["crop_id"]))
            db.execute("INSERT INTO orders(offer_id,farmer_id,buyer_id,crop_id,agreed_price,quantity) VALUES(?,?,?,?,?,?)",(offer_id,u["id"],o["buyer_id"],o["crop_id"],o["offered_price"],o["quantity"]))
        db.execute("UPDATE offers SET status=? WHERE id=?",(status,offer_id)); db.commit()
        return jsonify({"message":f"Offer {status}.","status":status})
    except sqlite3.IntegrityError:
        db.rollback(); return err("Conflicting order; refresh and try again.",409)
    finally: db.close()

@app.post("/api/calculator")
def calculator():
    d=get_json()
    if not d: return err("Send valid JSON.")
    q=positive(d.get("quantity")); p=positive(d.get("price"))
    try:
        transport=float(d.get("transport_cost",0)); other=float(d.get("other_expenses",0))
        if not all(math.isfinite(x) and x>=0 for x in (transport,other)): raise ValueError()
    except (TypeError,ValueError): return err("Expenses must be non-negative numbers.")
    if not q or not p: return err("Quantity and price must be positive.")
    gross=q*p
    return jsonify({"gross_amount":round(gross,2),"transport_cost":round(transport,2),"other_expenses":round(other,2),"net_amount":round(gross-transport-other,2),"note":"Estimate is before production costs."})

@app.get("/api/recommendations")
def recommendations():
    crop=request.args.get("crop","").strip()
    try:
        q=float(request.args.get("quantity","1")); rate=float(request.args.get("transport_cost_per_km","0")); other=float(request.args.get("other_expenses","0"))
        if not all(math.isfinite(x) for x in (q,rate,other)) or q<=0 or rate<0 or other<0: raise ValueError()
    except ValueError: return err("Quantity must be positive; expenses must be non-negative.")
    opts=recommend_markets(crop,q,rate,other)
    return jsonify({"options":opts,"best_option":opts[0] if opts else None,"note":"Uses demonstration prices, not live market data."})

@app.get("/api/orders")
@need_login()
def orders():
    u=user_now(); db=get_db()
    if u["role"]=="farmer":
        rows=db.execute("SELECT o.*,c.name crop_name,b.name buyer_name,f.name farmer_name FROM orders o JOIN crops c ON c.id=o.crop_id JOIN users b ON b.id=o.buyer_id JOIN users f ON f.id=o.farmer_id WHERE o.farmer_id=? ORDER BY o.created_at DESC",(u["id"],)).fetchall()
    else:
        rows=db.execute("SELECT o.*,c.name crop_name,b.name buyer_name,f.name farmer_name FROM orders o JOIN crops c ON c.id=o.crop_id JOIN users b ON b.id=o.buyer_id JOIN users f ON f.id=o.farmer_id WHERE o.buyer_id=? ORDER BY o.created_at DESC",(u["id"],)).fetchall()
    db.close(); return jsonify([dict(r) for r in rows])

@app.patch("/api/orders/<int:order_id>")
@need_login("farmer")
def update_order(order_id):
    u=user_now(); d=get_json() or {}; status=str(d.get("status","")).lower()
    if status not in ("confirmed","processing","completed","cancelled"): return err("Invalid order status.")
    db=get_db(); row=db.execute("SELECT * FROM orders WHERE id=? AND farmer_id=?",(order_id,u["id"])).fetchone()
    if not row: db.close(); return err("Order not found or unauthorized.",404)
    db.execute("UPDATE orders SET order_status=? WHERE id=?",(status,order_id)); db.commit(); db.close()
    return jsonify({"message":"Order status updated.","status":status})

if __name__=="__main__":
    with app.app_context(): init_db()
    app.run(debug=app.config["DEBUG"])
