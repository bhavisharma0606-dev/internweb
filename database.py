import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    # Prediction history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_type TEXT NOT NULL,
            cod_amount REAL,
            product_value REAL,
            charged_weight REAL,
            shipping_charge REAL,
            zone TEXT,
            prediction TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# Create a login account directly
def create_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (username, password)
            VALUES (?, ?)
        """, (username, hashed_password))

        conn.commit()
        print("Login account created successfully!")

    except sqlite3.IntegrityError:
        print("This username already exists.")

    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
    print(f"Tables created/checked in: {DB_PATH}")