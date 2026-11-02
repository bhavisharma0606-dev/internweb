
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, jsonify, flash
)
from functools import wraps
import pandas as pd
import pickle
import os
from werkzeug.security import check_password_hash
from database import get_connection, create_tables

app = Flask(__name__)
app.secret_key = "smart_rto_predictor_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------- LOAD MODELS ----------------

with open(os.path.join(BASE_DIR, "rto_model.pkl"), "rb") as f:
    rto_model = pickle.load(f)

with open(os.path.join(BASE_DIR, "cod_model.pkl"), "rb") as f:
    cod_model = pickle.load(f)


# ---------------- LOGIN REQUIRED ----------------

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("home.html")

# ---------------- LOGIN ----------------


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()

            if user and check_password_hash(user[2], password):
                session["user_id"] = user[0]
                session["username"] = user[1]
                return redirect(url_for("dashboard"))

            flash("Invalid username or password.", "danger")
        finally:
            conn.close()

    return render_template("login.html")



# ---------------- LOGOUT ----------------

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- EXISTING DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ---------------- SAVE PREDICTION DIRECTLY ----------------

def insert_prediction_record(result, prediction_type):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (
                prediction_type,
                cod_amount,
                product_value,
                charged_weight,
                shipping_charge,
                zone,
                prediction
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_type,
            result["cod_amount"],
            result["product_value"],
            result["charged_weight"],
            result["shipping_charge"],
            result["zone"],
            result["prediction"]
        ))
        conn.commit()
    finally:
        conn.close()


# ---------------- MAKE PREDICTION ----------------


def make_prediction(model, form_data):
    raw_weight = float(form_data.get("charged_weight", 0))
    unit = form_data.get("weight_unit", "g").strip().lower()

    # Convert kg to grams if user selected kg
    if unit == "kg":
        weight_in_grams = raw_weight * 1000.0
    else:
        weight_in_grams = raw_weight

    values = {
        "cod_amount": float(form_data.get("cod_amount", 0)),
        "charged_weight": weight_in_grams,
        "shipping_charge": float(form_data.get("shipping_charge", 0)),
        "zone": form_data.get("zone", "A"),
        "product_value": float(form_data.get("product_value", 0))
    }

    input_data = pd.DataFrame([values])
    prediction = model.predict(input_data)[0]

    confidence = None
    chart_labels = []
    chart_values = []

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(input_data)[0]
        confidence = round(float(max(probabilities)) * 100, 2)

        if hasattr(model, "classes_"):
            chart_labels = [str(label) for label in model.classes_]
        else:
            chart_labels = [str(prediction)]

        chart_values = [
            round(float(probability) * 100, 2)
            for probability in probabilities
        ]

    values["prediction"] = str(prediction)
    values["confidence"] = confidence
    values["chart_labels"] = chart_labels
    values["chart_values"] = chart_values

    return values


# ---------------- VALIDATION ----------------

def validate_prediction_input(form_data):
    try:
        cod_amount = float(form_data.get("cod_amount", 0))
        product_value = float(form_data.get("product_value", 0))
        raw_weight = float(form_data.get("charged_weight", 0))
        shipping_charge = float(form_data.get("shipping_charge", 0))
        unit = form_data.get("weight_unit", "g").strip().lower()
    except (ValueError, TypeError):
        return False, "Please enter valid numerical values for all fields."

    if not (1 <= product_value <= 500000):
        return False, "Product Value must be between ₹1 and ₹500,000."

    if cod_amount <= 0:
        return False, "COD Amount must be greater than ₹0."

    if cod_amount > product_value:
        return False, f"COD Amount (₹{cod_amount:,.2f}) cannot exceed Product Value (₹{product_value:,.2f})."

    weight_kg = raw_weight / 1000.0 if unit == "g" else raw_weight
    if not (0.1 <= weight_kg <= 50.0):
        return False, "Charged Weight must be between 0.1 kg (100g) and 50 kg (50,000g)."

    if not (0 <= shipping_charge <= 5000):
        return False, "Shipping Charge must be between ₹0 and ₹5,000."

    return True, None

# ---------------- RTO PREDICTION ----------------


@app.route("/rto_prediction", methods=["GET", "POST"])
@login_required
def rto_prediction():
    prediction = None
    confidence = None
    chart_labels = []
    chart_values = []

    if request.method == "POST":
        is_valid, error_msg = validate_prediction_input(request.form)
        if not is_valid:
            flash(error_msg, "danger")
        else:
            try:
                result = make_prediction(rto_model, request.form)

                insert_prediction_record(result, "RTO")

                prediction = result["prediction"]
                confidence = result["confidence"]
                chart_labels = result["chart_labels"]
                chart_values = result["chart_values"]

            except Exception as error:
                flash(f"RTO prediction error: {error}", "danger")

    return render_template(
        "rto_prediction.html",
        prediction=prediction,
        confidence=confidence,
        chart_labels=chart_labels,
        chart_values=chart_values
    )

