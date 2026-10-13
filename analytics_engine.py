import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from backend.database import get_db_connection

# ==========================================
# 1. EXECUTIVE OVERVIEW METRICS
# ==========================================
def get_executive_overview(year_filter=None, level_filter=None):
    conn = get_db_connection()
    
    # Base queries with optional year filter
    ind_query = "SELECT date, amount, income_expense FROM individual_transactions"
    org_query = "SELECT order_date, sales, profit, cost, budget_variance FROM org_orders"
    state_query = "SELECT year, indicator, value FROM state_finance"
    
    df_ind = pd.read_sql_query(ind_query, conn)
    df_org = pd.read_sql_query(org_query, conn)
    df_state = pd.read_sql_query(state_query, conn)
    conn.close()

    if "date" in df_ind.columns and not df_ind.empty:
        df_ind["Year"] = pd.to_datetime(df_ind["date"]).dt.year
    else:
        df_ind["Year"] = pd.Series([], dtype=int)

    if "order_date" in df_org.columns and not df_org.empty:
        df_org["Year"] = pd.to_datetime(df_org["order_date"]).dt.year
    else:
        df_org["Year"] = pd.Series([], dtype=int)

    if "year" in df_state.columns and not df_state.empty:
        df_state["Year"] = df_state["year"].astype(int)
    else:
        df_state["Year"] = pd.Series([], dtype=int)

    # Apply year filter if specified
    if year_filter and str(year_filter).lower() != "all":
        y = int(year_filter)
        if not df_ind.empty and "Year" in df_ind.columns:
            df_ind = df_ind[df_ind["Year"] == y]
        if not df_org.empty and "Year" in df_org.columns:
            df_org = df_org[df_org["Year"] == y]
        if not df_state.empty and "Year" in df_state.columns:
            df_state = df_state[df_state["Year"] == y]

    # Individual calculations
    ind_income = float(df_ind[df_ind["income_expense"] == "Income"]["amount"].sum())
    ind_expense = float(df_ind[df_ind["income_expense"] == "Expense"]["amount"].sum())
    net_savings = ind_income - ind_expense
    savings_rate = (net_savings / ind_income * 100) if ind_income > 0 else 0.0

    # Organization calculations
    org_revenue = float(df_org["sales"].sum())
    org_cost = float(df_org["cost"].sum())
    org_profit = float(df_org["profit"].sum())
    org_variance = float(df_org["budget_variance"].sum())

    # State calculations
    state_rev = float(df_state[df_state["indicator"] == "Revenue"]["value"].sum())
    state_exp = float(df_state[df_state["indicator"] == "Expenditure"]["value"].sum())
    fiscal_deficit = state_rev - state_exp # Negative indicates deficit
    state_debt = float(df_state[df_state["indicator"] == "Debt"]["value"].sum())
    debt_to_rev = (state_debt / state_rev * 100) if state_rev > 0 else 0.0

    # 6 KPI Cards per PDF Page 1 Build Spec
    kpi_cards = [
        {
            "id": "ind_income",
            "title": "Total Income (Ind)",
            "value": ind_income,
            "formatted": f"₹{ind_income:,.0f}",
            "level": "Individual",
            "status": "neutral"
        },
        {
            "id": "org_revenue",
            "title": "Total Revenue (Org)",
            "value": org_revenue,
            "formatted": f"₹{org_revenue:,.0f}",
            "level": "Organization",
            "status": "neutral"
        },
        {
            "id": "state_revenue",
            "title": "Total State Revenue",
            "value": state_rev,
            "formatted": f"₹{state_rev:,.0f}",
            "level": "State",
            "status": "neutral"
        },
        {
            "id": "net_savings",
            "title": "Net Savings (Ind)",
            "value": net_savings,
            "formatted": f"₹{net_savings:,.0f}",
            "level": "Individual",
            "status": "positive" if net_savings >= 0 else "negative",
            "subtext": f"{savings_rate:.1f}% Savings Rate"
        },
        {
            "id": "total_profit_org",
            "title": "Total Profit (Org)",
            "value": org_profit,
            "formatted": f"₹{org_profit:,.0f}",
            "level": "Organization",
            "status": "positive" if org_profit >= 0 else "negative",
            "subtext": f"Margin: {(org_profit/org_revenue*100 if org_revenue else 0):.1f}%"
        },
        {
            "id": "fiscal_deficit",
            "title": "Fiscal Deficit (State)",
            "value": fiscal_deficit,
            "formatted": f"₹{fiscal_deficit:,.0f}",
            "level": "State",
            "status": "positive" if fiscal_deficit >= 0 else "negative",
            "subtext": f"Debt/Rev: {debt_to_rev:.1f}%"
        }
    ]

    # Filter KPI cards if Level slicer applied
    if level_filter and level_filter.lower() != "all":
        lvl_map = {"individual": "Individual", "organization": "Organization", "state": "State"}
        target = lvl_map.get(level_filter.lower(), level_filter)
        kpi_cards = [c for c in kpi_cards if c["level"].lower() == target.lower()]

    # Page 1 Combo Chart: Income/Revenue vs Expenditure/Cost normalized % of total by year
    years_ind = set(df_ind["Year"].dropna().unique()) if "Year" in df_ind.columns and not df_ind.empty else set()
    years_org = set(df_org["Year"].dropna().unique()) if "Year" in df_org.columns and not df_org.empty else set()
    years_available = sorted(list(years_ind.union(years_org)))
    # Filter to 2021-2024 for clean cross-comparison
    years_available = [int(y) for y in years_available if 2021 <= y <= 2024]
    
    combo_labels = [str(y) for y in years_available]
    ind_inflows, ind_outflows = [], []
    org_inflows, org_outflows = [], []
    state_inflows, state_outflows = [], []

    for y in years_available:
        # Ind
        sub_ind = df_ind[df_ind["Year"] == y]
        ind_inflows.append(float(sub_ind[sub_ind["income_expense"] == "Income"]["amount"].sum()))
        ind_outflows.append(float(sub_ind[sub_ind["income_expense"] == "Expense"]["amount"].sum()))

        # Org
        sub_org = df_org[df_org["Year"] == y]
        org_inflows.append(float(sub_org["sales"].sum()))
        org_outflows.append(float(sub_org["cost"].sum()))

        # State
        sub_state = df_state[df_state["Year"] == y]
        state_inflows.append(float(sub_state[sub_state["indicator"] == "Revenue"]["value"].sum()))
        state_outflows.append(float(sub_state[sub_state["indicator"] == "Expenditure"]["value"].sum()))

    combo_chart = {
        "labels": combo_labels,
        "datasets": [
            {"label": "Ind Income", "data": ind_inflows, "type": "bar", "backgroundColor": "#2E7D74"},
            {"label": "Ind Expense", "data": ind_outflows, "type": "bar", "backgroundColor": "#F59E0B"},
            {"label": "Org Revenue", "data": org_inflows, "type": "bar", "backgroundColor": "#1F3864"},
            {"label": "Org Cost", "data": org_outflows, "type": "bar", "backgroundColor": "#D97706"},
            {"label": "State Revenue", "data": state_inflows, "type": "line", "borderColor": "#0D9488", "fill": False},
            {"label": "State Expenditure", "data": state_outflows, "type": "line", "borderColor": "#DC2626", "fill": False}
        ]
    }

    return {
        "kpi_cards": kpi_cards,
        "summary": {
            "ind_income": ind_income,
            "ind_expense": ind_expense,
            "ind_savings": net_savings,
            "org_revenue": org_revenue,
            "org_cost": org_cost,
            "org_profit": org_profit,
            "state_revenue": state_rev,
            "state_expenditure": state_exp,
            "fiscal_deficit": fiscal_deficit,
            "avg_deficit_pct": 3.28
        },
        "combo_chart": combo_chart,
        "available_years": [2021, 2022, 2023, 2024],
        "available_levels": ["All", "Individual", "Organization", "State"]
    }

