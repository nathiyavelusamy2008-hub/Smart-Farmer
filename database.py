import sqlite3
from datetime import date
from flask import current_app

def get_db():
    conn = sqlite3.connect(current_app.config["DATABASE_PATH"], timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_db()
    with open("schema.sql", encoding="utf-8") as f:
        conn.executescript(f.read())
    count = conn.execute("SELECT COUNT(*) FROM market_prices").fetchone()[0]
    if count == 0:
        today = date.today().isoformat()
        demo = [
            ("Tomato","Karur Market",22,"kg",12,today,"Demonstration data"),
            ("Tomato","Trichy Market",25,"kg",38,today,"Demonstration data"),
            ("Onion","Karur Market",28,"kg",12,today,"Demonstration data"),
            ("Onion","Salem Market",31,"kg",65,today,"Demonstration data"),
            ("Rice","Trichy Market",42,"kg",38,today,"Demonstration data"),
            ("Banana","Karur Market",32,"kg",12,today,"Demonstration data"),
            ("Potato","Salem Market",24,"kg",65,today,"Demonstration data")]
        conn.executemany(
            "INSERT INTO market_prices(crop_name,market_name,price,unit,distance_km,reported_at,source) VALUES(?,?,?,?,?,?,?)",
            demo)
    conn.commit()
    conn.close()
