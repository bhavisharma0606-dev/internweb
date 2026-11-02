# Smart COD Risk & RTO Prediction System

A production-grade Machine Learning web application built with Flask and a modern White Glassmorphism UI that enables e-commerce merchants and logistics operators to predict Return To Origin (RTO) probabilities and assess Cash on Delivery (COD) risk before dispatching shipments.

---

## Key Features

- **RTO Prediction**: Accurately determines the probability of return for individual shipments with confidence metrics and outcome breakdown charts.
- **COD Risk Analysis**: Evaluates high-risk vs. low-risk Cash on Delivery transactions to prevent shipping cost leakage and stranded inventory.
- **Business Insights Dashboard**: Centralized summary analytics presenting operational metrics, aggregate delivery statuses, and risk profiles.
- **Real-Time Tracking & Analytics**: Interactive Chart.js data visualizations streaming zone-level trends, carrier performances, financial aggregations, and live prediction logs.
- **Outlier & Unit Validation**: Dynamic client-side and server-side validation preventing extreme input anomalies, supporting dynamic conversion between Grams (g) and Kilograms (kg).
- **Responsive White Glassmorphism UI**: High-contrast, clean SaaS layout with zero horizontal overflow and seamless mobile navigation.

---

## Tech Stack

- **Backend**: Python, Flask 3.1.3, SQLite
- **Machine Learning**: Scikit-Learn 1.6.1, NumPy 2.5.4, Pandas 3.1.0, Joblib 1.6.0
- **Frontend**: HTML5, Vanilla JavaScript (ES6+), Bootstrap 5, Bootstrap Icons, Chart.js
- **Styling**: Custom CSS3 Glassmorphism (`backdrop-filter: blur(10px)`, CSS Grid, Flexbox)

---

## Project Structure

```text
smart-rto-predictor/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── database.py
├── create_user.py
├── database.db
├── rto_model.pkl
├── cod_model.pkl
├── static/
│   └── css/
│       └── styles.css
└── templates/
    ├── base.html
    ├── home.html
    ├── login.html
    ├── dashboard.html
    ├── rto_prediction.html
    ├── cod_prediction.html
    └── realtime_dashboard.html
```

---

## Local Setup & Installation

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Git installed on your system

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/smart-rto-predictor.git
cd smart-rto-predictor
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:
```bash
cp .env.example .env   # Or create .env manually
```
Update values for `SECRET_KEY`, `DATABASE_URL`, and model paths as needed.

### 5. Initialize Database & Seed Users
```bash
python database.py
python create_user.py
```

### 6. Run the Application
```bash
python app.py
```

The web application will be accessible at:
```
http://127.0.0.1:5000
```