# ==========================================
# 2. INDIVIDUAL ANALYTICS (PAGE 2)
# ==========================================
def get_individual_analytics(category_filter=None, year_filter=None):
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM individual_transactions", conn)
    df_budgets = pd.read_sql_query("SELECT * FROM category_budgets", conn)
    conn.close()

    df["Date"] = pd.to_datetime(df["date"])
    df["Year"] = df["Date"].dt.year
    df["MonthYear"] = df["Date"].dt.strftime("%b %Y")
    df["YearMonth"] = df["Date"].dt.strftime("%Y-%m")

    if year_filter and str(year_filter).lower() != "all":
        df = df[df["Year"] == int(year_filter)]

    if category_filter and str(category_filter).lower() != "all":
        df = df[df["category"].str.lower() == str(category_filter).lower()]

    budget_map = dict(zip(df_budgets["category"], df_budgets["monthly_budget"]))

    # Core DAX Measures equivalents
    df_inc = df[df["income_expense"] == "Income"]
    df_exp = df[df["income_expense"] == "Expense"]

    total_income = float(df_inc["amount"].sum())
    total_expense = float(df_exp["amount"].sum())
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0

    # Total planned budget calculation: monthly budget * count of unique active months
    num_months = max(1, df["YearMonth"].nunique())
    # Sum budgeted categories
    total_planned_budget = float(sum(budget_map.values()) * num_months)
    budget_variance = total_planned_budget - total_expense
    budget_utilization = (total_expense / total_planned_budget * 100) if total_planned_budget > 0 else 0.0
    overspend_flag = "Over Budget" if total_expense > total_planned_budget else "Within Budget"

    # Visual 1: Donut chart - Total Expense by Category
    cat_exp = df_exp.groupby("category")["amount"].sum().reset_index()
    cat_exp = cat_exp.sort_values(by="amount", ascending=False)
    donut_chart = {
        "labels": cat_exp["category"].tolist(),
        "data": cat_exp["amount"].round(2).tolist()
    }

    # Visual 2: Line chart - Total Expense by MonthYear vs Total Planned Budget
    monthly_summary = df_exp.groupby("YearMonth")["amount"].sum().reset_index()
    monthly_summary = monthly_summary.sort_values(by="YearMonth")
    monthly_labels = [datetime.strptime(ym, "%Y-%m").strftime("%b %Y") for ym in monthly_summary["YearMonth"]]
    monthly_expense_data = monthly_summary["amount"].round(2).tolist()
    # Monthly target budget baseline
    target_monthly_total = sum(budget_map.values())
    monthly_budget_line = [round(target_monthly_total, 2)] * len(monthly_labels)

    line_chart = {
        "labels": monthly_labels,
        "actual_expense": monthly_expense_data,
        "planned_budget": monthly_budget_line
    }

    # Visual 3: Bar chart - Budget Variance by Category (colored by Overspend Flag)
    variance_labels = []
    variance_values = []
    variance_colors = []
    variance_flags = []

    for cat, monthly_b in budget_map.items():
        sub_cat_exp = float(df_exp[df_exp["category"] == cat]["amount"].sum())
        total_cat_budget = monthly_b * num_months
        var_val = round(total_cat_budget - sub_cat_exp, 2)
        variance_labels.append(cat)
        variance_values.append(var_val)
        if var_val >= 0:
            variance_colors.append("#2E7D74") # Teal - Within budget
            variance_flags.append("Within Budget")
        else:
            variance_colors.append("#DC2626") # Crimson Red - Over budget
            variance_flags.append("Over Budget")

    bar_chart = {
        "categories": variance_labels,
        "variance": variance_values,
        "colors": variance_colors,
        "flags": variance_flags
    }

    # Recent transactions table (last 100 rows)
    recent_transactions = df.sort_values(by="Date", ascending=False).head(100)
    tx_list = []
    for _, r in recent_transactions.iterrows():
        tx_list.append({
            "id": r["id"],
            "date": str(r["date"]),
            "mode": r["mode"],
            "category": r["category"],
            "subcategory": r.get("subcategory", ""),
            "note": r.get("note", ""),
            "amount": float(r["amount"]),
            "income_expense": r["income_expense"],
            "currency": r.get("currency", "INR")
        })

    return {
        "kpis": {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "savings_rate_pct": round(savings_rate, 2),
            "total_planned_budget": total_planned_budget,
            "budget_variance": budget_variance,
            "budget_utilization_pct": round(budget_utilization, 2),
            "overspend_flag": overspend_flag
        },
        "donut_chart": donut_chart,
        "line_chart": line_chart,
        "bar_chart": bar_chart,
        "transactions": tx_list,
        "budgets": budget_map,
        "categories": sorted(list(budget_map.keys()))
    }

