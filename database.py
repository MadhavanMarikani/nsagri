import sqlite3
import os

DB_NAME = 'agriculture.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_NAME):
        conn = get_db()
        with open('schema.sql', 'r') as f:
            conn.executescript(f.read())
        
        # Seed initial data for demo matching design screenshots
        cursor = conn.cursor()
        
        # Default user (Password: farmer123)
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, password_hash, farm_location)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Farmer', 'farmer@agri.com', '9876543210', 'pbkdf2:sha256:260000$farmer123hash', 'Field 1 (North)'))
        
        user_id = cursor.lastrowid

        # Seed Crops
        crops_data = [
            (user_id, 'Rice', 'Growing', 'Tillering', 2.5, '25 Quintal/Acre', '10 Apr 2024', 'Urea, DAP, Potash', 'https://images.unsplash.com/photo-1536657464919-892534f60d6e?w=500&auto=format&fit=crop'),
            (user_id, 'Wheat', 'Matured', 'Matured', 3.0, '28 Quintal/Acre', '15 Nov 2023', 'Urea, DAP, Zinc Sulphate', 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=500&auto=format&fit=crop'),
            (user_id, 'Maize', 'Growing', 'Vegetative', 2.0, '30 Quintal/Acre', '05 Apr 2024', 'Urea, DAP, Potash', 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=500&auto=format&fit=crop'),
            (user_id, 'Cotton', 'Flowering', 'Flowering', 1.8, '18 Quintal/Acre', '20 Mar 2024', 'Urea, SSP, Potash', 'https://images.unsplash.com/photo-1605000797499-95a51c5269ae?w=500&auto=format&fit=crop'),
            (user_id, 'Sugarcane', 'Growing', 'Grand Growth', 1.5, '800 Quintal/Acre', '12 Jan 2024', 'Pressmud, Urea, Potash', 'https://images.unsplash.com/photo-1589923188900-85dae523342b?w=500&auto=format&fit=crop')
        ]
        cursor.executemany('''
            INSERT INTO crops (user_id, name, status, stage, area_acres, expected_yield, sowing_date, fertilizers, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', crops_data)

        # Seed Soil Record
        cursor.execute('''
            INSERT INTO soil_records (user_id, field_name, soil_type, ph_value, moisture_pct, nitrogen_val, nitrogen_pct, phosphorus_val, phosphorus_pct, potassium_val, potassium_pct, health_status, test_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Field 1 (North)', 'Loamy Soil', 6.8, 42.0, 36.2, 72.0, 18.5, 58.0, 320.0, 80.0, 'Good', '20 May 2024'))

        # Seed Weather Forecasts
        weather_data = [
            ('Today', '20 May', 32, 22, 10, 'Partly Cloudy'),
            ('Tue', '21 May', 33, 23, 0, 'Sunny'),
            ('Wed', '22 May', 31, 22, 20, 'Partly Cloudy'),
            ('Thu', '23 May', 28, 21, 60, 'Rainy'),
            ('Fri', '24 May', 27, 21, 70, 'Heavy Rain'),
            ('Sat', '25 May', 30, 22, 10, 'Partly Cloudy'),
            ('Sun', '26 May', 33, 23, 0, 'Sunny')
        ]
        cursor.executemany('''
            INSERT INTO weather_forecasts (day_name, date_str, max_temp, min_temp, rain_chance, condition)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', weather_data)

        # Seed Transactions
        trans_data = [
            (user_id, '20 May 2024', 'Sold Rice (50 Bags)', 'Income', 'Income', 25000),
            (user_id, '18 May 2024', 'Purchased Urea Fertilizer', 'Fertilizers', 'Expense', 8500),
            (user_id, '16 May 2024', 'Hired Labor (4 Days)', 'Labor', 'Expense', 6000),
            (user_id, '14 May 2024', 'Sold Maize (30 Bags)', 'Income', 'Income', 15000),
            (user_id, '12 May 2024', 'Purchased Pesticides', 'Pesticides', 'Expense', 4500)
        ]
        cursor.executemany('''
            INSERT INTO transactions (user_id, date_str, description, category, trans_type, amount)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', trans_data)

        # Seed Activities
        act_data = [
            (user_id, 'Crop Update', 'Rice crop status updated', 'Crop Update', '20 May 2024'),
            (user_id, 'Soil Testing', 'Soil test completed for Field 2', 'Soil Testing', '19 May 2024'),
            (user_id, 'Weather Update', 'Heavy rain expected tomorrow', 'Weather Update', '19 May 2024'),
            (user_id, 'Expense Added', 'Fertilizer purchase of ₹ 5,000', 'Expense Added', '18 May 2024'),
            (user_id, 'Income Added', 'Sold vegetables for ₹ 8,000', 'Income Added', '18 May 2024')
        ]
        cursor.executemany('''
            INSERT INTO activities (user_id, title, details, activity_type, date_str)
            VALUES (?, ?, ?, ?, ?)
        ''', act_data)

        conn.commit()
        conn.close()
        print("Database initialized & seeded successfully!")
