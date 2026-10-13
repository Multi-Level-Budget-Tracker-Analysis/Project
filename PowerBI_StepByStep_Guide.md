# MULTI-LEVEL BUDGET TRACKER ANALYTICS
## Complete Power BI Build Guide & Lab Project Manual
**Data Visualization Lab Project — NIE Mysuru**

---

### Table of Contents
1. [Overview & Project Architecture](#1-overview--project-architecture)
2. [Data Source Inventory & Setup](#2-data-source-inventory--setup)
3. [Step-by-Step Power Query ETL Pipeline](#3-step-by-step-power-query-etl-pipeline)
4. [Data Modeling & Star Schema Setup](#4-data-modeling--star-schema-setup)
5. [DAX Measures Library & Implementation](#5-dax-measures-library--implementation)
6. [Page-by-Page Dashboard Construction](#6-page-by-page-dashboard-construction)
7. [Time-Series Forecasting & Predictive Analytics](#7-time-series-forecasting--predictive-analytics)
8. [Faculty Defense & Viva Cheatsheet](#8-faculty-defense--viva-cheatsheet)

---

### 1. Overview & Project Architecture
This project implements a multi-tier financial analytics system structured across three hierarchical levels of economy:
- **Tier 1: Individual / Micro-Budget**: Tracking household income, day-to-day expenditures, category budget limits, budget variance, and personal savings rate.
- **Tier 2: Enterprise / Mesoeconomic**: Organization-level financial performance analyzing departmental budgets (Consumer, Corporate, Home Office), procurement costs, sales revenue, and regional budget variances.
- **Tier 3: Macro / State & National**: Public finance tracking state-level revenues, expenditures, fiscal deficits, debt-to-revenue ratios, and national central sector allocations.

---

### 2. Data Source Inventory & Setup
All datasets are located in `BudgetTrackerAnalytics/`:
- **`01_RawData/individual_transactions.csv`**: Daily personal financial ledger (`Date`, `Mode`, `Category`, `Subcategory`, `Note`, `Amount`, `Income/Expense`, `Currency`).
- **`01_RawData/org_superstore.csv`**: Enterprise orders and cost analysis (`Order ID`, `Order Date`, `Ship Date`, `Ship Mode`, `Segment`, `City`, `State`, `Region`, `Category`, `Sub-Category`, `Product Name`, `Sales`, `Quantity`, `Discount`, `Profit`).
- **`01_RawData/state_finance_india.csv`**: Unpivoted longitudinal state public finance data (`State`, `Year`, `Indicator`, `Value`).
- **`01_RawData/national_union_budget.csv`**: Central ministry budget allocations & expenditures (`Ministry`, `Sector`, `Year`, `Allocation`, `Expenditure`).
- **`02_CleanData/DateTable.csv`**: Universal date dimension table (2014-2025).

---

### 3. Step-by-Step Power Query ETL Pipeline
1. Launch **Power BI Desktop**.
2. Click **Home -> Get Data -> Text/CSV**, browse to `d:\Multi level budget\BudgetTrackerAnalytics\01_RawData`.
3. Select `individual_transactions.csv` and click **Transform Data**.
4. Repeat for `org_superstore.csv`, `state_finance_india.csv`, and `national_union_budget.csv`.
5. Apply the Power Query transformations (copy directly from `03_PowerBI/PowerQuery_M_Cleaning.pq` using the **Advanced Editor**):
   - **Individual**: Set column types, generate `MonthYear`, add `MonthlyBudget` target mapping, and remove blank records.
   - **Organization**: Rename `Segment` to `Department`, calculate `Cost = [Sales] - [Profit]`, calculate `BudgetVariance = [Sales] - [Cost]`.
   - **State**: Ensure long format (`State`, `Year`, `Indicator`, `Value`) with `Year` as Integer and `Value` as Decimal.
   - **National**: Set `Allocation` and `Expenditure` as Decimals.
6. Click **Home -> Close & Apply**.

---

### 4. Data Modeling & Star Schema Setup
1. Switch to the **Model View** (left sidebar icon).
2. Create the Date dimension table:
   - Click **Modeling -> New Table**
   - DAX formula:
     ```dax
     DateTable = 
     ADDCOLUMNS(
         CALENDAR(DATE(2014, 1, 1), DATE(2025, 12, 31)),
         "Year", YEAR([Date]),
         "MonthName", FORMAT([Date], "MMM"),
         "MonthNum", MONTH([Date]),
         "Quarter", "Q" & FORMAT([Date], "Q"),
         "MonthYear", FORMAT([Date], "MMM yyyy")
     )
     ```
   - Click **Modeling -> Mark as Date Table** and select `DateTable[Date]`.
3. Establish relationships:
   - `DateTable[Date]` (1) ─── 1:M ───> `Individual[Date]` (*)
   - `DateTable[Date]` (1) ─── 1:M ───> `Organization[Order Date]` (*)
   - `DateTable[Year]` (1) ─── 1:M ───> `State[Year]` (*)
   - `DateTable[Year]` (1) ─── 1:M ───> `National[Year]` (*)
4. Create the disconnected `LevelTable` for cross-level comparison slicer:
   - **Modeling -> New Table**:
     ```dax
     LevelTable = 
     DATATABLE(
         "Level", STRING,
         "LevelOrder", INTEGER,
         {
             {"Individual", 1},
             {"Organization", 2},
             {"State", 3}
         }
     )
     ```

---

### 5. DAX Measures Library & Implementation
Create a dedicated measures container:
1. **Modeling -> New Table**: `_Measures = ROW("x", 1)`
2. Hide column `x`.
3. Enter the DAX formulas from `DAX_Measures_Library.dax`:
   - Individual: `Total Income`, `Total Expense`, `Net Savings`, `Savings Rate %`, `Total Planned Budget`, `Budget Variance (Ind)`, `Budget Utilization % (Ind)`, `Overspend Flag`.
   - Organization: `Total Revenue (Org)`, `Total Cost (Org)`, `Total Profit (Org)`, `Budget Variance (Org)`, `Budget Utilization % (Org)`, `Revenue Growth %`, `Top Department by Cost`.
   - State / Nation: `Total State Revenue`, `Total State Expenditure`, `Fiscal Deficit`, `Debt to Revenue %`, `National Sector Allocation`, `Sector Share %`.
   - Dynamic Cross-Level: `Selected Utilization %`.

---

### 6. Page-by-Page Dashboard Construction

#### Import Custom Theme
- Navigate to **View -> Themes -> Browse for themes**, select `03_PowerBI/navy_amber_teal_theme.json`.

#### Page 1: Executive Overview
- **6 KPI Cards**:
  1. `Total Income (Ind)`
  2. `Total Revenue (Org)`
  3. `Total State Revenue`
  4. `Net Savings` (Conditional formatting: Font green if > 0, red if < 0)
  5. `Total Profit (Org)` (Conditional formatting: Green if positive)
  6. `Fiscal Deficit` (Conditional formatting: Red if negative)
- **Top Slicers**: Slicer on `DateTable[Year]` and Slicer on `LevelTable[Level]`.
- **Combo Chart**: Normalized revenue/income vs cost/expenditure over time.

#### Page 2: Individual Analytics
- **Donut Chart**: Legend = `Individual[Category]`, Values = `[Total Expense]`.
- **Line Chart**: X-axis = `DateTable[MonthYear]`, Y-axis = `[Total Expense]` and `[Total Planned Budget]`.
- **Bar Chart**: Y-axis = `Individual[Category]`, X-axis = `[Budget Variance (Ind)]`, Data Colors = Field Value based on `[Overspend Flag]`.
- **KPI Cards**: `[Savings Rate %]` and `[Budget Utilization % (Ind)]`.
- **Interactive Data Table**: Columns = `Date`, `Category`, `Subcategory`, `Amount`, `Mode` with a search filter on `Category`.

#### Page 3: Organization Analytics
- **Clustered Bar Chart**: Y-axis = `Organization[Department]`, X-axis = `[Total Revenue (Org)]` and `[Total Cost (Org)]`.
- **Treemap Visual**: Category = `Organization[Category]`, Details = `Organization[Sub-Category]`, Values = `[Total Profit (Org)]`.
- **Line Chart**: X-axis = `DateTable[Quarter]`, Y-axis = `[Revenue Growth %]`.
- **Matrix Visual**: Rows = `Organization[Region]`, Columns = `Organization[Category]`, Values = `[Budget Variance (Org)]`.
- **Card**: `[Top Department by Cost]`.

#### Page 4: State / Nation Analytics
- **Filled Map / Shape Map**: Location = `State[State]`, Color saturation = `[Fiscal Deficit]` or `[Total State Expenditure]`.
- **Line Chart**: X-axis = `State[Year]`, Lines = `[Total State Revenue]` and `[Total State Expenditure]`.
- **Bar Chart**: Y-axis = `National[Sector]`, X-axis = `[National Sector Allocation]`, Data Labels = `[Sector Share %]`.
- **KPI Card**: `[Debt to Revenue %]`.

#### Page 5: Predictive Analytics
- **3 Side-by-Side Line Charts**:
  1. Personal Monthly Expense Over Time.
  2. Organization Quarterly Revenue Over Time.
  3. State Longitudinal Expenditure Over Time.
- **Enabling Power BI Forecast**:
  - Select each chart -> Go to the **Analytics Pane** (magnifying glass icon).
  - Expand **Forecast** -> Click **+ Add**.
  - Set **Forecast length** = 6 periods, **Confidence interval** = 95%.
  - Power BI fits Holt-Winters exponential smoothing automatically.
- **KPI Projection Cards & Decision Takeaway Notes**:
  - Summary commentary explaining the decision implications of projected deficits and cost trends.

---

### 7. Time-Series Forecasting & Predictive Analytics
- **Methodology**: Multiplicative/Additive Holt-Winters Exponential Smoothing.
- **Confidence Intervals**: 95% upper and lower prediction bounds.
- **What-If Analysis**: Sensitivity analysis on spending cuts, savings rates, and organizational profit margins.

---

### 8. Faculty Defense & Viva Cheatsheet
Refer to `Presentation_Cheatsheet.md` for answers to common questions regarding:
- Why star schema was used over snowflake.
- How disconnected tables enable dynamic SWITCH measures without circular dependencies.
- How missing monthly budget columns were handled via calculated dimension targets.