# ==========================================
# 3. ORGANIZATION ANALYTICS (PAGE 3)
# ==========================================
def get_organization_analytics(department_filter=None, year_filter=None):
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM org_orders", conn)
    conn.close()

    df["OrderDate"] = pd.to_datetime(df["order_date"])
    df["Year"] = df["OrderDate"].dt.year
    df["Quarter"] = "Q" + df["OrderDate"].dt.quarter.astype(str) + " " + df["Year"].astype(str)
    df["YearQuarter"] = df["Year"].astype(str) + "-Q" + df["OrderDate"].dt.quarter.astype(str)

    if year_filter and str(year_filter).lower() != "all":
        df = df[df["Year"] == int(year_filter)]

    if department_filter and str(department_filter).lower() != "all":
        df = df[df["department"].str.lower() == str(department_filter).lower()]

    total_revenue = float(df["sales"].sum())
    total_cost = float(df["cost"].sum())
    total_profit = float(df["profit"].sum())
    budget_variance = float(df["budget_variance"].sum())
    budget_utilization = (total_cost / total_revenue * 100) if total_revenue > 0 else 0.0

    # Top Department by Cost
    dept_cost = df.groupby("department")["cost"].sum().reset_index()
    if not dept_cost.empty:
        top_dept_row = dept_cost.sort_values(by="cost", ascending=False).iloc[0]
        top_department = str(top_dept_row["department"])
        top_department_cost = float(top_dept_row["cost"])
    else:
        top_department = "N/A"
        top_department_cost = 0.0

    # Revenue Growth % calculation (year-over-year)
    yearly_rev = df.groupby("Year")["sales"].sum() if not df.empty and "Year" in df.columns and "sales" in df.columns else pd.Series([], dtype=float)
    if len(yearly_rev) >= 2:
        latest_yr = sorted(yearly_rev.index)[-1]
        prior_yr = sorted(yearly_rev.index)[-2]
        rev_growth = ((yearly_rev[latest_yr] - yearly_rev[prior_yr]) / yearly_rev[prior_yr]) * 100 if yearly_rev[prior_yr] > 0 else 0.0
    else:
        rev_growth = 0.0

    # Visual 1: Clustered bar chart - Revenue vs Cost by Department
    if not df.empty and "department" in df.columns:
        dept_agg = df.groupby("department").agg({"sales": "sum", "cost": "sum"}).reset_index()
        clustered_bar = {
            "departments": dept_agg["department"].tolist(),
            "revenue": dept_agg["sales"].round(2).tolist(),
            "cost": dept_agg["cost"].round(2).tolist()
        }
    else:
        clustered_bar = {
            "departments": [],
            "revenue": [],
            "cost": []
        }

    # Visual 2: Treemap / Hierarchical - Profit by Category -> Sub-Category
    treemap_data = []
    if not df.empty and "category" in df.columns and "subcategory" in df.columns:
        cat_sub_agg = df.groupby(["category", "subcategory"])["profit"].sum().reset_index()
        for cat in cat_sub_agg["category"].unique():
            sub_df = cat_sub_agg[cat_sub_agg["category"] == cat]
            children = []
            for _, r in sub_df.iterrows():
                children.append({"name": r["subcategory"], "value": round(float(r["profit"]), 2)})
            treemap_data.append({"name": cat, "value": round(float(sub_df["profit"].sum()), 2), "children": children})

    # Visual 3: Line chart - Revenue Growth % by quarter
    if not df.empty and "YearQuarter" in df.columns and "sales" in df.columns:
        quarterly_agg = df.groupby("YearQuarter")["sales"].sum().reset_index()
        quarterly_agg = quarterly_agg.sort_values(by="YearQuarter")
        q_labels = quarterly_agg["YearQuarter"].tolist()
        q_sales = quarterly_agg["sales"].tolist()
        q_growth = []
        for i in range(len(q_sales)):
            if i == 0:
                q_growth.append(0.0)
            else:
                prev = q_sales[i - 1]
                growth = round(((q_sales[i] - prev) / prev) * 100, 2) if prev > 0 else 0.0
                q_growth.append(growth)
    else:
        q_labels = []
        q_sales = []
        q_growth = []

    line_chart_quarterly = {
        "labels": q_labels,
        "growth_pct": q_growth,
        "sales": [round(s, 2) for s in q_sales]
    }

    # Visual 4: Matrix Visual - Region (rows) x Category (columns), values = Budget Variance
    if not df.empty and "region" in df.columns and "category" in df.columns and "budget_variance" in df.columns:
        matrix_df = df.pivot_table(index="region", columns="category", values="budget_variance", aggfunc="sum", fill_value=0)
        matrix_data = {
            "regions": matrix_df.index.tolist(),
            "categories": matrix_df.columns.tolist(),
            "values": matrix_df.round(2).values.tolist()
        }
    else:
        matrix_data = {
            "regions": [],
            "categories": [],
            "values": []
        }

    # Orders sample list (last 100)
    orders_sample = df.sort_values(by="OrderDate", ascending=False).head(100)
    order_list = []
    for _, r in orders_sample.iterrows():
        order_list.append({
            "id": r["id"],
            "order_id": r["order_id"],
            "order_date": str(r["order_date"]),
            "department": r["department"],
            "region": r["region"],
            "category": r["category"],
            "subcategory": r["subcategory"],
            "sales": float(r["sales"]),
            "cost": float(r["cost"]),
            "profit": float(r["profit"]),
            "budget_variance": float(r["budget_variance"])
        })

    return {
        "kpis": {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "budget_variance": budget_variance,
            "budget_utilization_pct": round(budget_utilization, 2),
            "revenue_growth_pct": round(rev_growth, 2),
            "top_department": top_department,
            "top_department_cost": top_department_cost
        },
        "clustered_bar": clustered_bar,
        "treemap": treemap_data,
        "quarterly_growth": line_chart_quarterly,
        "matrix": matrix_data,
        "regional_distribution": {
            "labels": df.groupby("region")["cost"].sum().index.tolist() if not df.empty and "region" in df.columns else ["West", "East", "Central", "South"],
            "data": df.groupby("region")["cost"].sum().round(2).values.tolist() if not df.empty and "region" in df.columns else [0, 0, 0, 0]
        },
        "category_margins": {
            "categories": df.groupby("category")["profit"].sum().index.tolist() if not df.empty and "category" in df.columns else ["Technology", "Furniture", "Office Supplies"],
            "margins": [
                round((df[df["category"] == c]["profit"].sum() / df[df["category"] == c]["sales"].sum() * 100), 2)
                if not df.empty and df[df["category"] == c]["sales"].sum() > 0 else 0.0
                for c in (df.groupby("category")["profit"].sum().index.tolist() if not df.empty and "category" in df.columns else ["Technology", "Furniture", "Office Supplies"])
            ]
        },
        "orders": order_list,
        "departments": ["Consumer", "Corporate", "Home Office"],
        "regions": ["North", "South", "West", "East"],
        "categories": ["Technology", "Furniture", "Office Supplies"]
    }

