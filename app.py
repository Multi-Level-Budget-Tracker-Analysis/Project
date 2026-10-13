import os
import csv
import json
from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
import pandas as pd
from datetime import datetime

from backend.database import (
    get_db_connection,
    init_db,
    authenticate_user,
    create_user,
    get_demo_user
)
from backend.analytics_engine import (
    get_executive_overview,
    get_individual_analytics,
    get_organization_analytics,
    get_state_nation_analytics,
    get_predictive_analytics,
    calculate_custom_individual,
    calculate_custom_organization
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")
RAW_DATA_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "01_RawData")
CLEAN_DATA_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "02_CleanData")
PBI_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "03_PowerBI")

app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATES_DIR)
CORS(app)

# Ensure database exists
init_db()

# ==========================================
# 0. AUTHENTICATION & ACCESS CONTROL API
# ==========================================
@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    try:
        body = request.get_json(force=True) or {}
        username = body.get("username", "").strip()
        password = body.get("password", "")
        user = authenticate_user(username, password)
        if user:
            return jsonify({
                "success": True,
                "message": f"Welcome back, {user['full_name']}!",
                "user": user
            })
        return jsonify({"success": False, "error": "Invalid username or password. Check credentials or use 1-click Demo buttons."}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    try:
        body = request.get_json(force=True) or {}
        username = body.get("username", "").strip()
        password = body.get("password", "")
        full_name = body.get("full_name", "").strip() or username
        role = body.get("role", "Student / Analyst")
        
        ok, res = create_user(username, password, full_name, role)
        if ok:
            return jsonify({
                "success": True,
                "message": "Account created successfully! You can now log in.",
                "user": res
            })
        return jsonify({"success": False, "error": res}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/auth/demo", methods=["POST"])
def auth_demo():
    try:
        body = request.get_json(force=True) or {}
        role = body.get("role", "user")
        user = get_demo_user(role)
        if user:
            return jsonify({
                "success": True,
                "message": f"Authenticated as {user['role']} ({user['full_name']})",
                "user": user
            })
        return jsonify({"success": False, "error": "Demo profile not found."}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    return jsonify({
        "status": "online",
        "demo_profiles": [
            {"username": "admin", "name": "Administrator", "role": "Admin", "pass": "admin123"},
            {"username": "user", "name": "Verified User", "role": "User", "pass": "user123"},
            {"username": "guest", "name": "Guest Reviewer", "role": "Guest", "pass": "guest123"}
        ]
    })

# ==========================================
# 1. FRONTEND SERVING & DEDICATED PAGES
# ==========================================
@app.route("/")
@app.route("/login")
def landing_route():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_route():
    return render_template("dashboard.html")

@app.route("/individual")
def individual_route():
    return render_template("individual.html")

@app.route("/organization")
def organization_route():
    return render_template("organization.html")

@app.route("/state-nation")
def state_nation_route():
    return render_template("state_nation.html")

@app.route("/powerbi")
def powerbi_route():
    return render_template("powerbi.html")

@app.route("/predictive")
def predictive_route():
    return render_template("predictive.html")

@app.route("/overview")
def overview_route():
    return render_template("overview.html")


# ==========================================
# 2. EXECUTIVE OVERVIEW API
# ==========================================
@app.route("/api/overview", methods=["GET"])
def overview_api():
    year = request.args.get("year", "All")
    level = request.args.get("level", "All")
    data = get_executive_overview(year_filter=year, level_filter=level)
    return jsonify(data)

# ==========================================
# 3. INDIVIDUAL LEVEL API
# ==========================================
@app.route("/api/individual", methods=["GET"])
def individual_api():
    category = request.args.get("category", "All")
    year = request.args.get("year", "All")
    data = get_individual_analytics(category_filter=category, year_filter=year)
    return jsonify(data)

@app.route("/api/individual/calculate", methods=["POST"])
def calculate_individual_api():
    try:
        body = request.get_json(force=True) or {}
        res = calculate_custom_individual(body)
        return jsonify({"success": True, "data": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/individual/transaction", methods=["POST"])
def add_individual_transaction():
    try:
        body = request.get_json(force=True)
        tx_date = body.get("date", datetime.now().strftime("%Y-%m-%d"))
        mode = body.get("mode", "UPI")
        category = body.get("category", "Food & Dining")
        subcategory = body.get("subcategory", "General")
        note = body.get("note", "User Input")
        amount = float(body.get("amount", 0.0))
        income_expense = body.get("income_expense", "Expense")
        currency = body.get("currency", "INR")

        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be greater than zero."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO individual_transactions (date, mode, category, subcategory, note, amount, income_expense, currency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx_date, mode, category, subcategory, note, amount, income_expense, currency))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Append to CSVs so Power BI stays synchronized
        raw_csv = os.path.join(RAW_DATA_DIR, "individual_transactions.csv")
        clean_csv = os.path.join(CLEAN_DATA_DIR, "individual_clean.csv")

        # Read target budget for category
        target_budget = 5000.0
        try:
            conn_b = get_db_connection()
            b_row = conn_b.execute("SELECT monthly_budget FROM category_budgets WHERE category = ?", (category,)).fetchone()
            if b_row:
                target_budget = float(b_row[0])
            conn_b.close()
        except:
            pass

        try:
            new_raw_row = [tx_date, mode, category, subcategory, note, amount, income_expense, currency]
            with open(raw_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(new_raw_row)

            month_year = datetime.strptime(tx_date[:10], "%Y-%m-%d").strftime("%b %Y")
            new_clean_row = [tx_date, mode, category, subcategory, note, amount, income_expense, currency, month_year, target_budget]
            with open(clean_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(new_clean_row)
        except (OSError, IOError):
            # Read-only serverless environment (e.g. Vercel)
            pass

        return jsonify({
            "success": True,
            "message": "Transaction recorded successfully.",
            "id": new_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/individual/transaction/<int:tx_id>", methods=["DELETE"])
def delete_individual_transaction(tx_id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM individual_transactions WHERE id = ?", (tx_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Transaction #{tx_id} deleted."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/individual/budget", methods=["POST"])
def update_category_budget():
    try:
        body = request.get_json(force=True)
        category = body.get("category")
        monthly_budget = float(body.get("monthly_budget", 0.0))

        if not category:
            return jsonify({"success": False, "error": "Category name is required."}), 400

        conn = get_db_connection()
        conn.execute("INSERT OR REPLACE INTO category_budgets (category, monthly_budget) VALUES (?, ?)", (category, monthly_budget))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": f"Budget for '{category}' updated to ₹{monthly_budget:,.2f}."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# 4. ORGANIZATION LEVEL API
# ==========================================
@app.route("/api/organization", methods=["GET"])
def organization_api():
    department = request.args.get("department", "All")
    year = request.args.get("year", "All")
    data = get_organization_analytics(department_filter=department, year_filter=year)
    return jsonify(data)

@app.route("/api/organization/calculate", methods=["POST"])
def calculate_organization_api():
    try:
        body = request.get_json(force=True) or {}
        res = calculate_custom_organization(body)
        return jsonify({"success": True, "data": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/organization/order", methods=["POST"])
def add_organization_order():
    try:
        body = request.get_json(force=True)
        order_date = body.get("order_date", datetime.now().strftime("%Y-%m-%d"))
        ship_date = body.get("ship_date", order_date)
        ship_mode = body.get("ship_mode", "Standard Class")
        department = body.get("department", "Corporate") # Segment conceptually renamed
        region = body.get("region", "South")
        city = body.get("city", "Bengaluru")
        category = body.get("category", "Technology")
        subcategory = body.get("subcategory", "Phones")
        product_name = body.get("product_name", f"{subcategory} Enterprise Procurement")
        sales = float(body.get("sales", 0.0))
        profit = float(body.get("profit", 0.0))
        discount = float(body.get("discount", 0.0))
        quantity = int(body.get("quantity", 1))

        if sales <= 0:
            return jsonify({"success": False, "error": "Sales must be greater than zero."}), 400

        # Calculations from PDF:
        # Cost = Sales - Profit (departmental expenditure)
        # BudgetVariance = Sales - Cost (equivalent to profit)
        cost = round(sales - profit, 2)
        budget_variance = round(sales - cost, 2)

        order_id = f"CA-{order_date[:4]}-{datetime.now().strftime('%f')[:5]}"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO org_orders (order_id, order_date, ship_date, ship_mode, department, city, state, region, category, subcategory, product_name, sales, quantity, discount, profit, cost, budget_variance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, order_date, ship_date, ship_mode, department, city, f"{region} Region", region, category, subcategory, product_name, sales, quantity, discount, profit, cost, budget_variance))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Sync to CSVs
        raw_csv = os.path.join(RAW_DATA_DIR, "org_superstore.csv")
        clean_csv = os.path.join(CLEAN_DATA_DIR, "org_clean.csv")

        try:
            new_raw_row = [order_id, order_date, ship_date, ship_mode, department, city, f"{region} Region", region, category, subcategory, product_name, sales, quantity, discount, profit]
            with open(raw_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(new_raw_row)

            new_clean_row = [order_id, order_date, ship_date, ship_mode, department, city, f"{region} Region", region, category, subcategory, product_name, sales, quantity, discount, profit, cost, budget_variance]
            with open(clean_csv, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(new_clean_row)
        except (OSError, IOError):
            # Read-only serverless environment (e.g. Vercel)
            pass

        return jsonify({
            "success": True,
            "message": "Enterprise order/cost item logged successfully.",
            "id": new_id,
            "order_id": order_id
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/organization/order/<int:order_id>", methods=["DELETE"])
def delete_organization_order(order_id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM org_orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Order #{order_id} deleted."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# 5. STATE / NATION API
# ==========================================
@app.route("/api/state-nation", methods=["GET"])
def state_nation_api():
    year = request.args.get("year", "All")
    data = get_state_nation_analytics(year_filter=year)
    return jsonify(data)

# ==========================================
# 6. PREDICTIVE ANALYTICS & WHAT-IF SIMULATION API
# ==========================================
@app.route("/api/predictive", methods=["GET"])
def predictive_api():
    data = get_predictive_analytics()
    return jsonify(data)

@app.route("/api/predictive/simulate", methods=["POST"])
def simulate_predictive_api():
    try:
        body = request.get_json(force=True)
        ind_cut = float(body.get("whatif_ind_cut_pct", 0))
        org_growth = float(body.get("whatif_org_growth_pct", 0))
        state_deficit_target = float(body.get("whatif_state_deficit_target_pct", 0))
        data = get_predictive_analytics(
            whatif_ind_cut_pct=ind_cut,
            whatif_org_growth_pct=org_growth,
            whatif_state_deficit_target_pct=state_deficit_target
        )
        return jsonify(data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# 7. POWER BI ASSETS & EXPORT HUBS
# ==========================================
@app.route("/api/powerbi/theme", methods=["GET"])
def get_pbi_theme():
    theme_file = os.path.join(PBI_DIR, "navy_amber_teal_theme.json")
    with open(theme_file, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/api/powerbi/dax", methods=["GET"])
def get_pbi_dax():
    dax_file = os.path.join(PBI_DIR, "DAX_Measures_Library.dax")
    with open(dax_file, "r", encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "text/plain; charset=utf-8"}

@app.route("/api/powerbi/powerquery", methods=["GET"])
@app.route("/api/powerbi/pq", methods=["GET"])
def get_pbi_pq():
    pq_file = os.path.join(PBI_DIR, "PowerQuery_M_Cleaning.pq")
    with open(pq_file, "r", encoding="utf-8") as f:
        return f.read(), 200, {"Content-Type": "text/plain; charset=utf-8"}

@app.route("/api/powerbi/export-all", methods=["POST"])
def export_all_csvs():
    try:
        conn = get_db_connection()
        # Export Individual
        df_ind = pd.read_sql_query("SELECT * FROM individual_transactions", conn)
        df_budgets = pd.read_sql_query("SELECT * FROM category_budgets", conn)
        budget_map = dict(zip(df_budgets["category"], df_budgets["monthly_budget"])) if not df_budgets.empty else {}
        if not df_ind.empty and "date" in df_ind.columns:
            df_ind["MonthYear"] = pd.to_datetime(df_ind["date"]).dt.strftime("%b %Y")
            df_ind["MonthlyBudget"] = df_ind["category"].map(budget_map).fillna(5000.0)
        else:
            df_ind["MonthYear"] = pd.Series([], dtype=str)
            df_ind["MonthlyBudget"] = pd.Series([], dtype=float)
        df_ind.to_csv(os.path.join(CLEAN_DATA_DIR, "individual_clean.csv"), index=False)

        # Export Organization
        df_org = pd.read_sql_query("SELECT * FROM org_orders", conn)
        df_org.to_csv(os.path.join(CLEAN_DATA_DIR, "org_clean.csv"), index=False)

        # Export State
        df_state = pd.read_sql_query("SELECT * FROM state_finance", conn)
        df_state.to_csv(os.path.join(CLEAN_DATA_DIR, "state_clean.csv"), index=False)

        # Export National
        df_nat = pd.read_sql_query("SELECT * FROM national_budget", conn)
        df_nat.to_csv(os.path.join(CLEAN_DATA_DIR, "national_clean.csv"), index=False)
        conn.close()

        return jsonify({
            "success": True,
            "message": "All clean CSV datasets synchronized successfully! Ready for Power BI refresh."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/data/reload", methods=["POST"])
def reload_datasets_route():
    try:
        from backend.database import load_csvs_into_db
        count = load_csvs_into_db()
        return jsonify({
            "success": True,
            "message": f"Datasets reloaded into SQLite database ({count} records imported from CSVs).",
            "records_imported": count
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Download CSVs directly
@app.route("/data/raw/<filename>")
def download_raw_csv(filename):
    return send_from_directory(RAW_DATA_DIR, filename, as_attachment=True)

@app.route("/data/clean/<filename>")
def download_clean_csv(filename):
    return send_from_directory(CLEAN_DATA_DIR, filename, as_attachment=True)

@app.route("/data/powerbi/<filename>")
def download_pbi_file(filename):
    return send_from_directory(PBI_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
