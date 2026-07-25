from flask import Flask, render_template, request, redirect, url_for, session
from database import init_db, get_db
import sqlite3
from datetime import datetime, timedelta
import random
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'smart_agri_secret_key_123'

# Initialize SQLite Database on launch
init_db()

# Run a startup migration to ensure weather forecast dates and record years are in sync with today's date
def sync_weather_dates():
    conn = get_db()
    try:
        forecasts = conn.execute('SELECT * FROM weather_forecasts ORDER BY id ASC').fetchall()
        now = datetime.now()
        for i, f in enumerate(forecasts):
            target_date = now + timedelta(days=i)
            day_name = 'Today' if i == 0 else target_date.strftime('%a')
            date_str = target_date.strftime('%d %b')
            conn.execute('''
                UPDATE weather_forecasts
                SET day_name = ?, date_str = ?
                WHERE id = ?
            ''', (day_name, date_str, f['id']))
            
        # Update seeded transaction, activity, and soil dates to the current calendar year dynamically
        current_year = str(now.year)
        conn.execute("UPDATE transactions SET date_str = REPLACE(date_str, '2024', ?) WHERE date_str LIKE '%2024'", (current_year,))
        conn.execute("UPDATE activities SET date_str = REPLACE(date_str, '2024', ?) WHERE date_str LIKE '%2024'", (current_year,))
        conn.execute("UPDATE soil_records SET test_date = REPLACE(test_date, '2024', ?) WHERE test_date LIKE '%2024'", (current_year,))
        
        conn.commit()
    except Exception as e:
        print(f"Error syncing weather and record dates: {e}")
    finally:
        conn.close()

sync_weather_dates()

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password.')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        farm_location = request.form['farm_location']
        
        conn = get_db()
        try:
            conn.execute('''
                INSERT INTO users (full_name, email, phone, password_hash, farm_location)
                VALUES (?, ?, ?, ?, ?)
            ''', (full_name, email, phone, password, farm_location))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Email already exists!')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    conn = get_db()
    crops = conn.execute('SELECT * FROM crops').fetchall()
    activities = conn.execute('SELECT * FROM activities ORDER BY id DESC LIMIT 5').fetchall()
    
    # Calculate financial stats
    total_income = conn.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Income'").fetchone()[0] or 0
    total_expenses = conn.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Expense'").fetchone()[0] or 0
    
    # Get current date and day formatted (e.g., '25 Jul 2026, Saturday')
    today_str = datetime.now().strftime('%d %b %Y, %A')
    
    conn.close()
    return render_template('dashboard.html', 
                           crops=crops, 
                           activities=activities,
                           total_crops=len(crops),
                           total_income=total_income,
                           total_expenses=total_expenses,
                           today_str=today_str)

@app.route('/crops')
def crops():
    conn = get_db()
    crops_list = conn.execute('SELECT * FROM crops').fetchall()
    
    # Calculate crop stats dynamically
    total_area = conn.execute('SELECT SUM(area_acres) FROM crops').fetchone()[0] or 0
    active_crops = conn.execute("SELECT COUNT(*) FROM crops WHERE status IN ('Growing', 'Flowering')").fetchone()[0]
    
    total_yield = 0
    for crop in crops_list:
        try:
            val = float(crop['expected_yield'].split()[0])
            total_yield += val
        except (ValueError, IndexError):
            pass
            
    conn.close()
    return render_template('crops.html', 
                           crops=crops_list, 
                           total_area=round(total_area, 1),
                           active_crops=active_crops,
                           total_yield=int(total_yield))

@app.route('/crops/add', methods=['POST'])
def add_crop():
    name = request.form['name']
    status = request.form['status']
    stage = request.form['stage']
    area_acres = float(request.form['area_acres'])
    expected_yield = request.form['expected_yield']
    fertilizers = request.form['fertilizers']
    image_url = request.form.get('image_url') or 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=500&auto=format&fit=crop'
    sowing_date = datetime.now().strftime('%d %b %Y')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO crops (user_id, name, status, stage, area_acres, expected_yield, sowing_date, fertilizers, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (1, name, status, stage, area_acres, expected_yield, sowing_date, fertilizers, image_url))
    conn.commit()
    conn.close()
    return redirect(url_for('crops'))