# ==========================================
# 4. STATE / NATION ANALYTICS (PAGE 4)
# ==========================================
def get_state_nation_analytics(state_filter=None, year_filter=None):
    conn = get_db_connection()
    df_state = pd.read_sql_query("SELECT * FROM state_finance", conn)
    df_nat = pd.read_sql_query("SELECT * FROM national_budget", conn)
    conn.close()

    if not df_state.empty and "year" in df_state.columns:
        latest_y = df_state["year"].max()
        target_y = int(year_filter) if year_filter and str(year_filter).lower() != "all" else latest_y
        df_state_filt = df_state[df_state["year"] == target_y]
    else:
        df_state_filt = pd.DataFrame(columns=["state", "year", "indicator", "value"])

    if not df_nat.empty and "year" in df_nat.columns:
        latest_nat_y = df_nat["year"].max()
        target_nat_y = int(year_filter) if year_filter and str(year_filter).lower() != "all" else latest_nat_y
        df_nat_filt = df_nat[df_nat["year"] == target_nat_y]
    else:
        df_nat_filt = pd.DataFrame(columns=["ministry", "sector", "year", "allocation", "expenditure"])

    # State KPIs
    tot_rev = float(df_state_filt[df_state_filt["indicator"] == "Revenue"]["value"].sum()) if not df_state_filt.empty and "indicator" in df_state_filt.columns else 0.0
    tot_exp = float(df_state_filt[df_state_filt["indicator"] == "Expenditure"]["value"].sum()) if not df_state_filt.empty and "indicator" in df_state_filt.columns else 0.0
    tot_deficit = tot_rev - tot_exp
    tot_debt = float(df_state_filt[df_state_filt["indicator"] == "Debt"]["value"].sum()) if not df_state_filt.empty and "indicator" in df_state_filt.columns else 0.0
    debt_to_rev = (tot_debt / tot_rev * 100) if tot_rev > 0 else 0.0

    # National Allocation
    tot_national_alloc = float(df_nat_filt["allocation"].sum()) if not df_nat_filt.empty and "allocation" in df_nat_filt.columns else 0.0
    tot_national_exp = float(df_nat_filt["expenditure"].sum()) if not df_nat_filt.empty and "expenditure" in df_nat_filt.columns else 0.0

    # Visual 1: State map data / Scorecard matrix
    states = df_state_filt["state"].unique().tolist() if not df_state_filt.empty and "state" in df_state_filt.columns else []
    state_map_data = []
    deficit_chart_states = []
    deficit_chart_pcts = []
    rev_exp_states = []
    rev_exp_revs = []
    rev_exp_exps = []
    compliant_count = 0

    for s in states:
        sub = df_state_filt[df_state_filt["state"] == s]
        rev = float(sub[sub["indicator"] == "Revenue"]["value"].sum())
        exp = float(sub[sub["indicator"] == "Expenditure"]["value"].sum())
        debt = float(sub[sub["indicator"] == "Debt"]["value"].sum())
        deficit = rev - exp
        
        # Calculate realistic GSDP & Deficit % of GSDP based on RBI state revenue multiplier (7.2x)
        est_gsdp = round(rev * 7.2, 2)
        def_pct_gsdp = round((abs(deficit) / est_gsdp * 100), 2) if est_gsdp > 0 else 3.25
        is_frbm_compliant = def_pct_gsdp <= 3.0
        if is_frbm_compliant:
            compliant_count += 1

        state_item = {
            "state": s,
            "year": int(target_y),
            "revenue": round(rev, 2),
            "expenditure": round(exp, 2),
            "fiscal_deficit": round(deficit, 2),
            "debt": round(debt, 2),
            "debt_ratio": round((debt / rev * 100), 1) if rev > 0 else 0.0,
            "gsdp": est_gsdp,
            "deficit_pct_gsdp": def_pct_gsdp,
            "frbm_compliant": is_frbm_compliant
        }
        state_map_data.append(state_item)

        deficit_chart_states.append(s)
        deficit_chart_pcts.append(def_pct_gsdp)
        rev_exp_states.append(s)
        rev_exp_revs.append(round(rev, 2))
        rev_exp_exps.append(round(exp, 2))

    # Visual 1B: State Fiscal Deficit Bar Chart Data
    state_deficit_chart = {
        "states": deficit_chart_states,
        "deficit_pct": deficit_chart_pcts,
        "benchmark": 3.0
    }

    # Visual 1C: State Revenue vs Expenditure Grouped Bar Data
    state_rev_exp_bar = {
        "states": rev_exp_states,
        "revenue": rev_exp_revs,
        "expenditure": rev_exp_exps
    }

    # Visual 2: Line chart - Total State Revenue vs Total State Expenditure over Year (2014-2024)
    if not df_state.empty and "year" in df_state.columns and "indicator" in df_state.columns:
        yearly_state = df_state.groupby(["year", "indicator"])["value"].sum().unstack(fill_value=0).reset_index()
        yearly_state = yearly_state.sort_values(by="year")
        rev_s = yearly_state.get("Revenue", pd.Series([0.0]*len(yearly_state)))
        exp_s = yearly_state.get("Expenditure", pd.Series([0.0]*len(yearly_state)))
        state_line_chart = {
            "years": yearly_state["year"].tolist(),
            "revenue": rev_s.round(2).tolist(),
            "expenditure": exp_s.round(2).tolist(),
            "deficit": (rev_s - exp_s).round(2).tolist()
        }
    else:
        state_line_chart = {
            "years": [],
            "revenue": [],
            "expenditure": [],
            "deficit": []
        }

    # Visual 3: Bar chart - National Sector Allocation by Sector sorted descending with Sector Share %
    if not df_nat_filt.empty and "sector" in df_nat_filt.columns and "allocation" in df_nat_filt.columns:
        sector_agg = df_nat_filt.groupby("sector")["allocation"].sum().reset_index()
        sector_agg = sector_agg.sort_values(by="allocation", ascending=False)
        total_alloc = sector_agg["allocation"].sum()
        sector_agg["share_pct"] = (sector_agg["allocation"] / total_alloc * 100).round(2) if total_alloc > 0 else 0.0

        national_bar_chart = {
            "sectors": sector_agg["sector"].tolist(),
            "allocation": sector_agg["allocation"].round(2).tolist(),
            "share_pct": sector_agg["share_pct"].tolist() if isinstance(sector_agg["share_pct"], pd.Series) else [0.0] * len(sector_agg)
        }
    else:
        national_bar_chart = {
            "sectors": [],
            "allocation": [],
            "share_pct": []
        }

    avg_def_pct = round(sum(deficit_chart_pcts) / len(deficit_chart_pcts), 2) if deficit_chart_pcts else 3.28
    compliance_rate = round((compliant_count / len(states) * 100), 1) if states else 60.0

    return {
        "kpis": {
            "total_state_revenue": tot_rev,
            "total_state_expenditure": tot_exp,
            "fiscal_deficit": tot_deficit,
            "avg_fiscal_deficit_pct": avg_def_pct,
            "debt_to_revenue_pct": round(debt_to_rev, 2),
            "total_national_allocation": tot_national_alloc,
            "total_national_expenditure": tot_national_exp,
            "frbm_compliance_rate_pct": compliance_rate
        },
        "state_map_data": state_map_data,
        "state_deficit_chart": state_deficit_chart,
        "state_rev_exp_bar": state_rev_exp_bar,
        "state_line_chart": state_line_chart,
        "national_bar_chart": national_bar_chart
    }

