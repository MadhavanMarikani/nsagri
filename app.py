from flask import Flask, render_template, request, redirect, url_for, session
from database import init_db, get_db
import sqlite3

app = Flask(__name__)
app.secret_key = 'smart_agri_secret_key_123'

# Initialize SQLite Database on launch
init_db()

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
    
    conn.close()
    return render_template('dashboard.html', 
                           crops=crops, 
                           activities=activities,
                           total_crops=len(crops),
                           total_income=total_income,
                           total_expenses=total_expenses)

@app.route('/crops')
def crops():
    conn = get_db()
    crops_list = conn.execute('SELECT * FROM crops').fetchall()
    conn.close()
    return render_template('crops.html', crops=crops_list)

@app.route('/crops/add', methods=['POST'])
def add_crop():
    name = request.form['name']
    status = request.form['status']
    stage = request.form['stage']
    area_acres = float(request.form['area_acres'])
    expected_yield = request.form['expected_yield']
    fertilizers = request.form['fertilizers']
    image_url = request.form.get('image_url') or 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=500&auto=format&fit=crop'
    
    conn = get_db()
    conn.execute('''
        INSERT INTO crops (user_id, name, status, stage, area_acres, expected_yield, sowing_date, fertilizers, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (1, name, status, stage, area_acres, expected_yield, 'Today', fertilizers, image_url))
    conn.commit()
    conn.close()
    return redirect(url_for('crops'))

@app.route('/soil')
def soil():
    conn = get_db()
    soil_rec = conn.execute('SELECT * FROM soil_records LIMIT 1').fetchone()
    conn.close()
    return render_template('soil.html', soil=soil_rec)

@app.route('/weather')
def weather():
    conn = get_db()
    forecast = conn.execute('SELECT * FROM weather_forecasts').fetchall()
    conn.close()
    return render_template('weather.html', forecast=forecast)

@app.route('/finance')
def finance():
    conn = get_db()
    trans = conn.execute('SELECT * FROM transactions ORDER BY id DESC').fetchall()
    total_income = conn.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Income'").fetchone()[0] or 0
    total_expenses = conn.execute("SELECT SUM(amount) FROM transactions WHERE trans_type = 'Expense'").fetchone()[0] or 0
    conn.close()
    return render_template('finance.html', transactions=trans, total_income=total_income, total_expenses=total_expenses)

@app.route('/finance/add', methods=['POST'])
def add_transaction():
    description = request.form['description']
    trans_type = request.form['trans_type']
    category = request.form['category']
    amount = float(request.form['amount'])
    
    conn = get_db()
    conn.execute('''
        INSERT INTO transactions (user_id, date_str, description, category, trans_type, amount)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (1, 'Today', description, category, trans_type, amount))
    conn.commit()
    conn.close()
    return redirect(url_for('finance'))

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