@app.route('/crops/delete/<int:crop_id>', methods=['POST'])
def delete_crop(crop_id):
    conn = get_db()
    conn.execute('DELETE FROM crops WHERE id = ?', (crop_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('crops'))

@app.route('/soil')
def soil():
    conn = get_db()
    # Get all available field names from soil_records
    fields_raw = conn.execute('SELECT DISTINCT field_name FROM soil_records').fetchall()
    fields = [f['field_name'] for f in fields_raw]
    
    # Selected field parameter
    selected_field = request.args.get('field') or (fields[0] if fields else None)
    
    soil_rec = None
    history = []
    recommendation = "No soil records available."
    
    if selected_field:
        # Fetch the latest soil record for the selected field
        soil_rec = conn.execute('SELECT * FROM soil_records WHERE field_name = ? ORDER BY id DESC LIMIT 1', (selected_field,)).fetchone()
        
        # Fetch historical records for the selected field for the line chart
        history_raw = conn.execute('SELECT * FROM soil_records WHERE field_name = ? ORDER BY id ASC', (selected_field,)).fetchall()
        history = [dict(h) for h in history_raw]
        
        # Generate dynamic recommendation based on NPK and pH values
        if soil_rec:
            ph = soil_rec['ph_value']
            n_pct = soil_rec['nitrogen_pct']
            p_pct = soil_rec['phosphorus_pct']
            k_pct = soil_rec['potassium_pct']
            
            recs = []
            if ph < 6.0:
                recs.append("Soil is acidic. Add agricultural lime to raise pH level.")
            elif ph > 7.5:
                recs.append("Soil is alkaline. Add sulfur or organic compost to lower pH.")
                
            if n_pct < 50:
                recs.append("Nitrogen levels are low. Apply nitrogen-rich fertilizer like Urea.")
            if p_pct < 50:
                recs.append("Phosphorus levels are low. Apply DAP or Single Superphosphate.")
            if k_pct < 50:
                recs.append("Potassium levels are low. Apply Muriate of Potash.")
                
            if recs:
                recommendation = " ".join(recs)
            else:
                recommendation = "All primary nutrients (NPK) and pH levels are optimal. Soil health is in excellent condition!"
                
    conn.close()
    return render_template('soil.html', 
                           soil=soil_rec, 
                           fields=fields, 
                           selected_field=selected_field, 
                           history=history,
                           recommendation=recommendation)

@app.route('/soil/test/<path:field_name>')
def test_soil(field_name):
    conn = get_db()
    last_rec = conn.execute('SELECT * FROM soil_records WHERE field_name = ? ORDER BY id DESC LIMIT 1', (field_name,)).fetchone()
    
    if not last_rec:
        conn.close()
        return "Field not found", 400
        
    user_id = last_rec['user_id']
    soil_type = last_rec['soil_type']
    
    # Generate randomized realistic values
    ph_value = round(random.uniform(5.5, 7.8), 1)
    moisture_pct = round(random.uniform(20.0, 65.0), 1)
    
    nitrogen_val = round(random.uniform(15.0, 45.0), 1)
    phosphorus_val = round(random.uniform(8.0, 35.0), 1)
    potassium_val = round(random.uniform(150.0, 390.0), 1)
    
    nitrogen_pct = min(100.0, round((nitrogen_val / 45.0) * 100.0, 1))
    phosphorus_pct = min(100.0, round((phosphorus_val / 35.0) * 100.0, 1))
    potassium_pct = min(100.0, round((potassium_val / 380.0) * 100.0, 1))
    
    avg_pct = (nitrogen_pct + phosphorus_pct + potassium_pct) / 3.0
    if avg_pct >= 70:
        health_status = 'Good'
    elif avg_pct >= 45:
        health_status = 'Fair'
    else:
        health_status = 'Poor'
        
    test_date = datetime.now().strftime('%d %b %Y')
    
    conn.execute('''
        INSERT INTO soil_records (user_id, field_name, soil_type, ph_value, moisture_pct, nitrogen_val, nitrogen_pct, phosphorus_val, phosphorus_pct, potassium_val, potassium_pct, health_status, test_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, field_name, soil_type, ph_value, moisture_pct, nitrogen_val, nitrogen_pct, phosphorus_val, phosphorus_pct, potassium_val, potassium_pct, health_status, test_date))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('soil', field=field_name))

@app.route('/weather')
def weather():
    conn = get_db()
    forecast_raw = conn.execute('SELECT * FROM weather_forecasts ORDER BY id ASC').fetchall()
    
    # Calculate dynamic dates and day names starting from today and physically update SQLite
    now = datetime.now()
    forecast = []
    
    for i, row in enumerate(forecast_raw):
        target_date = now + timedelta(days=i)
        day_name = 'Today' if i == 0 else target_date.strftime('%a')
        date_str = target_date.strftime('%d %b')
        
        conn.execute('''
            UPDATE weather_forecasts
            SET day_name = ?, date_str = ?
            WHERE id = ?
        ''', (day_name, date_str, row['id']))
        
        forecast.append({
            'id': row['id'],
            'day_name': day_name,
            'date_str': date_str,
            'max_temp': row['max_temp'],
            'min_temp': row['min_temp'],
            'rain_chance': row['rain_chance'],
            'condition': row['condition']
        })
    conn.commit()
    conn.close()
        
    # Calculate today's weather dynamically from the first item
    today_weather = forecast[0] if forecast else None
    
    def estimate_humidity(cond):
        if 'Heavy Rain' in cond:
            return 92
        elif 'Rain' in cond:
            return 82
        elif 'Cloudy' in cond:
            return 65
        else:
            return 40
            
    def estimate_wind(cond):
        if 'Heavy Rain' in cond:
            return 18
        elif 'Rain' in cond:
            return 14
        elif 'Cloudy' in cond:
            return 10
        else:
            return 6
            
    today_data = {
        'temp': today_weather['max_temp'] if today_weather else 28,
        'max_temp': today_weather['max_temp'] if today_weather else 32,
        'min_temp': today_weather['min_temp'] if today_weather else 22,
        'condition': today_weather['condition'] if today_weather else 'Partly Cloudy',
        'rain_chance': today_weather['rain_chance'] if today_weather else 10,
        'humidity': estimate_humidity(today_weather['condition'] if today_weather else 'Partly Cloudy'),
        'wind_speed': estimate_wind(today_weather['condition'] if today_weather else 'Partly Cloudy'),
        'sunrise': "05:50 AM",
        'sunset': "06:42 PM"
    }
    
    return render_template('weather.html', forecast=forecast, today=today_data)

@app.route('/weather/refresh')
def refresh_weather():
    conn = get_db()
    forecasts = conn.execute('SELECT * FROM weather_forecasts ORDER BY id ASC').fetchall()
    
    conditions_pool = ['Sunny', 'Partly Cloudy', 'Rainy', 'Heavy Rain']
    now = datetime.now()
    
    for i, f in enumerate(forecasts):
        cond = random.choice(conditions_pool)
        target_date = now + timedelta(days=i)
        day_name = 'Today' if i == 0 else target_date.strftime('%a')
        date_str = target_date.strftime('%d %b')
        
        if cond == 'Heavy Rain':
            rain_chance = random.randint(80, 100)
            max_temp = random.randint(25, 28)
            min_temp = random.randint(19, 21)
        elif cond == 'Rainy':
            rain_chance = random.randint(50, 79)
            max_temp = random.randint(27, 30)
            min_temp = random.randint(20, 22)
        elif cond == 'Partly Cloudy':
            rain_chance = random.randint(10, 40)
            max_temp = random.randint(29, 32)
            min_temp = random.randint(21, 23)
        else: # Sunny
            rain_chance = random.randint(0, 10)
            max_temp = random.randint(32, 36)
            min_temp = random.randint(22, 25)
            
        conn.execute('''
            UPDATE weather_forecasts
            SET max_temp = ?, min_temp = ?, rain_chance = ?, condition = ?, day_name = ?, date_str = ?
            WHERE id = ?
        ''', (max_temp, min_temp, rain_chance, cond, day_name, date_str, f['id']))
        
    conn.commit()
    conn.close()
    return redirect(url_for('weather'))

@app.route('/finance')
def finance():
    conn = get_db()
    trans = conn.execute('SELECT * FROM transactions ORDER BY id DESC').fetchall()
    total_income = conn.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Income'").fetchone()[0] or 0
    total_expenses = conn.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Expense'").fetchone()[0] or 0
    
    # Calculate dynamic income sources
    income_sources_raw = conn.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE trans_type = 'Income'
        GROUP BY category
        ORDER BY total DESC
    ''').fetchall()
    
    income_sources = []
    for item in income_sources_raw:
        pct = round((item['total'] / total_income) * 100.0, 1) if total_income > 0 else 0
        income_sources.append({
            'category': item['category'],
            'total': item['total'],
            'percentage': pct
        })
        
    # Calculate expense categories for Doughnut chart
    expense_categories_raw = conn.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE trans_type = 'Expense'
        GROUP BY category
        ORDER BY total DESC
    ''').fetchall()
    expense_categories = [dict(ec) for ec in expense_categories_raw]
    
    # Calculate monthly income & expense totals for 12-month bar chart
    months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_income = [0] * 12
    monthly_expense = [0] * 12
    
    for t in trans:
        date_parts = t['date_str'].split()
        month_name = None
        if len(date_parts) >= 2:
            month_name = date_parts[1][:3] # e.g. 'May'
        elif t['date_str'] == 'Today':
            month_name = datetime.now().strftime('%b') # e.g. 'Jul'
            
        if month_name in months_names:
            m_idx = months_names.index(month_name)
            if t['trans_type'] == 'Income':
                monthly_income[m_idx] += t['amount']
            else:
                monthly_expense[m_idx] += t['amount']
                
    conn.close()
    return render_template('finance.html', 
                           transactions=trans, 
                           total_income=total_income, 
                           total_expenses=total_expenses,
                           income_sources=income_sources,
                           expense_categories=expense_categories,
                           monthly_income=monthly_income,
                           monthly_expense=monthly_expense)

@app.route('/finance/add', methods=['POST'])
def add_transaction():
    description = request.form['description']
    trans_type = request.form['trans_type']
    category = request.form['category']
    amount = float(request.form['amount'])
    
    # Use real current formatted date, e.g. '25 Jul 2026'
    today_date = datetime.now().strftime('%d %b %Y')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO transactions (user_id, date_str, description, category, trans_type, amount)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (1, today_date, description, category, trans_type, amount))
    conn.commit()
    conn.close()
    return redirect(url_for('finance'))

@app.route('/reports')
def reports():
    conn = get_db()
    crops = conn.execute('SELECT * FROM crops').fetchall()
    
    total_crops = len(crops)
    total_area = sum(c['area_acres'] for c in crops)
    
    total_prod = 0
    for c in crops:
        yield_str = c['expected_yield']
        num_part = ''.join(char for char in yield_str if char.isdigit() or char == '.')
        if num_part:
            try:
                total_prod += float(num_part)
            except ValueError:
                pass
                
    total_revenue = conn.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Income'").fetchone()[0] or 0
    
    # Production Overview Chart
    crop_labels = [c['name'] for c in crops]
    crop_yields = []
    for c in crops:
        yield_str = c['expected_yield']
        num_part = ''.join(char for char in yield_str if char.isdigit() or char == '.')
        try:
            crop_yields.append(float(num_part) if num_part else 0)
        except ValueError:
            crop_yields.append(0)
    crop_yields_last = [round(y * 0.85, 1) for y in crop_yields]
    
    # Expense Overview Chart
    expense_categories_raw = conn.execute('''
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE trans_type = 'Expense'
        GROUP BY category
        ORDER BY total DESC
    ''').fetchall()
    expense_categories = [dict(ec) for ec in expense_categories_raw]
    
    # Dynamic dates
    now = datetime.now()
    current_month = now.strftime('%B %Y')
    today_str = now.strftime('%d %b %Y')
    period_str = f"01 {now.strftime('%b %Y')} - {today_str}"
    
    conn.close()
    return render_template('reports.html',
                           total_crops=total_crops,
                           total_area=total_area,
                           total_prod=total_prod,
                           total_revenue=total_revenue,
                           crop_labels=crop_labels,
                           crop_yields=crop_yields,
                           crop_yields_last=crop_yields_last,
                           expense_categories=expense_categories,
                           current_month=current_month,
                           today_str=today_str,
                           period_str=period_str)

@app.route('/reports/export')
@app.route('/reports/download/<report_name>')
def export_report(report_name='Smart_Agriculture_Full_Report'):
    conn = get_db()
    crops = conn.execute('SELECT * FROM crops').fetchall()
    transactions = conn.execute('SELECT * FROM transactions').fetchall()
    
    # Initialize FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    
    # Header Banner - Dark Green
    pdf.set_fill_color(27, 94, 32)
    pdf.rect(10, 10, 190, 24, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 14, "SMART AGRICULTURE MANAGEMENT SYSTEM", 0, 1, 'C')
    pdf.set_font("Helvetica", 'I', 10)
    pdf.cell(0, 4, f"Official Farm Report - Generated on {datetime.now().strftime('%d %b %Y %H:%M')}", 0, 1, 'C')
    pdf.ln(12)
    
    # Reset Text Color
    pdf.set_text_color(31, 41, 55)
    
    # Report Title
    pdf.set_font("Helvetica", 'B', 14)
    friendly_name = report_name.replace('_', ' ')
    pdf.cell(0, 10, f"Report Type: {friendly_name}", 0, 1)
    pdf.ln(4)
    
    # Render Report Data based on report_name
    if 'Crop_Report' in report_name or 'Full_Report' in report_name:
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Crops Inventory & Stages", 0, 1)
        pdf.ln(2)
        
        pdf.set_fill_color(32, 125, 38)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(35, 8, "Crop Name", border=1, fill=True)
        pdf.cell(30, 8, "Status", border=1, fill=True)
        pdf.cell(30, 8, "Stage", border=1, fill=True)
        pdf.cell(25, 8, "Area", border=1, fill=True)
        pdf.cell(35, 8, "Expected Yield", border=1, fill=True)
        pdf.cell(35, 8, "Sowing Date", border=1, fill=True, ln=1)
        
        pdf.set_text_color(31, 41, 55)
        pdf.set_font("Helvetica", size=9)
        for c in crops:
            pdf.cell(35, 8, str(c['name']), border=1)
            pdf.cell(30, 8, str(c['status']), border=1)
            pdf.cell(30, 8, str(c['stage']), border=1)
            pdf.cell(25, 8, f"{c['area_acres']} Acres", border=1)
            pdf.cell(35, 8, str(c['expected_yield']), border=1)
            pdf.cell(35, 8, str(c['sowing_date']), border=1, ln=1)
        pdf.ln(10)
        
    if 'Soil_Report' in report_name or 'Full_Report' in report_name:
        soil_recs = conn.execute('SELECT * FROM soil_records ORDER BY id DESC').fetchall()
        
        if pdf.get_y() > 180:
            pdf.add_page()
            
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Soil Analysis Ledger", 0, 1)
        pdf.ln(2)
        
        pdf.set_fill_color(32, 125, 38)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(35, 8, "Field Name", border=1, fill=True)
        pdf.cell(30, 8, "Soil Type", border=1, fill=True)
        pdf.cell(20, 8, "pH Level", border=1, fill=True)
        pdf.cell(25, 8, "Moisture (%)", border=1, fill=True)
        pdf.cell(20, 8, "N-P-K (%)", border=1, fill=True)
        pdf.cell(30, 8, "Health Status", border=1, fill=True)
        pdf.cell(30, 8, "Test Date", border=1, fill=True, ln=1)
        
        pdf.set_text_color(31, 41, 55)
        pdf.set_font("Helvetica", size=9)
        for s in soil_recs[:10]:
            pdf.cell(35, 8, str(s['field_name']), border=1)
            pdf.cell(30, 8, str(s['soil_type']), border=1)
            pdf.cell(20, 8, str(s['ph_value']), border=1)
            pdf.cell(25, 8, f"{s['moisture_pct']}%", border=1)
            pdf.cell(20, 8, f"{int(s['nitrogen_pct'])}-{int(s['phosphorus_pct'])}-{int(s['potassium_pct'])}", border=1)
            pdf.cell(30, 8, str(s['health_status']), border=1)
            pdf.cell(30, 8, str(s['test_date']), border=1, ln=1)
        pdf.ln(10)
        
    if 'Weather_Report' in report_name or 'Full_Report' in report_name:
        weather_recs = conn.execute('SELECT * FROM weather_forecasts ORDER BY id ASC').fetchall()
        
        if pdf.get_y() > 180:
            pdf.add_page()
            
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Weather Forecast Summary", 0, 1)
        pdf.ln(2)
        
        pdf.set_fill_color(32, 125, 38)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(30, 8, "Day", border=1, fill=True)
        pdf.cell(30, 8, "Date", border=1, fill=True)
        pdf.cell(30, 8, "Max Temp", border=1, fill=True)
        pdf.cell(30, 8, "Min Temp", border=1, fill=True)
        pdf.cell(35, 8, "Condition", border=1, fill=True)
        pdf.cell(35, 8, "Rain Chance (%)", border=1, fill=True, ln=1)
        
        pdf.set_text_color(31, 41, 55)
        pdf.set_font("Helvetica", size=9)
        for w in weather_recs:
            pdf.cell(30, 8, str(w['day_name']), border=1)
            pdf.cell(30, 8, str(w['date_str']), border=1)
            pdf.cell(30, 8, f"{w['max_temp']} C", border=1)
            pdf.cell(30, 8, f"{w['min_temp']} C", border=1)
            pdf.cell(35, 8, str(w['condition']), border=1)
            pdf.cell(35, 8, f"{w['rain_chance']}%", border=1, ln=1)
        pdf.ln(10)
        
    if 'Full_Report' in report_name or 'export' in request.path:
        if pdf.get_y() > 150:
            pdf.add_page()
            
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Financial Ledger (Recent Transactions)", 0, 1)
        pdf.ln(2)
        
        pdf.set_fill_color(32, 125, 38)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(30, 8, "Date", border=1, fill=True)
        pdf.cell(60, 8, "Description", border=1, fill=True)
        pdf.cell(30, 8, "Category", border=1, fill=True)
        pdf.cell(30, 8, "Type", border=1, fill=True)
        pdf.cell(40, 8, "Amount (Rs.)", border=1, fill=True, ln=1)
        
        pdf.set_text_color(31, 41, 55)
        pdf.set_font("Helvetica", size=9)
        for t in transactions[:20]:
            pdf.cell(30, 8, str(t['date_str']), border=1)
            pdf.cell(60, 8, str(t['description']), border=1)
            pdf.cell(30, 8, str(t['category']), border=1)
            pdf.cell(30, 8, str(t['trans_type']), border=1)
            pdf.cell(40, 8, f"Rs. {t['amount']:,.2f}", border=1, ln=1)
            
    conn.close()
    
    # Save to temporary path and read bytes
    import os
    temp_pdf_path = f"temp_{report_name}.pdf"
    pdf.output(temp_pdf_path)
    
    with open(temp_pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    os.remove(temp_pdf_path)
    
    from flask import Response
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-disposition": f"attachment; filename={report_name}.pdf"}
    )

@app.route('/reports/dl/<report_name>')
def download_report(report_name):
    return export_report(report_name)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/database')
def database_viewer():
    conn = get_db()
    tables_raw = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
    tables = []
    
    selected_table = request.args.get('table')
    valid_tables = [t['name'] for t in tables_raw]
    
    for t_name in valid_tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t_name}").fetchone()[0]
        tables.append({'name': t_name, 'count': count})
        
    columns = []
    rows = []
    pk_col = None
    
    if selected_table and selected_table in valid_tables:
        cols_raw = conn.execute(f"PRAGMA table_info({selected_table})").fetchall()
        columns = [{'name': c['name'], 'type': c['type'], 'pk': bool(c['pk'])} for c in cols_raw]
        pk_col = next((c['name'] for c in columns if c['pk']), None)
        rows = conn.execute(f"SELECT * FROM {selected_table}").fetchall()
        
    conn.close()
    return render_template('database.html', 
                           tables=tables, 
                           selected_table=selected_table, 
                           columns=columns, 
                           rows=rows,
                           pk_col=pk_col)

@app.route('/database/add/<table_name>', methods=['POST'])
def database_add(table_name):
    conn = get_db()
    valid_tables = [t['name'] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    if table_name not in valid_tables:
        conn.close()
        return "Invalid Table Name", 400
    
    cols_raw = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    columns = [c['name'] for c in cols_raw if not c['pk']]
    
    placeholders = ', '.join(['?'] * len(columns))
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    values = []
    for col in columns:
        val = request.form.get(col)
        values.append(None if val == '' else val)
        
    try:
        conn.execute(sql, values)
        conn.commit()
    except Exception as e:
        conn.close()
        return f"Database Error: {str(e)}", 500
        
    conn.close()
    return redirect(url_for('database_viewer', table=table_name))

@app.route('/database/edit/<table_name>/<row_id>', methods=['POST'])
def database_edit(table_name, row_id):
    conn = get_db()
    valid_tables = [t['name'] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    if table_name not in valid_tables:
        conn.close()
        return "Invalid Table Name", 400
        
    cols_raw = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    columns = [c['name'] for c in cols_raw if not c['pk']]
    pk_col = next((c['name'] for c in cols_raw if c['pk']), None)
    
    if not pk_col:
        conn.close()
        return "Table lacks a primary key to edit", 400
        
    set_clause = ', '.join([f"{col} = ?" for col in columns])
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {pk_col} = ?"
    
    values = []
    for col in columns:
        val = request.form.get(col)
        values.append(None if val == '' else val)
    values.append(row_id)
    
    try:
        conn.execute(sql, values)
        conn.commit()
    except Exception as e:
        conn.close()
        return f"Database Error: {str(e)}", 500
        
    conn.close()
    return redirect(url_for('database_viewer', table=table_name))

@app.route('/database/delete/<table_name>/<row_id>', methods=['POST'])
def database_delete(table_name, row_id):
    conn = get_db()
    valid_tables = [t['name'] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    if table_name not in valid_tables:
        conn.close()
        return "Invalid Table Name", 400
        
    cols_raw = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    pk_col = next((c['name'] for c in cols_raw if c['pk']), None)
    
    if not pk_col:
        conn.close()
        return "Table lacks a primary key to delete", 400
        
    sql = f"DELETE FROM {table_name} WHERE {pk_col} = ?"
    
    try:
        conn.execute(sql, (row_id,))
        conn.commit()
    except Exception as e:
        conn.close()
        return f"Database Error: {str(e)}", 500
        
    conn.close()
    return redirect(url_for('database_viewer', table=table_name))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