# ==========================================
# 5. PREDICTIVE ANALYTICS & WHAT-IF ENGINE (PAGE 5)
# ==========================================
def get_predictive_analytics(whatif_ind_cut_pct=0, whatif_org_growth_pct=0, whatif_state_deficit_target_pct=0):
    conn = get_db_connection()
    df_ind = pd.read_sql_query("SELECT date, amount, income_expense FROM individual_transactions WHERE income_expense = 'Expense'", conn)
    df_org = pd.read_sql_query("SELECT order_date, sales FROM org_orders", conn)
    df_state = pd.read_sql_query("SELECT year, indicator, value FROM state_finance WHERE indicator = 'Expenditure'", conn)
    conn.close()

    # --- 1. Individual Monthly Expense Forecast (6 Periods Ahead) ---
    if not df_ind.empty and "date" in df_ind.columns and "amount" in df_ind.columns:
        df_ind["Date"] = pd.to_datetime(df_ind["date"])
        monthly_ind = df_ind.groupby(df_ind["Date"].dt.strftime("%Y-%m"))["amount"].sum().reset_index()
        monthly_ind = monthly_ind.sort_values(by="Date")
        hist_ind_labels = [datetime.strptime(d, "%Y-%m").strftime("%b %y") for d in monthly_ind["Date"]]
        hist_ind_values = monthly_ind["amount"].tolist()
    else:
        hist_ind_labels = []
        hist_ind_values = []

    future_ind_labels = ["Jan 25", "Feb 25", "Mar 25", "Apr 25", "May 25", "Jun 25"]
    future_ind_forecast = []
    future_ind_upper = []
    future_ind_lower = []

    if hist_ind_values:
        alpha = 0.35
        smoothed = [hist_ind_values[0]]
        for val in hist_ind_values[1:]:
            smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])

        last_val = smoothed[-1]
        trend = (smoothed[-1] - smoothed[-4]) / 4.0 if len(smoothed) >= 4 else 0.0
        cut_factor = 1.0 - (float(whatif_ind_cut_pct) / 100.0)
        std_error = float(np.std(hist_ind_values[-12:])) if len(hist_ind_values) >= 12 else 5000.0

        for i in range(1, 7):
            base_pred = (last_val + trend * i) * cut_factor
            margin = 1.96 * std_error * np.sqrt(i * 0.3) # 95% Confidence Band
            future_ind_forecast.append(round(base_pred, 2))
            future_ind_upper.append(round(base_pred + margin, 2))
            future_ind_lower.append(round(max(0, base_pred - margin), 2))
    else:
        future_ind_forecast = [0.0] * 6
        future_ind_upper = [0.0] * 6
        future_ind_lower = [0.0] * 6

    ind_forecast_data = {
        "history_labels": hist_ind_labels[-12:],
        "history_values": [round(v, 2) for v in hist_ind_values[-12:]],
        "forecast_labels": future_ind_labels,
        "forecast_values": future_ind_forecast,
        "upper_bound": future_ind_upper,
        "lower_bound": future_ind_lower,
        "projected_next_month": future_ind_forecast[0]
    }

    # --- 2. Organization Quarterly Revenue Forecast (4 Periods Ahead) ---
    if not df_org.empty and "order_date" in df_org.columns and "sales" in df_org.columns:
        df_org["OrderDate"] = pd.to_datetime(df_org["order_date"])
        df_org["YQ"] = df_org["OrderDate"].dt.year.astype(str) + "-Q" + df_org["OrderDate"].dt.quarter.astype(str)
        quarterly_org = df_org.groupby("YQ")["sales"].sum().reset_index().sort_values(by="YQ")
        hist_org_labels = quarterly_org["YQ"].tolist()
        hist_org_values = quarterly_org["sales"].tolist()
    else:
        hist_org_labels = []
        hist_org_values = []

    org_growth_slider = float(whatif_org_growth_pct) / 100.0
    future_org_labels = ["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4"]
    future_org_forecast = []
    future_org_upper = []
    future_org_lower = []

    if hist_org_values:
        last_org = hist_org_values[-1]
        avg_org_growth = 0.035 + (org_growth_slider / 4.0)
        org_std = float(np.std(hist_org_values)) if len(hist_org_values) > 0 else 10000.0
        cur_org = last_org
        for i in range(1, 5):
            cur_org = cur_org * (1 + avg_org_growth)
            margin = 1.96 * org_std * np.sqrt(i * 0.4)
            future_org_forecast.append(round(cur_org, 2))
            future_org_upper.append(round(cur_org + margin, 2))
            future_org_lower.append(round(max(0, cur_org - margin), 2))
    else:
        last_org = 0.0
        future_org_forecast = [0.0] * 4
        future_org_upper = [0.0] * 4
        future_org_lower = [0.0] * 4

    org_forecast_data = {
        "history_labels": hist_org_labels[-8:],
        "history_values": [round(v, 2) for v in hist_org_values[-8:]],
        "forecast_labels": future_org_labels,
        "forecast_values": future_org_forecast,
        "upper_bound": future_org_upper,
        "lower_bound": future_org_lower,
        "projected_next_quarter": future_org_forecast[0]
    }

    # --- 3. State Public Expenditure Forecast (3 Years Ahead) ---
    if not df_state.empty and "year" in df_state.columns and "value" in df_state.columns:
        yearly_state = df_state.groupby("year")["value"].sum().reset_index().sort_values(by="year")
        hist_state_labels = [str(y) for y in yearly_state["year"]]
        hist_state_values = yearly_state["value"].tolist()
    else:
        hist_state_labels = []
        hist_state_values = []

    future_state_labels = ["2025", "2026", "2027"]
    future_state_forecast = []
    future_state_upper = []
    future_state_lower = []

    if hist_state_values:
        state_growth = 0.075 - (float(whatif_state_deficit_target_pct) / 100.0 * 0.02)
        last_state = hist_state_values[-1]
        state_std = float(np.std(hist_state_values)) if len(hist_state_values) > 0 else 50000.0
        cur_state = last_state
        for i in range(1, 4):
            cur_state = cur_state * (1 + state_growth)
            margin = 1.96 * state_std * np.sqrt(i * 0.5)
            future_state_forecast.append(round(cur_state, 2))
            future_state_upper.append(round(cur_state + margin, 2))
            future_state_lower.append(round(max(0, cur_state - margin), 2))
    else:
        last_state = 0.0
        future_state_forecast = [0.0] * 3
        future_state_upper = [0.0] * 3
        future_state_lower = [0.0] * 3

    state_forecast_data = {
        "history_labels": hist_state_labels[-6:],
        "history_values": [round(v, 2) for v in hist_state_values[-6:]],
        "forecast_labels": future_state_labels,
        "forecast_values": future_state_forecast,
        "upper_bound": future_state_upper,
        "lower_bound": future_state_lower,
        "projected_next_year": future_state_forecast[0]
    }

    # Executive Decision-Making Analytical Interpretation
    if hist_ind_values or hist_org_values or hist_state_values:
        savings_impact = round(future_ind_forecast[0] * (float(whatif_ind_cut_pct) / 100.0), 2)
        org_boost = round(future_org_forecast[0] - (last_org * 1.035), 2)

        decision_insights = (
            f"• Micro/Individual: A {whatif_ind_cut_pct}% discretionary spending adjustment conserves approx "
            f"₹{savings_impact:,.0f} per month, directly raising annual savings liquidity. \n"
            f"• Enterprise/Org: Target revenue growth of {whatif_org_growth_pct}% projects Q1 2025 revenue at "
            f"₹{future_org_forecast[0]:,.0f}, offsetting projected departmental logistics costs. \n"
            f"• Macro/State: Constraining expenditure inflation keeps projected 2025 public outlay within "
            f"₹{future_state_forecast[0]:,.0f}, narrowing the state debt servicing ratio."
        )
    else:
        decision_insights = (
            "• Micro/Individual: Ready for custom budget inputs. Use the Individual studio or add your personal dataset.\n"
            "• Enterprise/Org: Ready for departmental simulation. Use Organization studio or add your company orders dataset.\n"
            "• Macro/State: Ready for public finance data. Add your state finance records to view projections."
        )

    return {
        "individual_forecast": ind_forecast_data,
        "organization_forecast": org_forecast_data,
        "state_forecast": state_forecast_data,
        "decision_insights": decision_insights,
        "parameters": {
            "whatif_ind_cut_pct": whatif_ind_cut_pct,
            "whatif_org_growth_pct": whatif_org_growth_pct,
            "whatif_state_deficit_target_pct": whatif_state_deficit_target_pct
        }
    }

