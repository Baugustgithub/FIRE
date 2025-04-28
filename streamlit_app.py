import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# --- Tax Settings ---
FEDERAL_BRACKETS_2025 = [
    (0, 0.10),
    (11925, 0.12),
    (48475, 0.22),
    (103350, 0.24),
    (197300, 0.32),
    (250525, 0.35),
    (626350, 0.37),
]

VIRGINIA_BRACKETS_2025 = [
    (0, 0.02),
    (3000, 0.03),
    (5000, 0.05),
    (17000, 0.0575),
]

STANDARD_DEDUCTION_2025 = 15000

# --- Functions ---
def calculate_tax(taxable_income, brackets):
    tax = 0
    previous_limit = 0
    for limit, rate in brackets:
        if taxable_income > previous_limit:
            taxable_in_bracket = min(taxable_income, limit) - previous_limit
            tax += taxable_in_bracket * rate
            previous_limit = limit
        else:
            break
    return max(tax, 0)

# --- Streamlit App ---
st.set_page_config(page_title="🔥 FIRE Tax + FI Planner 2025", layout="wide")
st.title("🔥 FIRE Tax + FI Planner 2025 (Federal + Virginia) 🔥")

# --- Sidebar Inputs ---
st.sidebar.header("Income & Expenses")
gross_salary = st.sidebar.number_input("Gross Salary ($)", value=100000, step=1000)
pension_percent = st.sidebar.slider("Pension Contribution (% of Salary)", 0, 20, 5) / 100
annual_expenses = st.sidebar.number_input("Annual Expenses ($)", value=40000, step=1000)
current_investments = st.sidebar.number_input("Current Total Investment Value ($)", value=50000, step=1000)
expected_return = st.sidebar.number_input("Expected Annual Investment Growth Rate (%)", value=5.0, step=0.1) / 100
retirement_age = st.sidebar.number_input("Normal Retirement Age", value=58.5, step=0.5)

st.sidebar.header("Choose Accounts to Contribute To")
account_types = {
    "403(b) Traditional": st.sidebar.checkbox("403(b) Traditional"),
    "403(b) Roth": st.sidebar.checkbox("403(b) Roth"),
    "457(b) Traditional": st.sidebar.checkbox("457(b) Traditional"),
    "457(b) Roth": st.sidebar.checkbox("457(b) Roth"),
    "401(a) Employee": st.sidebar.checkbox("401(a) Employee Contribution"),
    "401(a) Employer": st.sidebar.checkbox("401(a) Employer Contribution"),
    "Solo 401(k) Employee": st.sidebar.checkbox("Solo 401(k) Employee Contribution"),
    "Solo 401(k) Employer": st.sidebar.checkbox("Solo 401(k) Employer Contribution"),
    "SEP IRA": st.sidebar.checkbox("SEP IRA"),
    "SIMPLE IRA": st.sidebar.checkbox("SIMPLE IRA"),
    "Traditional IRA": st.sidebar.checkbox("Traditional IRA"),
    "Roth IRA": st.sidebar.checkbox("Roth IRA"),
    "HSA": st.sidebar.checkbox("HSA"),
    "FSA": st.sidebar.checkbox("FSA"),
    "529 Plan": st.sidebar.checkbox("529 Plan"),
    "ESA": st.sidebar.checkbox("ESA"),
    "Taxable Brokerage Account": st.sidebar.checkbox("Taxable Brokerage Savings"),
}

st.sidebar.header("Annual Contributions ($/year)")
contributions = {}
for account, enabled in account_types.items():
    if enabled:
        contributions[account] = st.sidebar.number_input(f"{account} Contribution ($)", value=0, step=500)

