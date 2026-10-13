import os
import csv
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "01_RawData")
CLEAN_DATA_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "02_CleanData")
PBI_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "03_PowerBI")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "BudgetTrackerAnalytics", "04_Screenshots")

for d in [RAW_DATA_DIR, CLEAN_DATA_DIR, PBI_DIR, SCREENSHOTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ==========================================
# 1. INDIVIDUAL LEVEL: Daily Household Transactions
# ==========================================
def generate_individual_transactions():
    print("Generating balanced Individual Transactions (~2,500 records)...")
    random.seed(42)
    np.random.seed(42)
    
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range_days = (end_date - start_date).days

    # Monthly target budgets per category (INR)
    expense_categories = {
        "Food & Dining": (["Swiggy/Zomato", "Restaurant", "Cafe Coffee Day", "Snacks"], 150, 1800, 16000),
        "Groceries": (["Supermarket Provisions", "Vegetables & Fruits", "Dairy & Milk", "Gourmet Essentials"], 300, 2500, 18000),
        "Housing & Rent": (["Apartment Rent", "Society Maintenance", "Water Supply"], 15000, 24000, 25000),
        "Utilities": (["BESCOM Electricity", "Airtel Fiber Broadband", "Indane LPG Cylinder", "Mobile Postpaid"], 400, 2200, 6500),
        "Transportation": (["Petrol Fuel", "Namma Metro Recharge", "Uber/Ola Rides", "Car Maintenance"], 180, 2200, 9000),
        "Entertainment": (["PVR Cinema Tickets", "Netflix/Amazon Prime", "Gaming", "Weekend Trip"], 250, 2800, 7000),
        "Healthcare": (["Apollo Pharmacy", "Doctor Consultation", "Dental Clinic", "Health Lab Tests"], 300, 3200, 6000),
        "Education": (["Technical Books", "Coursera Subscription", "Udemy Course", "Exam Certifications"], 450, 4500, 5000),
        "Shopping": (["Amazon Fashion", "Electronics Gadgets", "Footwear", "Home Decor"], 500, 6500, 11000),
        "Personal Care": (["Salon Grooming", "Cult.fit Gym", "Personal Hygiene Supplies"], 250, 2200, 4500)
    }

    income_categories = {
        "Salary": (["Monthly Corporate Salary", "Annual Incentive Bonus", "HRA Credit"], 115000, 155000),
        "Freelance": (["Fullstack Dev Consulting", "Technical Writing", "UI/UX Review"], 15000, 35000),
        "Investments": (["Zerodha Stock Dividends", "Mutual Fund SIP Dividend", "Fixed Deposit Interest"], 5000, 18000),
        "Rental Income": (["Residential Unit Rent"], 12000, 20000)
    }

    modes = ["UPI", "Card", "Cash", "Net Banking"]
    mode_weights = [0.58, 0.26, 0.11, 0.05]

    records = []
    
    # 1. Monthly Recurring Income (36 months)
    cur = datetime(2022, 1, 1)
    while cur <= end_date:
        salary_amt = round(random.uniform(120000, 160000), 2)
        records.append({
            "Date": cur.strftime("%Y-%m-%d"),
            "Mode": "Net Banking",
            "Category": "Salary",
            "Subcategory": "Monthly Corporate Salary",
            "Note": f"Salary Credit for {cur.strftime('%B %Y')}",
            "Amount": salary_amt,
            "Income/Expense": "Income",
            "Currency": "INR"
        })
        
        # Monthly Rent fixed transaction on 5th
        rent_date = cur + timedelta(days=4)
        rent_amt = round(random.uniform(22000, 25000), 2)
        records.append({
            "Date": rent_date.strftime("%Y-%m-%d"),
            "Mode": "Net Banking",
            "Category": "Housing & Rent",
            "Subcategory": "Apartment Rent",
            "Note": f"Monthly Apartment Rent {cur.strftime('%b %Y')}",
            "Amount": rent_amt,
            "Income/Expense": "Expense",
            "Currency": "INR"
        })

        # Regular investment/freelance income
        if random.random() < 0.75:
            inv_date = cur + timedelta(days=random.randint(8, 24))
            cat = random.choice(list(income_categories.keys())[1:])
            sub = random.choice(income_categories[cat][0])
            amt = round(random.uniform(income_categories[cat][1], income_categories[cat][2]), 2)
            records.append({
                "Date": inv_date.strftime("%Y-%m-%d"),
                "Mode": random.choices(modes, weights=mode_weights)[0],
                "Category": cat,
                "Subcategory": sub,
                "Note": f"Received {sub}",
                "Amount": amt,
                "Income/Expense": "Income",
                "Currency": "INR"
            })
            
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)

    # 2. Daily expenses (~2,400 expenses)
    for _ in range(2400):
        day_offset = random.randint(0, date_range_days)
        tx_date = start_date + timedelta(days=day_offset)
        
        # Pick category (skip Housing since rent is handled)
        cat_choices = [c for c in expense_categories.keys() if c != "Housing & Rent"]
        cat_name = random.choice(cat_choices)
        sub_list, min_amt, max_amt, _ = expense_categories[cat_name]
        sub = random.choice(sub_list)
        amt = round(random.uniform(min_amt, max_amt), 2)
        mode = random.choices(modes, weights=mode_weights)[0]
        
        records.append({
            "Date": tx_date.strftime("%Y-%m-%d"),
            "Mode": mode,
            "Category": cat_name,
            "Subcategory": sub,
            "Note": f"{sub} transaction",
            "Amount": amt,
            "Income/Expense": "Expense",
            "Currency": "INR"
        })

    records.sort(key=lambda x: x["Date"])
    
    # Save Raw CSV
    raw_path = os.path.join(RAW_DATA_DIR, "individual_transactions.csv")
    keys = ["Date", "Mode", "Category", "Subcategory", "Note", "Amount", "Income/Expense", "Currency"]
    with open(raw_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)

    # Clean CSV with MonthlyBudget
    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])
    df["MonthYear"] = df["Date"].dt.strftime("%b %Y")
    
    category_budget_targets = {k: v[3] for k, v in expense_categories.items()}
    category_budget_targets["Salary"] = 0
    category_budget_targets["Freelance"] = 0
    category_budget_targets["Investments"] = 0
    category_budget_targets["Rental Income"] = 0

    df["MonthlyBudget"] = df["Category"].map(category_budget_targets).fillna(5000.0)
    
    clean_path = os.path.join(CLEAN_DATA_DIR, "individual_clean.csv")
    df.to_csv(clean_path, index=False)
    print(f"  -> Regenerated individual dataset ({len(records)} rows)")