# ==========================================
# 6. INTERACTIVE USER-INPUT CALCULATION ENGINES
# ==========================================
def calculate_custom_individual(input_data):
    """
    Accepts user inputs for Individual Mode:
    - monthly_income, other_income
    - category breakdown: { category: { actual: X, budget: Y } }
    Produces all relevant metrics, financial health score, and chart structures.
    """
    monthly_income = float(input_data.get("monthly_income", 0))
    other_income = float(input_data.get("other_income", 0))
    total_income = monthly_income + other_income

    categories = input_data.get("categories", {})
    if not categories:
        # Default fallback categories if empty
        categories = {
            "Food & Dining": {"actual": 16000, "budget": 16000},
            "Groceries": {"actual": 18000, "budget": 18000},
            "Housing & Rent": {"actual": 25000, "budget": 25000},
            "Utilities": {"actual": 6500, "budget": 6500},
            "Transportation": {"actual": 8500, "budget": 9000},
            "Entertainment": {"actual": 6500, "budget": 7000},
            "Healthcare": {"actual": 4500, "budget": 6000},
            "Education": {"actual": 3500, "budget": 5000},
            "Shopping": {"actual": 11000, "budget": 11000},
            "Personal Care": {"actual": 4000, "budget": 4500}
        }

    cat_labels = []
    cat_actuals = []
    cat_budgets = []
    cat_variances = []
    cat_colors = []
    cat_flags = []
    cat_breakdown = []

    total_expense = 0.0
    total_planned_budget = 0.0
    within_budget_count = 0

    for cat_name, vals in categories.items():
        actual = float(vals.get("actual", 0))
        budget = float(vals.get("budget", 0))
        variance = round(budget - actual, 2)
        total_expense += actual
        total_planned_budget += budget

        is_under = variance >= 0
        if is_under:
            within_budget_count += 1
            cat_colors.append("#2E7D74") # Teal
            cat_flags.append("Within Budget")
        else:
            cat_colors.append("#DC2626") # Red
            cat_flags.append("Over Budget")

        cat_labels.append(cat_name)
        cat_actuals.append(round(actual, 2))
        cat_budgets.append(round(budget, 2))
        cat_variances.append(variance)

        cat_breakdown.append({
            "category": cat_name,
            "actual": round(actual, 2),
            "budget": round(budget, 2),
            "variance": variance,
            "status": "Within Budget" if is_under else "Over Budget",
            "percent_spent": round((actual / budget * 100), 1) if budget > 0 else 0
        })

    net_savings = round(total_income - total_expense, 2)
    savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0
    budget_variance = round(total_planned_budget - total_expense, 2)
    budget_utilization = round((total_expense / total_planned_budget * 100), 1) if total_planned_budget > 0 else 0.0
    overspend_flag = "Over Budget" if total_expense > total_planned_budget else "Within Budget"

    # Financial Health Score (0 to 100)
    # 40 points for savings rate (target 20%+)
    savings_score = min(40, max(0, (savings_rate / 25.0) * 40))
    # 40 points for category budget discipline
    total_cats = max(1, len(categories))
    discipline_score = (within_budget_count / total_cats) * 40
    # 20 points for total utilization <= 100%
    util_score = 20 if budget_utilization <= 100 else max(0, 20 - (budget_utilization - 100))
    health_score = int(round(savings_score + discipline_score + util_score))

    health_rating = "Excellent" if health_score >= 80 else ("Good" if health_score >= 65 else ("Fair" if health_score >= 50 else "Needs Attention"))

    # Visual 1: Donut Chart - Category Spending Distribution
    donut_chart = {
        "labels": cat_labels,
        "data": cat_actuals
    }

    # Visual 2: Variance Bar Chart
    bar_chart = {
        "categories": cat_labels,
        "variance": cat_variances,
        "colors": cat_colors,
        "flags": cat_flags
    }

    # Visual 3: 12-Month Simulated Trend Line vs Budget Limit
    months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    monthly_trend = []
    # Baseline with small realistic seasonal variation
    np.random.seed(int(total_expense) % 1000)
    for m_idx in range(12):
        variation = 1.0 + float(np.sin(m_idx * 0.5) * 0.06)
        monthly_trend.append(round(total_expense * variation, 2))

    trend_line = {
        "labels": months,
        "actual_expense": monthly_trend,
        "planned_budget": [round(total_planned_budget, 2)] * 12
    }

    return {
        "kpis": {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "savings_rate_pct": savings_rate,
            "total_planned_budget": total_planned_budget,
            "budget_variance": budget_variance,
            "budget_utilization_pct": budget_utilization,
            "overspend_flag": overspend_flag,
            "health_score": health_score,
            "health_rating": health_rating
        },
        "donut_chart": donut_chart,
        "bar_chart": bar_chart,
        "trend_line": trend_line,
        "cat_breakdown": cat_breakdown,
        "monthly_income": monthly_income,
        "other_income": other_income
    }


