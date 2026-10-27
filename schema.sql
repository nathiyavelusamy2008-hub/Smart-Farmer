PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('farmer','buyer')),
 location TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS crops (
 id INTEGER PRIMARY KEY AUTOINCREMENT, farmer_id INTEGER NOT NULL REFERENCES users(id),
 name TEXT NOT NULL, quantity REAL NOT NULL CHECK(quantity>0),
 available_quantity REAL NOT NULL CHECK(available_quantity>=0), expected_price REAL NOT NULL CHECK(expected_price>0),
 harvest_date TEXT NOT NULL, quality_grade TEXT NOT NULL, location TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','sold','inactive')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_crops_name ON crops(name);
CREATE INDEX IF NOT EXISTS idx_crops_location ON crops(location);
CREATE TABLE IF NOT EXISTS market_prices (
 id INTEGER PRIMARY KEY AUTOINCREMENT, crop_name TEXT NOT NULL, market_name TEXT NOT NULL,
 price REAL NOT NULL CHECK(price>0), unit TEXT NOT NULL DEFAULT 'kg', distance_km REAL NOT NULL DEFAULT 0,
 reported_at TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'Demonstration data'
);
CREATE TABLE IF NOT EXISTS offers (
 id INTEGER PRIMARY KEY AUTOINCREMENT, crop_id INTEGER NOT NULL REFERENCES crops(id),
 buyer_id INTEGER NOT NULL REFERENCES users(id), offered_price REAL NOT NULL CHECK(offered_price>0),
 quantity REAL NOT NULL CHECK(quantity>0), status TEXT NOT NULL DEFAULT 'pending'
 CHECK(status IN ('pending','accepted','rejected')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS orders (
 id INTEGER PRIMARY KEY AUTOINCREMENT, offer_id INTEGER NOT NULL UNIQUE REFERENCES offers(id),
 farmer_id INTEGER NOT NULL REFERENCES users(id), buyer_id INTEGER NOT NULL REFERENCES users(id),
 crop_id INTEGER NOT NULL REFERENCES crops(id), agreed_price REAL NOT NULL, quantity REAL NOT NULL,
 order_status TEXT NOT NULL DEFAULT 'confirmed'
 CHECK(order_status IN ('confirmed','processing','completed','cancelled')), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
