CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    farm_location TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Growing', -- Growing, Matured, Flowering, Harvested
    stage TEXT NOT NULL,
    area_acres REAL NOT NULL,
    expected_yield TEXT NOT NULL,
    sowing_date TEXT NOT NULL,
    fertilizers TEXT NOT NULL,
    image_url TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS soil_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    soil_type TEXT NOT NULL,
    ph_value REAL NOT NULL,
    moisture_pct REAL NOT NULL,
    nitrogen_val REAL NOT NULL,
    nitrogen_pct REAL NOT NULL,
    phosphorus_val REAL NOT NULL,
    phosphorus_pct REAL NOT NULL,
    potassium_val REAL NOT NULL,
    potassium_pct REAL NOT NULL,
    health_status TEXT NOT NULL,
    test_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS weather_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day_name TEXT NOT NULL,
    date_str TEXT NOT NULL,
    max_temp INTEGER NOT NULL,
    min_temp INTEGER NOT NULL,
    rain_chance INTEGER NOT NULL,
    condition TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date_str TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    trans_type TEXT NOT NULL, -- Income or Expense
    amount REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    activity_type TEXT NOT NULL, -- Crop Update, Soil Testing, Weather Update, Expense Added, Income Added
    date_str TEXT NOT NULL
);