def calculate_custom_organization(input_data):
    """
    Accepts user inputs for Organization Mode:
    - company_name, fiscal_year
    - departments: { dept_name: { revenue: X, cost: Y } }
    - category_breakdown: { category: { sales: X, profit: Y } }
    - regional_breakdown: { region: { cat: val } }
    Produces all relevant enterprise KPIs, margins, and visualizations.
    """
    company_name = input_data.get("company_name", "Enterprise Corp")
    fiscal_year = int(input_data.get("fiscal_year", 2024))
    departments = input_data.get("departments", {})

    if not departments:
        departments = {
            "Corporate": {"revenue": 145000000, "cost": 108000000},
            "Consumer": {"revenue": 82000000, "cost": 61000000},
            "Home Office": {"revenue": 46000000, "cost": 36000000}
        }

    dept_names = []
    dept_revenues = []
    dept_costs = []
    dept_profits = []
    dept_margins = []
    dept_variances = []

    total_revenue = 0.0
    total_cost = 0.0
    top_dept = ""
    top_dept_cost = -1.0

    for d_name, vals in departments.items():
        rev = float(vals.get("revenue", 0))
        c = float(vals.get("cost", 0))
        profit = round(rev - c, 2)
        variance = round(rev - c, 2)
        margin = round((profit / rev * 100), 1) if rev > 0 else 0.0

        dept_names.append(d_name)
        dept_revenues.append(round(rev, 2))
        dept_costs.append(round(c, 2))
        dept_profits.append(profit)
        dept_margins.append(margin)
        dept_variances.append(variance)

        total_revenue += rev
        total_cost += c

        if c > top_dept_cost:
            top_dept_cost = c
            top_dept = d_name

    total_profit = round(total_revenue - total_cost, 2)
    profit_margin = round((total_profit / total_revenue * 100), 1) if total_revenue > 0 else 0.0
    budget_variance = round(total_revenue - total_cost, 2)
    budget_utilization = round((total_cost / total_revenue * 100), 1) if total_revenue > 0 else 0.0

    # Visual 1: Clustered Bar - Revenue vs Cost by Department
    clustered_bar = {
        "departments": dept_names,
        "revenue": dept_revenues,
        "cost": dept_costs
    }

    # Visual 2: Category Breakdown / Treemap
    category_breakdown = input_data.get("category_breakdown", {})
    if not category_breakdown:
        category_breakdown = {
            "Technology": {"sales": round(total_revenue * 0.48, 2), "profit": round(total_profit * 0.52, 2)},
            "Furniture": {"sales": round(total_revenue * 0.32, 2), "profit": round(total_profit * 0.28, 2)},
            "Office Supplies": {"sales": round(total_revenue * 0.20, 2), "profit": round(total_profit * 0.20, 2)}
        }

    treemap_data = []
    for cat_name, cat_vals in category_breakdown.items():
        treemap_data.append({
            "name": cat_name,
            "value": round(float(cat_vals.get("profit", 0)), 2),
            "sales": round(float(cat_vals.get("sales", 0)), 2),
            "children": [
                {"name": f"{cat_name} Core", "value": round(float(cat_vals.get("profit", 0)) * 0.6, 2)},
                {"name": f"{cat_name} Enterprise", "value": round(float(cat_vals.get("profit", 0)) * 0.4, 2)}
            ]
        })

    # Visual 3: Quarterly Growth Line Chart
    q_labels = [f"{fiscal_year}-Q1", f"{fiscal_year}-Q2", f"{fiscal_year}-Q3", f"{fiscal_year}-Q4"]
    q_weights = [0.22, 0.24, 0.26, 0.28]
    q_sales = [round(total_revenue * w, 2) for w in q_weights]
    q_growth = [0.0]
    for i in range(1, 4):
        prev = q_sales[i - 1]
        g = round(((q_sales[i] - prev) / prev * 100), 2) if prev > 0 else 0.0
        q_growth.append(g)

    quarterly_growth = {
        "labels": q_labels,
        "growth_pct": q_growth,
        "sales": q_sales
    }

    # Visual 4: Region × Category Matrix Visual
    regions = ["North", "South", "West", "East"]
    cats = list(category_breakdown.keys())
    reg_weights = [0.30, 0.35, 0.20, 0.15]
    matrix_values = []

    for r_idx, reg in enumerate(regions):
        row_vals = []
        for c_name in cats:
            c_profit = float(category_breakdown[c_name].get("profit", 0))
            val = round(c_profit * reg_weights[r_idx] * (0.95 + (r_idx * 0.03)), 2)
            row_vals.append(val)
        matrix_values.append(row_vals)

    matrix = {
        "regions": regions,
        "categories": cats,
        "values": matrix_values
    }

    return {
        "company_name": company_name,
        "fiscal_year": fiscal_year,
        "kpis": {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "profit_margin_pct": profit_margin,
            "budget_variance": budget_variance,
            "budget_utilization_pct": budget_utilization,
            "top_department": top_dept,
            "top_department_cost": top_dept_cost
        },
        "clustered_bar": clustered_bar,
        "treemap": treemap_data,
        "quarterly_growth": quarterly_growth,
        "matrix": matrix,
        "departments_summary": [
            {
                "department": dept_names[i],
                "revenue": dept_revenues[i],
                "cost": dept_costs[i],
                "profit": dept_profits[i],
                "margin_pct": dept_margins[i]
            }
            for i in range(len(dept_names))
        ]
    }

