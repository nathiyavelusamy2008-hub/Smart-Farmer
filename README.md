# 🌱 Smart Farmer – Connect, Compare, Sell

A beginner-friendly Flask + SQLite college project for agricultural price comparison, direct farmer/buyer listings and offers, net-return calculation, and market recommendations.

**Data warning:** market prices included in the project are demonstration data only. They are not live, official, or guaranteed prices. The recommendation is a transparent calculation, not an AI prediction.

## Problem statement
Farmers can find it difficult to compare selling opportunities, reach buyers, and understand how transport costs affect returns.

## Features
- Farmer and buyer registration/login; passwords hashed with Werkzeug.
- Session-based login and role-checked actions.
- Crop listing creation, browsing, and filters.
- Demonstration market-price comparison with source/date.
- Buyer offers; farmers can accept or reject offers.
- Order records and order status display.
- Net return calculator and market ranking by estimated return.
- Responsive HTML/CSS/JavaScript frontend, Flask API, SQLite database.
- Basic automated tests.

## Technology
Python, Flask, SQLite, HTML5, CSS3, JavaScript Fetch API, Werkzeug, Flask-WTF, python-dotenv.

## Folder structure
```text
smart_farmer/
├── app.py
├── config.py
├── database.py
├── schema.sql
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── templates/ (index.html, login.html, register.html, dashboard.html)
├── static/css/style.css
├── static/js/app.js
├── static/images/
├── services/ (market_service.py, recommendation_service.py)
└── tests/test_app.py
```

## Requirements
Python 3.10+ recommended, VS Code, and internet for installing dependencies the first time. No Node.js, MySQL, Docker, paid API, or external AI service is required.

## Run on Windows in VS Code
1. Extract `smart_farmer_project.zip`.
2. In VS Code choose **File → Open Folder** and select `smart_farmer`.
3. Choose **Terminal → New Terminal**.
4. Optional virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If activation is blocked, use `.venv\Scripts\python.exe` in place of `py`, or activate from Command Prompt with `.venv\Scripts\activate.bat`.
5. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
6. Copy `.env.example` to `.env` and replace the placeholder `SECRET_KEY` with a long random value.
7. Start:
   ```powershell
   py app.py
   ```
8. Visit **http://127.0.0.1:5000**. Keep the terminal running; press Ctrl+C to stop.

**Important:** Live Server alone cannot run a Flask backend. Start the app with `py app.py`.

## Try the application
1. Register as a Farmer or Buyer with a 10–15 digit phone number and password of at least 8 characters.
2. Farmer: open Dashboard and publish a crop listing.
3. Buyer: return Home and click Make offer on a crop listing.
4. Farmer: Dashboard → accept/reject pending offers.
5. Check orders and try the calculator and recommendation features.

## API routes
- `GET /`, `GET /login`, `GET /register`, `GET /dashboard`
- `POST /api/register`, `POST /api/login`, `POST /api/logout`, `GET /api/me`
- `GET /api/dashboard`, `GET/POST /api/crops`, `GET /api/markets`
- `POST/GET /api/offers`, `PATCH /api/offers/<id>`
- `POST /api/calculator`, `GET /api/recommendations`
- `GET /api/orders`, `PATCH /api/orders/<id>`

## Market data
The app seeds demonstration records automatically. To add an official data source later, check the provider's current API availability, terms, units, and update schedule. No external market API is configured by default.

## Run tests
```powershell
py -m unittest discover -s tests -v
```

## Upload to GitHub
1. Create an empty repository on GitHub.
2. In the project folder terminal:
   ```powershell
   git init
   git add .
   git commit -m "Initial Smart Farmer project"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```
3. Replace the remote URL with your repository URL. Install Git for Windows if `git` is not recognized.
4. `.gitignore` excludes `.env`, databases, virtual environments, and caches. Never commit real credentials or personal user data.

## Deployment and security notes
- Use a production WSGI server and HTTPS; do not expose Flask's development server.
- Set a strong `SECRET_KEY`, keep debug disabled, and enable `COOKIE_SECURE=1` behind HTTPS.
- Flask-WTF CSRF protection is enabled. Extend the browser frontend with proper CSRF token retrieval and headers before public deployment.
- Review rate limiting, phone verification, password reset, database backups, logging, and access controls before handling real users.
- This is an educational prototype; it does not include payments, real-time market feeds, identity verification, transport booking, or external AI.