# --- Main Calculations ---
if st.sidebar.button("🚀 Run FIRE Simulation"):
    
    pension_contribution = gross_salary * pension_percent
    
    # Reduce AGI by pension + traditional pre-tax contributions
    agi = gross_salary - pension_contribution
    agi_reducing_accounts = [
        "403(b) Traditional", "457(b) Traditional", 
        "401(a) Employee", "Solo 401(k) Employee",
        "SEP IRA", "SIMPLE IRA", "Traditional IRA",
        "HSA", "FSA"
    ]
    
    for account in agi_reducing_accounts:
        agi -= contributions.get(account, 0)
    
    # Virginia 529 Plan deduction (up to $4000)
    va_529_deduction = min(contributions.get("529 Plan", 0), 4000)
    agi -= va_529_deduction
    
    taxable_income = max(agi - STANDARD_DEDUCTION_2025, 0)
    
    federal_tax = calculate_tax(taxable_income, FEDERAL_BRACKETS_2025)
    state_tax = calculate_tax(taxable_income, VIRGINIA_BRACKETS_2025)
    total_tax = federal_tax + state_tax
    
    # Calculate effective tax rate based on gross salary
    effective_tax_rate = total_tax / gross_salary if gross_salary > 0 else 0
    
    # Fix after-tax income calculation
    after_tax_income = gross_salary - pension_contribution - total_tax
    
    # Total Contributions
    total_savings = sum(contributions.values())
    savings_rate = total_savings / gross_salary if gross_salary > 0 else 0
    
    # Calculate disposable income (after taxes and post-tax savings)
    post_tax_savings = total_savings - sum(contributions.get(account, 0) for account in agi_reducing_accounts) - va_529_deduction
    disposable_income = after_tax_income - post_tax_savings
    
    # --- FIRE Financial Summary ---
    st.subheader("📋 FIRE Financial Summary")
    fire_summary = pd.DataFrame({
        "Metric": [
            "Adjusted Gross Income (AGI)",
            "Taxable Income",
            "Federal Taxes Paid",
            "Virginia State Taxes Paid",
            "Total Taxes Paid",
            "Effective Tax Rate (on Gross Salary)",
            "After-Tax Income",
            "Total Annual Savings",
            "Savings Rate",
            "Disposable Income (After Taxes & Savings)"
        ],
        "Amount": [
            f"${agi:,.0f}",
            f"${taxable_income:,.0f}",
            f"${federal_tax:,.0f}",
            f"${state_tax:,.0f}",
            f"${total_tax:,.0f}",
            f"{effective_tax_rate:.1%}",
            f"${after_tax_income:,.0f}",
            f"${total_savings:,.0f}",
            f"{savings_rate:.1%}",
            f"${disposable_income:,.0f}"
        ]
    })
    
    st.dataframe(fire_summary)
    
    # --- Contributions Table ---
    st.subheader("📚 Contributions Detail")
    contribs = [(k, v) for k, v in contributions.items()]
    st.dataframe(pd.DataFrame(contribs, columns=["Account", "Annual Contribution ($)"]))
    
    # --- Pie Chart Money Flow ---
    st.subheader("📊 Money Flow Chart")
    labels = ["Federal Taxes", "State Taxes", "Savings", "After-Tax Disposable Income"]
    values = [federal_tax, state_tax, total_savings, after_tax_income]
    
    fig1, ax1 = plt.subplots()
    ax1.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)

    # --- Contribution Impact Summary ---
    st.subheader("🚀 Contribution Impact Summary")
    baseline_taxable_income = gross_salary - STANDARD_DEDUCTION_2025
    baseline_federal_tax = calculate_tax(baseline_taxable_income, FEDERAL_BRACKETS_2025)
    baseline_state_tax = calculate_tax(baseline_taxable_income, VIRGINIA_BRACKETS_2025)
    baseline_total_tax = baseline_federal_tax + baseline_state_tax
    baseline_after_tax_income = gross_salary - baseline_total_tax
    
    st.write(f"**Reduction in Total Taxes Paid:** ${baseline_total_tax - total_tax:,.0f}")
    st.write(f"**Increase in Total Annual Savings:** ${total_savings:,.0f}")
    st.write(f"**Change in After-Tax Income:** ${after_tax_income - baseline_after_tax_income:,.0f}")
    
    comparison = pd.DataFrame({
        "No Contributions": [baseline_total_tax, baseline_after_tax_income, 0],
        "With Contributions": [total_tax, after_tax_income, total_savings]
    }, index=["Taxes Paid", "After-Tax Income", "Savings"])
    st.bar_chart(comparison)

    # --- FI Milestones ---
    st.subheader("🌱 FI Milestones Projection")
    invest_value = current_investments
    annual_contrib = total_savings
    years = []
    balances = []
    current_age = 0  # Assuming starting at year 0; user can adjust if needed
    milestones = {
        "Coast FI": False,
        "Barista FI": False,
        "Lean FI (75% Expenses)": False,
        "Full FI (100% Expenses)": False,
        "Fat FI (150% Expenses)": False,
    }
    
    # Calculate Coast FI target (amount needed now to grow to Full FI by retirement age without further contributions)
    years_to_retirement = retirement_age - current_age
    full_fi_target = annual_expenses * 25
    coast_fi_target = full_fi_target / ((1 + expected_return) ** years_to_retirement)
    
    # Calculate Barista FI (assuming 50% of expenses covered by investments, rest by part-time work)
    barista_fi_target = (annual_expenses * 0.5) * 25
    
    for year in range(1, 51):
        invest_value = invest_value * (1 + expected_return) + annual_contrib
        balances.append(invest_value)
        years.append(year)
        
        if not milestones["Coast FI"] and invest_value >= coast_fi_target:
            if year == 1 and invest_value >= coast_fi_target:
                milestones["Coast FI"] = "✅ Already Achieved"
            else:
                milestones["Coast FI"] = f"{year} years"
                
        if not milestones["Barista FI"] and invest_value >= barista_fi_target:
            if year == 1 and invest_value >= barista_fi_target:
                milestones["Barista FI"] = "✅ Already Achieved"
            else:
                milestones["Barista FI"] = f"{year} years"
                
        if not milestones["Lean FI (75% Expenses)"] and invest_value >= (annual_expenses * 0.75) * 25:
            milestones["Lean FI (75% Expenses)"] = f"{year} years" if year > 0 else "✅ Already Achieved"
            
        if not milestones["Full FI (100% Expenses)"] and invest_value >= annual_expenses * 25:
            milestones["Full FI (100% Expenses)"] = f"{year} years" if year > 0 else "✅ Already Achieved"
            
        if not milestones["Fat FI (150% Expenses)"] and invest_value >= (annual_expenses * 1.5) * 25:
            milestones["Fat FI (150% Expenses)"] = f"{year} years" if year > 0 else "✅ Already Achieved"
            
    milestone_table = pd.DataFrame(list(milestones.items()), columns=["Milestone", "Time to Achieve"])
    st.table(milestone_table)
    
    # --- Milestone Explanations (Moved Above Chart) ---
    st.subheader("📖 What the Milestones Mean")
    st.markdown("""
    - **Coast FI**: Investments grow enough by retirement age (set to {retirement_age} years) even without adding new savings.
    - **Barista FI**: Investments cover 50% of expenses; part-time work can bridge the gap.
    - **Lean FI**: Investments = 75% of your full annual expenses.
    - **Full FI**: Investments = 100% of your full desired lifestyle expenses.
    - **Fat FI**: Investments = 150% of your lifestyle expenses — extra cushion and luxury.
    """.format(retirement_age=retirement_age))
    
    # --- Net Worth Growth Chart ---
    st.subheader("📈 Investment Growth Over Time")
    fig2, ax2 = plt.subplots()
    ax2.plot(years, balances, label="Projected Portfolio Value")
    ax2.axhline(y=annual_expenses * 25, color='g', linestyle='--', label='Full FI Target (25x Expenses)')
    
    # Format Y-axis to show dollar amounts (e.g., $500k, $800k, $1M)
    ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'${int(x/1000)}k' if x < 1000000 else f'${x/1000000:.1f}M'))
    
    ax2.set_xlabel("Years")
    ax2.set_ylabel("Portfolio Value ($)")
    ax2.legend()
    st.pyplot(fig2)