# ==========================================
# 2. ORGANIZATION LEVEL: Superstore Dataset
# ==========================================
def generate_organization_superstore():
    print("Generating Organization Superstore Dataset (~3,200 records)...")
    random.seed(101)
    np.random.seed(101)

    start_date = datetime(2021, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range_days = (end_date - start_date).days

    departments = ["Consumer", "Corporate", "Home Office"]
    regions = {
        "North": ["Delhi", "Chandigarh", "Jaipur", "Lucknow", "Noida"],
        "South": ["Bengaluru", "Chennai", "Hyderabad", "Kochi", "Mysuru"],
        "West": ["Mumbai", "Pune", "Ahmedabad", "Surat", "Nagpur"],
        "East": ["Kolkata", "Bhubaneswar", "Patna", "Ranchi", "Guwahati"]
    }
    
    catalog = {
        "Technology": {
            "Phones": ["Cisco IP Phone", "Samsung Enterprise Galaxy", "Apple iPhone Corp", "Polycom VoIP Deskset"],
            "Accessories": ["Logitech MX Master", "Dell USB-C Dock", "SanDisk 1TB SSD", "Anker PowerPort Hub"],
            "Machines": ["HP LaserJet Pro Enterprise", "Zebra Thermal Label Printer", "Epson Business Projector"],
            "Copiers": ["Canon ImageRunner Advance", "Sharp Enterprise Copier", "Kyocera Multifunction"]
        },
        "Furniture": {
            "Chairs": ["Herman Miller Aeron", "Steelcase Leap Chair", "Executive High-Back Leather", "Ergonomic Mesh Chair"],
            "Tables": ["Conference 10-Seater Table", "Height Adjustable Standing Desk", "Modular Workstation Desk"],
            "Bookcases": ["DuraSteel 5-Tier Shelving", "Oak Executive Bookcase", "Heavy Duty Storage Unit"],
            "Furnishings": ["Acoustic Sound Dampeners", "Desk Privacy Panels", "LED Ergonomic Desk Lamp"]
        },
        "Office Supplies": {
            "Storage": ["Fireproof Security Filing Cabinet", "Fellowes Heavy Storage Box", "Steel Lockers 4-Door"],
            "Supplies": ["Paper Trimmer Heavy Duty", "Staple Pro Cartridge Pack", "High-Volume Hole Punch"],
            "Binders": ["Presentation Ring Binder Box", "Heavy Duty Thermal Binder", "Index Tab Dividers Bulk"],
            "Paper": ["Multi-purpose Copy Paper A4 Pallet", "Heavy Cardstock 250gsm", "Continuous Feed Invoice Paper"],
            "Art": ["Presentation Whiteboard 6x4ft", "Magnetic Planning Board Kit", "Glass Dry-Erase Wall Panel"]
        }
    }

    ship_modes = ["Standard Class", "Second Class", "First Class", "Same Day"]
    ship_weights = [0.60, 0.20, 0.15, 0.05]

    records = []
    order_id_counter = 10001

    for _ in range(3200):
        day_offset = random.randint(0, date_range_days)
        order_date = start_date + timedelta(days=day_offset)
        ship_date = order_date + timedelta(days=random.randint(1, 6))

        dept = random.choice(departments)
        reg = random.choice(list(regions.keys()))
        city = random.choice(regions[reg])
        cat = random.choice(list(catalog.keys()))
        sub_cat = random.choice(list(catalog[cat].keys()))
        product = random.choice(catalog[cat][sub_cat])
        ship_mode = random.choices(ship_modes, weights=ship_weights)[0]

        qty = random.randint(1, 14)
        
        if cat == "Technology":
            unit_price = random.uniform(2500, 38000)
            margin = random.uniform(0.18, 0.38)
        elif cat == "Furniture":
            unit_price = random.uniform(2200, 26000)
            margin = random.uniform(0.10, 0.26)
        else:
            unit_price = random.uniform(350, 4800)
            margin = random.uniform(0.20, 0.42)

        discount = random.choice([0.0, 0.05, 0.10, 0.15, 0.20])
        gross_sales = unit_price * qty
        sales = round(gross_sales * (1 - discount), 2)
        
        # Mostly profitable, occasional tight margin or small loss
        if discount >= 0.20 and random.random() < 0.25:
            profit = round(-1 * sales * random.uniform(0.04, 0.12), 2)
        else:
            profit = round(sales * margin, 2)

        order_id = f"CA-{order_date.year}-{order_id_counter}"
        order_id_counter += 1

        records.append({
            "Order ID": order_id,
            "Order Date": order_date.strftime("%Y-%m-%d"),
            "Ship Date": ship_date.strftime("%Y-%m-%d"),
            "Ship Mode": ship_mode,
            "Segment": dept,
            "City": city,
            "State": reg + " Region",
            "Region": reg,
            "Category": cat,
            "Sub-Category": sub_cat,
            "Product Name": product,
            "Sales": sales,
            "Quantity": qty,
            "Discount": discount,
            "Profit": profit
        })

    records.sort(key=lambda x: x["Order Date"])

    raw_path = os.path.join(RAW_DATA_DIR, "org_superstore.csv")
    keys = list(records[0].keys())
    with open(raw_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)

    df = pd.DataFrame(records)
    df.rename(columns={"Segment": "Department"}, inplace=True)
    df["Cost"] = (df["Sales"] - df["Profit"]).round(2)
    df["BudgetVariance"] = (df["Sales"] - df["Cost"]).round(2)
    
    clean_path = os.path.join(CLEAN_DATA_DIR, "org_clean.csv")
    df.to_csv(clean_path, index=False)
    print(f"  -> Regenerated organization dataset ({len(records)} rows)")

# ==========================================
# 3. STATE LEVEL
# ==========================================
def generate_state_finance_india():
    print("Generating State Finance India Dataset...")
    random.seed(202)
    
    states = [
        ("Maharashtra", 380000, 1.08),
        ("Tamil Nadu", 270000, 1.07),
        ("Karnataka", 240000, 1.08),
        ("Gujarat", 230000, 1.09),
        ("Uttar Pradesh", 320000, 1.09),
        ("West Bengal", 195000, 1.06),
        ("Rajasthan", 185000, 1.07),
        ("Telangana", 175000, 1.08),
        ("Kerala", 145000, 1.06),
        ("Madhya Pradesh", 180000, 1.07),
        ("Andhra Pradesh", 170000, 1.07),
        ("Punjab", 110000, 1.05),
        ("Delhi", 85000, 1.08),
        ("Odisha", 130000, 1.08),
        ("Haryana", 125000, 1.07)
    ]
    
    years = list(range(2014, 2025))
    records = []

    for state, base_rev_2024, growth in states:
        for year in years:
            power = year - 2024
            year_rev = base_rev_2024 * (growth ** power) * random.uniform(0.98, 1.02)
            deficit_pct = random.uniform(0.04, 0.09)
            year_exp = year_rev * (1.0 + deficit_pct)
            year_fiscal_deficit = round(year_rev - year_exp, 2)
            year_debt = round(year_rev * random.uniform(2.1, 3.2), 2)
            
            records.append({"State": state, "Year": year, "Indicator": "Revenue", "Value": round(year_rev, 2)})
            records.append({"State": state, "Year": year, "Indicator": "Expenditure", "Value": round(year_exp, 2)})
            records.append({"State": state, "Year": year, "Indicator": "Fiscal Deficit", "Value": year_fiscal_deficit})
            records.append({"State": state, "Year": year, "Indicator": "Debt", "Value": year_debt})

    raw_path = os.path.join(RAW_DATA_DIR, "state_finance_india.csv")
    keys = ["State", "Year", "Indicator", "Value"]
    with open(raw_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)

    clean_path = os.path.join(CLEAN_DATA_DIR, "state_clean.csv")
    pd.DataFrame(records).to_csv(clean_path, index=False)
    print(f"  -> Regenerated state dataset ({len(records)} rows)")

# ==========================================
# 4. NATION LEVEL
# ==========================================
def generate_national_union_budget():
    print("Generating National Union Budget Dataset...")
    random.seed(303)

    sectors = [
        ("Ministry of Defence", "Defence", 621540),
        ("Ministry of Road Transport & Highways", "Infrastructure", 278000),
        ("Ministry of Railways", "Infrastructure", 255000),
        ("Ministry of Consumer Affairs & Food", "Food Security & Subsidy", 213000),
        ("Ministry of Agriculture & Farmers Welfare", "Agriculture", 132000),
        ("Ministry of Rural Development", "Rural Development", 180000),
        ("Ministry of Education", "Human Capital & Education", 125000),
        ("Ministry of Health & Family Welfare", "Healthcare", 90000),
        ("Ministry of Home Affairs", "Internal Security", 202000),
        ("Ministry of Communications & IT", "Technology & Telecom", 115000),
        ("Ministry of Power & Renewable Energy", "Energy Transition", 85000),
        ("Ministry of Housing & Urban Affairs", "Urban Development", 82000)
    ]

    records = []
    years = [2021, 2022, 2023, 2024]

    for ministry, sector, base_alloc_2024 in sectors:
        for yr in years:
            factor = (1.09) ** (yr - 2024)
            alloc = round(base_alloc_2024 * factor * random.uniform(0.98, 1.02), 2)
            util_rate = random.uniform(0.94, 0.99)
            exp = round(alloc * util_rate, 2)
            
            records.append({
                "Ministry": ministry,
                "Sector": sector,
                "Year": yr,
                "Allocation": alloc,
                "Expenditure": exp
            })

    raw_path = os.path.join(RAW_DATA_DIR, "national_union_budget.csv")
    keys = ["Ministry", "Sector", "Year", "Allocation", "Expenditure"]
    with open(raw_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)

    clean_path = os.path.join(CLEAN_DATA_DIR, "national_clean.csv")
    pd.DataFrame(records).to_csv(clean_path, index=False)
    print(f"  -> Regenerated national dataset ({len(records)} rows)")

# ==========================================
# 5. SHARED DATE TABLE
# ==========================================
def generate_shared_date_table():
    print("Generating Shared Date Table (2014-2025)...")
    start_date = datetime(2014, 1, 1)
    end_date = datetime(2025, 12, 31)

    date_list = []
    curr = start_date
    while curr <= end_date:
        date_list.append({
            "Date": curr.strftime("%Y-%m-%d"),
            "Year": curr.year,
            "MonthName": curr.strftime("%b"),
            "MonthNum": curr.month,
            "Quarter": f"Q{(curr.month - 1) // 3 + 1}",
            "MonthYear": curr.strftime("%b %Y")
        })
        curr += timedelta(days=1)

    clean_path = os.path.join(CLEAN_DATA_DIR, "DateTable.csv")
    keys = ["Date", "Year", "MonthName", "MonthNum", "Quarter", "MonthYear"]
    with open(clean_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(date_list)

if __name__ == "__main__":
    generate_individual_transactions()
    generate_organization_superstore()
    generate_state_finance_india()
    generate_national_union_budget()
    generate_shared_date_table()
    print("All balanced datasets regenerated successfully!")
