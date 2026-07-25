# Smart Agriculture Management System 🌾🚜

A full-featured web application built with **Python (Flask)**, **SQLite**, **HTML5/CSS3**, and **Chart.js**. Designed for farmers to manage crops, analyze soil health, track weather forecasts, log transactions, and export comprehensive farm reports.

---

## 🌟 Features

- **Dashboard**: High-level overview with KPI cards (Active Crops, Weather, Profit/Loss), interactive charts (Farm Overview, Crop Status, Monthly Expenses vs Income), and recent activity feed.
- **Crops Management**: View crop details, stage, area, expected yield, sowing date, and fertilizer usage. Add new crops dynamically with image URLs and delete existing crops.
- **Soil Analysis**: Monitor soil parameters including pH levels, moisture percentage, NPK (Nitrogen, Phosphorus, Potassium) nutrient gauges, and recommendations. Includes a sensor test simulator.
- **Weather Forecast**: 7-day weather predictions, temperature trends, rainfall statistics, and sunrise/sunset times with live forecast refresh simulator.
- **Finance Tracking**: Income & expense logging, net profit calculation, transaction history, expense breakdown by category, and top income sources.
- **Reports & Analytics**: Generate and export dynamic downloadable **PDF reports** (`Smart_Agriculture_Full_Report.pdf`, `Crop_Report.pdf`, `Soil_Report.pdf`, `Weather_Report.pdf`) styled with header banners and tables.
- **User Authentication**: Login, Registration, and Session management with secure SQLite database backing.
- **Developer Database Panel**: A hidden CRUD admin page (`/database`) to view, add, edit, and delete rows in any database table directly.

---

## 🚀 How to Run the Project

### Prerequisites

Ensure you have **Python 3.8+** installed on your system.

### Step 1: Clone the Repository

```bash
git clone https://github.com/MadhavanMarikani/nsagri.git
cd nsagri
```

### Step 2: Create & Activate Virtual Environment (Recommended)

**On Windows (PowerShell):**
```powershell
python -m venv env
.\env\Scripts\Activate
```

**On macOS / Linux:**
```bash
python3 -m venv env
source env/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

Upon launching, the app will automatically initialize the SQLite database (`agriculture.db`) with initial demo data.

### Step 5: Open in Browser

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🔑 Default Login Credentials

You can use the default demo account pre-filled on the login screen or register a new account:

- **Email**: `farmer@agri.com`
- **Password**: `farmer123`

---

## 📁 Project Structure

```text
nsagri/
├── app.py                   # Main Flask application & routes
├── database.py              # SQLite connection & database initialization/seeding
├── schema.sql               # Database table schemas
├── requirements.txt         # Python package dependencies
├── static/
│   ├── css/
│   │   └── style.css        # Complete UI design system & responsive styling
│   └── js/
│       └── main.js          # Modal popups & UI interaction handlers
└── templates/
    ├── base.html            # Sidebar navigation layout
    ├── splash.html          # Splash screen loader
    ├── login.html           # Login page
    ├── register.html        # Registration page
    ├── dashboard.html       # Farm Dashboard
    ├── crops.html           # Crops Management & Details
    ├── soil.html            # Soil Health & Analysis
    ├── weather.html         # Weather Forecast & Trends
    ├── finance.html         # Finance Details & Transactions
    ├── reports.html         # Detailed Reports page
    ├── database.html        # Developer Database Viewer/Editor (CRUD)
    └── about.html           # About Us page
```

---

## 💻 Tech Stack

- **Backend**: Python 3, Flask, FPDF2 (PDF generation)
- **Database**: SQLite3
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6+), FontAwesome Icons
- **Data Visualization**: Chart.js
