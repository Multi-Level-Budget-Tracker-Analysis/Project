import sqlite3
import os
import hashlib
import secrets
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_DB_PATH = os.path.join(BASE_DIR, "backend", "budget_tracker.db")
RAW_DATA_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "01_RawData")
CLEAN_DATA_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "02_CleanData")

def hash_password(password: str, salt: str = None) -> str:
    if not salt:
        salt = secrets.token_hex(8)
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash or ":" not in stored_hash:
        return False
    salt, hashed = stored_hash.split(":", 1)
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest() == hashed

def get_db_path():
    # If on Vercel or running in a read-only environment
    if os.environ.get("VERCEL") or not os.access(os.path.dirname(ORIGINAL_DB_PATH), os.W_OK):
        import shutil
        tmp_db = "/tmp/budget_tracker.db"
        if not os.path.exists(tmp_db) and os.path.exists(ORIGINAL_DB_PATH):
            try:
                shutil.copyfile(ORIGINAL_DB_PATH, tmp_db)
            except Exception:
                pass
        return tmp_db
    return ORIGINAL_DB_PATH

def get_db_connection():
    db_file = get_db_path()
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Individual Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS individual_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        mode TEXT NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT,
        note TEXT,
        amount REAL NOT NULL,
        income_expense TEXT NOT NULL,
        currency TEXT DEFAULT 'INR'
    )
    """)

    # 2. Category Budget Targets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS category_budgets (
        category TEXT PRIMARY KEY,
        monthly_budget REAL NOT NULL
    )
    """)

    # 3. Organization Superstore Orders / Costs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS org_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT NOT NULL,
        order_date TEXT NOT NULL,
        ship_date TEXT,
        ship_mode TEXT,
        department TEXT NOT NULL,
        city TEXT,
        state TEXT,
        region TEXT NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT NOT NULL,
        product_name TEXT,
        sales REAL NOT NULL,
        quantity INTEGER NOT NULL,
        discount REAL DEFAULT 0.0,
        profit REAL NOT NULL,
        cost REAL NOT NULL,
        budget_variance REAL NOT NULL
    )
    """)

    # 4. State Finance Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS state_finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state TEXT NOT NULL,
        year INTEGER NOT NULL,
        indicator TEXT NOT NULL,
        value REAL NOT NULL
    )
    """)

    # 5. National Union Budget Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS national_budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ministry TEXT NOT NULL,
        sector TEXT NOT NULL,
        year INTEGER NOT NULL,
        allocation REAL NOT NULL,
        expenditure REAL NOT NULL
    )
    """)

    # 6. Users Authentication Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Financial Analyst',
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()

    # Pre-seed default demo accounts if not present
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        demo_accounts = [
            ("admin", hash_password("admin123"), "Administrator", "Admin"),
            ("user", hash_password("user123"), "Verified User", "User"),
            ("guest", hash_password("guest123"), "Guest Reviewer", "Guest"),
            ("student", hash_password("student123"), "Verified User", "User"),
            ("demo", hash_password("demo123"), "Guest Reviewer", "Guest")
        ]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.executemany("""
            INSERT OR IGNORE INTO users (username, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, [(u, p, n, r, now_str) for u, p, n, r in demo_accounts])
        conn.commit()

    conn.close()

