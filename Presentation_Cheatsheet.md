# MULTI-LEVEL BUDGET TRACKER ANALYTICS
## Viva & Faculty Presentation Cheatsheet

### 1. Key Questions Faculty Ask & Exact Answers

**Q1: Why did you choose Power BI over standard Python (Matplotlib/Seaborn) or Web dashboards alone?**
> **Answer**: "Power BI unifies the complete analytics lifecycle into a single enterprise-grade platform: (1) automated ETL and shape transformations via Power Query M-code, (2) scalable multi-table star schema relational modeling, (3) real-time calculation engines using context-aware DAX measures, and (4) built-in time-series exponential smoothing without external ML script dependencies. To complement this, we also built a complete full-stack web application allowing live data entry and dynamic synchronization."

**Q2: What is your Data Modeling strategy?**
> **Answer**: "We implemented a Star Schema centered around a shared, marked Date Dimension table (`DateTable`). It connects via 1-to-Many single-direction relationships to `Individual[Date]`, `Organization[Order Date]`, `State[Year]`, and `National[Year]`. The three fact tables remain mutually independent to prevent ambiguous cross-filtering and circular dependencies. We also created a disconnected `LevelTable` to power cross-level SWITCH DAX measures."

**Q3: How did you calculate Budget vs Actual when the raw Kaggle dataset had no target budget column?**
> **Answer**: "The raw Kaggle personal transactions only contained actual expenses. In Power Query, we engineered a planned monthly budget mapping column (`MonthlyBudget`) by establishing category-specific benchmark targets based on historical spending averages (e.g., ₹32,000 for Food, ₹28,000 for Housing, etc.). This enabled calculation of `Budget Variance` and `Budget Utilization %` via DAX."

**Q4: How does your Predictive Analytics work?**
> **Answer**: "Power BI's native forecasting engine uses Holt-Winters Exponential Smoothing. It evaluates seasonal cycles, trend slope, and damping factors, generating forecasts across future periods with a 95% confidence interval shaded band. In our web application backend, we mirrored this using exponential moving average and auto-regressive projection."

**Q5: What are the three levels of your project?**
> **Answer**:
> 1. **Individual Level**: Micro-financial hygiene (Income vs. Expense, category breakdown, savings rate, overspend detection).
> 2. **Organization Level**: Meso-economic cost centers (Superstore data treated as Corporate/Consumer/Home Office departments, procurement cost vs. revenue, regional variances).
> 3. **State / Nation Level**: Macro-public finance (State revenues, expenditures, fiscal deficits, debt-to-revenue ratios, and national union ministry budget allocations).

---

### 2. Live Demo Checklist for Faculty
- [ ] Show the **Executive Overview** page: Point out the 6 KPI cards with conditional green/red formatting.
- [ ] Interact with the **Year** and **Level** slicers to show dynamic cross-filtering.
- [ ] Navigate to **Individual Analytics**: Show the Donut chart and the Overspend Flag bar chart.
- [ ] Navigate to **Organization Analytics**: Show the Treemap drill-down from Category to Sub-Category, and the Region x Category Matrix.
- [ ] Navigate to **State / Nation Analytics**: Point out the Indian State Map and Sector Allocation bar chart.
- [ ] Navigate to **Predictive Analytics**: Explain the 95% confidence bounds on the forecast charts.
- [ ] Open the **Web Application**: Add a live transaction or order, show the instant recalculation, and show how the updated data exports directly to Power BI!