# ---------------- COD PREDICTION ----------------


@app.route("/cod_prediction", methods=["GET", "POST"])
@login_required
def cod_prediction():
    prediction = None
    confidence = None
    chart_labels = []
    chart_values = []

    if request.method == "POST":
        is_valid, error_msg = validate_prediction_input(request.form)
        if not is_valid:
            flash(error_msg, "danger")
        else:
            try:
                result = make_prediction(cod_model, request.form)

                insert_prediction_record(result, "COD")

                prediction = result["prediction"]
                confidence = result["confidence"]
                chart_labels = result["chart_labels"]
                chart_values = result["chart_values"]

            except Exception as error:
                flash(f"COD prediction error: {error}", "danger")

    return render_template(
        "cod_prediction.html",
        prediction=prediction,
        confidence=confidence,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


# ---------------- REAL-TIME DASHBOARD ----------------

@app.route("/realtime-dashboard")
@login_required
def realtime_dashboard():
    return render_template("realtime_dashboard.html")


# ---------------- DASHBOARD API ----------------

@app.route("/api/dashboard-data")
@login_required
def dashboard_data():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM predictions")
        total = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT 
                COALESCE(SUM(cod_amount), 0),
                COALESCE(SUM(product_value), 0),
                COALESCE(AVG(cod_amount), 0),
                COALESCE(AVG(product_value), 0),
                COALESCE(AVG(shipping_charge), 0)
            FROM predictions
        """)
        sum_row = cursor.fetchone()
        total_cod_amount = round(float(sum_row[0]), 2)
        total_product_value = round(float(sum_row[1]), 2)
        avg_cod_amount = round(float(sum_row[2]), 2)
        avg_product_value = round(float(sum_row[3]), 2)
        avg_shipping_charge = round(float(sum_row[4]), 2)

        cursor.execute("""
            SELECT 
                CASE 
                    WHEN prediction_type LIKE 'COD%' THEN 'COD'
                    ELSE prediction_type 
                END as norm_type,
                COUNT(*)
            FROM predictions
            GROUP BY norm_type
        """)
        type_rows = cursor.fetchall()
        type_data = {str(row[0]): row[1] for row in type_rows}
        type_labels = [str(row[0]) for row in type_rows]
        type_counts = [row[1] for row in type_rows]

        cursor.execute("""
            SELECT zone, COUNT(*)
            FROM predictions
            WHERE zone IS NOT NULL AND zone != ''
            GROUP BY zone
            ORDER BY zone ASC
        """)
        zone_rows = cursor.fetchall()
        zone_data = {str(row[0]): row[1] for row in zone_rows}
        zone_labels = [str(row[0]) for row in zone_rows]
        zone_counts = [row[1] for row in zone_rows]

        cursor.execute("""
            SELECT prediction, COUNT(*)
            FROM predictions
            WHERE prediction IS NOT NULL AND prediction != ''
            GROUP BY prediction
            ORDER BY COUNT(*) DESC
        """)
        result_rows = cursor.fetchall()
        result_data = {str(row[0]): row[1] for row in result_rows}
        result_labels = [str(row[0]) for row in result_rows]
        result_counts = [row[1] for row in result_rows]

        cursor.execute("""
            SELECT prediction_type, cod_amount, product_value,
                   charged_weight, shipping_charge, zone, prediction, created_at
            FROM predictions
            ORDER BY id DESC
            LIMIT 10
        """)

        recent = []
        for row in cursor.fetchall():
            recent.append({
                "prediction_type": row[0],
                "cod_amount": row[1] or 0,
                "product_value": row[2] or 0,
                "charged_weight": row[3] or 0,
                "shipping_charge": row[4] or 0,
                "zone": row[5] or "N/A",
                "prediction": row[6] or "N/A",
                "created_at": str(row[7]) if row[7] else ""
            })

        rto_count = type_data.get("RTO", 0)
        cod_count = type_data.get("COD", 0)
        rto_percentage = round((rto_count / total * 100), 1) if total > 0 else 0
        cod_percentage = round((cod_count / total * 100), 1) if total > 0 else 0

        return jsonify({
            "total_predictions": total,
            "rto_predictions": rto_count,
            "cod_predictions": cod_count,
            "rto_percentage": rto_percentage,
            "cod_percentage": cod_percentage,
            "total_cod_amount": total_cod_amount,
            "total_product_value": total_product_value,
            "avg_cod_amount": avg_cod_amount,
            "avg_product_value": avg_product_value,
            "avg_shipping_charge": avg_shipping_charge,
            "zones": zone_data,
            "zone_labels": zone_labels,
            "zone_counts": zone_counts,
            "results": result_data,
            "result_labels": result_labels,
            "result_counts": result_counts,
            "types": type_data,
            "type_labels": type_labels,
            "type_counts": type_counts,
            "recent_predictions": recent
        })

    finally:
        conn.close()


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