def clear_all_datasets():
    """Wipes all transactional and analytical data while preserving user accounts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM individual_transactions")
    cursor.execute("DELETE FROM category_budgets")
    cursor.execute("DELETE FROM org_orders")
    cursor.execute("DELETE FROM state_finance")
    cursor.execute("DELETE FROM national_budget")
    conn.commit()
    conn.close()
    print("All analytical datasets cleared from SQLite database.")

def load_csvs_into_db():
    """Loads records from CleanData CSVs into SQLite database if data rows exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    total_loaded = 0

    # 1. Individual Transactions
    ind_csv = os.path.join(CLEAN_DATA_DIR, "individual_clean.csv")
    if not os.path.exists(ind_csv) or os.path.getsize(ind_csv) < 120:
        ind_csv = os.path.join(RAW_DATA_DIR, "individual_transactions.csv")

    if os.path.exists(ind_csv) and os.path.getsize(ind_csv) > 120:
        try:
            df_ind = pd.read_csv(ind_csv)
            if not df_ind.empty:
                cursor.execute("DELETE FROM individual_transactions")
                for _, row in df_ind.iterrows():
                    cursor.execute("""
                    INSERT INTO individual_transactions (date, mode, category, subcategory, note, amount, income_expense, currency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get("date", row.get("Date", "")))[:10],
                        str(row.get("mode", row.get("Mode", "UPI"))),
                        str(row.get("category", row.get("Category", "General"))),
                        str(row.get("subcategory", row.get("Subcategory", ""))),
                        str(row.get("note", row.get("Note", ""))),
                        float(row.get("amount", row.get("Amount", 0.0))),
                        str(row.get("income_expense", row.get("Income/Expense", "Expense"))),
                        str(row.get("currency", row.get("Currency", "INR")))
                    ))
                total_loaded += len(df_ind)
                print(f"Loaded {len(df_ind)} records into individual_transactions.")
        except Exception as e:
            print("Notice loading individual transactions:", e)

    # 2. Organization Orders
    org_csv = os.path.join(CLEAN_DATA_DIR, "org_clean.csv")
    if not os.path.exists(org_csv) or os.path.getsize(org_csv) < 180:
        org_csv = os.path.join(RAW_DATA_DIR, "org_superstore.csv")

    if os.path.exists(org_csv) and os.path.getsize(org_csv) > 180:
        try:
            df_org = pd.read_csv(org_csv)
            if not df_org.empty:
                cursor.execute("DELETE FROM org_orders")
                for _, row in df_org.iterrows():
                    sales = float(row.get("sales", row.get("Sales", 0.0)))
                    profit = float(row.get("profit", row.get("Profit", 0.0)))
                    cost = float(row.get("cost", row.get("Cost", sales - profit)))
                    variance = float(row.get("budget_variance", row.get("BudgetVariance", 0.0)))

                    cursor.execute("""
                    INSERT INTO org_orders (order_id, order_date, ship_date, ship_mode, department, city, state, region, category, subcategory, product_name, sales, quantity, discount, profit, cost, budget_variance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get("order_id", row.get("Order ID", ""))),
                        str(row.get("order_date", row.get("Order Date", "")))[:10],
                        str(row.get("ship_date", row.get("Ship Date", "")))[:10],
                        str(row.get("ship_mode", row.get("Ship Mode", "Standard Class"))),
                        str(row.get("department", row.get("Department", row.get("Segment", "Corporate")))),
                        str(row.get("city", row.get("City", ""))),
                        str(row.get("state", row.get("State", ""))),
                        str(row.get("region", row.get("Region", "North"))),
                        str(row.get("category", row.get("Category", "General"))),
                        str(row.get("subcategory", row.get("Sub-Category", ""))),
                        str(row.get("product_name", row.get("Product Name", ""))),
                        sales,
                        int(row.get("quantity", row.get("Quantity", 1))),
                        float(row.get("discount", row.get("Discount", 0.0))),
                        profit,
                        cost,
                        variance
                    ))
                total_loaded += len(df_org)
                print(f"Loaded {len(df_org)} records into org_orders.")
        except Exception as e:
            print("Notice loading organization orders:", e)

    # 3. State Public Finances
    state_csv = os.path.join(CLEAN_DATA_DIR, "state_clean.csv")
    if not os.path.exists(state_csv) or os.path.getsize(state_csv) < 60:
        state_csv = os.path.join(RAW_DATA_DIR, "state_finance_india.csv")

    if os.path.exists(state_csv) and os.path.getsize(state_csv) > 60:
        try:
            df_state = pd.read_csv(state_csv)
            if not df_state.empty:
                cursor.execute("DELETE FROM state_finance")
                for _, row in df_state.iterrows():
                    cursor.execute("""
                    INSERT INTO state_finance (state, year, indicator, value)
                    VALUES (?, ?, ?, ?)
                    """, (
                        str(row.get("state", row.get("State", ""))),
                        int(row.get("year", row.get("Year", 2024))),
                        str(row.get("indicator", row.get("Indicator", ""))),
                        float(row.get("value", row.get("Value", 0.0)))
                    ))
                total_loaded += len(df_state)
                print(f"Loaded {len(df_state)} records into state_finance.")
        except Exception as e:
            print("Notice loading state finance:", e)

    # 4. National Budget
    nat_csv = os.path.join(CLEAN_DATA_DIR, "national_clean.csv")
    if not os.path.exists(nat_csv) or os.path.getsize(nat_csv) < 60:
        nat_csv = os.path.join(RAW_DATA_DIR, "national_union_budget.csv")

    if os.path.exists(nat_csv) and os.path.getsize(nat_csv) > 60:
        try:
            df_nat = pd.read_csv(nat_csv)
            if not df_nat.empty:
                cursor.execute("DELETE FROM national_budget")
                for _, row in df_nat.iterrows():
                    cursor.execute("""
                    INSERT INTO national_budget (ministry, sector, year, allocation, expenditure)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(row.get("ministry", row.get("Ministry", ""))),
                        str(row.get("sector", row.get("Sector", ""))),
                        int(row.get("year", row.get("Year", 2024))),
                        float(row.get("allocation", row.get("Allocation", 0.0))),
                        float(row.get("expenditure", row.get("Expenditure", 0.0)))
                    ))
                total_loaded += len(df_nat)
                print(f"Loaded {len(df_nat)} records into national_budget.")
        except Exception as e:
            print("Notice loading national budget:", e)

    conn.commit()
    conn.close()
    return total_loaded

def authenticate_user(username, password):
    if not username or not password:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),)).fetchone()
    conn.close()
    if user and verify_password(password, user["password_hash"]):
        return {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    return None

def create_user(username, password, full_name, role="Financial Analyst"):
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."

    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return False, f"Username '{username}' is already registered. Please choose another or login."

    hashed = hash_password(password)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO users (username, password_hash, full_name, role, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, hashed, full_name.strip() or username, role, now_str)
    )
    conn.commit()
    new_user = conn.execute("SELECT id, username, full_name, role FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return True, {
        "id": new_user["id"],
        "username": new_user["username"],
        "full_name": new_user["full_name"],
        "role": new_user["role"]
    }

def get_demo_user(role_key):
    role_map = {
        "admin": "admin",
        "user": "user",
        "guest": "guest",
        "student": "user",
        "demo": "guest"
    }
    uname = role_map.get(str(role_key).lower())
    if not uname:
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT id, username, full_name, role FROM users WHERE username = ?", (uname,)).fetchone()
    conn.close()
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    return None

if __name__ == "__main__":
    import sys
    if "--clear" in sys.argv:
        clear_all_datasets()
    elif "--reload" in sys.argv or "--sync" in sys.argv:
        init_db()
        load_csvs_into_db()
    else:
        init_db()
        print("Database initialized (datasets empty until CSVs or inputs are provided).")
