// ==============================================================================
// MULTI-LEVEL BUDGET TRACKER ANALYTICS — POWER QUERY M CLEANING CODE
// Data Visualization Lab Project — NIE Mysuru
// ==============================================================================
// Copy and paste each block into Power Query -> Advanced Editor for each query.
// ==============================================================================

// ------------------------------------------------------------------------------
// QUERY 1: Individual
// Source: 01_RawData/individual_transactions.csv
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("D:\Multi level budget\BudgetTrackerAnalytics\01_RawData\individual_transactions.csv"),[Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"Date", type date}, 
        {"Mode", type text}, 
        {"Category", type text}, 
        {"Subcategory", type text}, 
        {"Note", type text}, 
        {"Amount", type number}, 
        {"Income/Expense", type text}, 
        {"Currency", type text}
    }),
    #"Removed Blank Rows" = Table.SelectRows(#"Changed Type", each not List.IsEmpty(List.RemoveMatchingItems(Record.FieldValues(_), {"", null}))),
    #"Added MonthYear" = Table.AddColumn(#"Removed Blank Rows", "MonthYear", each Date.ToText([Date], "MMM yyyy"), type text),
    // Budget mapping target per category
    #"Added MonthlyBudget" = Table.AddColumn(#"Added MonthYear", "MonthlyBudget", each 
        if [Category] = "Food & Dining" then 32000
        else if [Category] = "Groceries" then 24000
        else if [Category] = "Housing & Rent" then 28000
        else if [Category] = "Utilities" then 8000
        else if [Category] = "Transportation" then 12000
        else if [Category] = "Entertainment" then 9000
        else if [Category] = "Healthcare" then 7500
        else if [Category] = "Education" then 8500
        else if [Category] = "Shopping" then 15000
        else if [Category] = "Personal Care" then 6000
        else 0, type number
    )
in
    #"Added MonthlyBudget"


// ------------------------------------------------------------------------------
// QUERY 2: Organization
// Source: 01_RawData/org_superstore.csv
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("D:\Multi level budget\BudgetTrackerAnalytics\01_RawData\org_superstore.csv"),[Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"Order ID", type text}, 
        {"Order Date", type date}, 
        {"Ship Date", type date}, 
        {"Ship Mode", type text}, 
        {"Segment", type text}, 
        {"City", type text}, 
        {"State", type text}, 
        {"Region", type text}, 
        {"Category", type text}, 
        {"Sub-Category", type text}, 
        {"Product Name", type text}, 
        {"Sales", type number}, 
        {"Quantity", Int64.Type}, 
        {"Discount", type number}, 
        {"Profit", type number}
    }),
    #"Renamed Columns" = Table.RenameColumns(#"Changed Type",{{"Segment", "Department"}}),
    #"Added Cost" = Table.AddColumn(#"Renamed Columns", "Cost", each [Sales] - [Profit], type number),
    #"Added BudgetVariance" = Table.AddColumn(#"Added Cost", "BudgetVariance", each [Sales] - [Cost], type number)
in
    #"Added BudgetVariance"


// ------------------------------------------------------------------------------
// QUERY 3: State
// Source: 01_RawData/state_finance_india.csv
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("D:\Multi level budget\BudgetTrackerAnalytics\01_RawData\state_finance_india.csv"),[Delimiter=",", Columns=4, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"State", type text}, 
        {"Year", Int64.Type}, 
        {"Indicator", type text}, 
        {"Value", type number}
    })
in
    #"Changed Type"


// ------------------------------------------------------------------------------
// QUERY 4: National
// Source: 01_RawData/national_union_budget.csv
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents("D:\Multi level budget\BudgetTrackerAnalytics\01_RawData\national_union_budget.csv"),[Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"Ministry", type text}, 
        {"Sector", type text}, 
        {"Year", Int64.Type}, 
        {"Allocation", type number}, 
        {"Expenditure", type number}
    })
in
    #"Changed Type"


// ------------------------------------------------------------------------------
// QUERY 5: DateTable (DAX Table)
// Modeling -> New Table
// ------------------------------------------------------------------------------
/*
DateTable = 
ADDCOLUMNS(
    CALENDAR(DATE(2014, 1, 1), DATE(2025, 12, 31)),
    "Year", YEAR([Date]),
    "MonthName", FORMAT([Date], "MMM"),
    "MonthNum", MONTH([Date]),
    "Quarter", "Q" & FORMAT([Date], "Q"),
    "MonthYear", FORMAT([Date], "MMM yyyy")
)
*/

// ------------------------------------------------------------------------------
// QUERY 6: LevelTable (Disconnected Table for Slicer)
// Modeling -> New Table
// ------------------------------------------------------------------------------
/*
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
*/
