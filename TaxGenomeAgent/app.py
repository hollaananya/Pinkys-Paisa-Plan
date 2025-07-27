import streamlit as st
import os
import json
from dotenv import load_dotenv
from utils.fi_mcp_client import FiMCPClient
from agents.tax_genome_agent import TaxGenomeAgent, TaxRegime
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

load_dotenv()

# Page config
st.set_page_config(
    page_title="Tax Genome Agent",
    page_icon="🧬💰",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    text-align: center;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: 1rem;
}
.tax-card {
    background: white;
    padding: 1.5rem;
    border-radius: 15px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin: 1rem 0;
    border-left: 5px solid #667eea;
}
.savings-highlight {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    margin: 1rem 0;
}
.deduction-item {
    background: #232946;   /* dark blue */
    color: #fff;           /* white text */
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #28a745;
}
.urgent-action {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
}
.regime-comparison {
    background: #1a237e; /* dark blue */
    color: #fff;         /* white text for contrast */
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #2196f3;
}
</style>
""", unsafe_allow_html=True)

# Initialize clients
@st.cache_resource
def init_clients():
    fi_client = FiMCPClient()
    tax_agent = TaxGenomeAgent()
    return fi_client, tax_agent

def display_tax_dashboard(fi_client, tax_agent):
    """Display comprehensive tax dashboard"""
    
    # Get tax profile data
    tax_profile = fi_client.get_tax_profile_data()
    deduction_analysis = fi_client.get_deduction_analysis()
    family_profile = fi_client.get_family_tax_profile()
    
    # Calculate tax for both regimes
    gross_income = tax_profile.get('annual_income', 0)
    current_deductions = tax_profile.get('current_deductions', {})
    
    old_regime_tax = tax_agent._calculate_tax_liability(
        gross_income, TaxRegime.OLD, current_deductions
    )
    new_regime_tax = tax_agent._calculate_tax_liability(
        gross_income, TaxRegime.NEW, {}
    )
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Annual Income", f"₹{gross_income:,.0f}")
    
    with col2:
        better_regime = "Old" if old_regime_tax.total_tax < new_regime_tax.total_tax else "New"
        better_tax = min(old_regime_tax.total_tax, new_regime_tax.total_tax)
        st.metric("Optimal Tax", f"₹{better_tax:,.0f}", f"{better_regime} Regime")
    
    with col3:
        total_deductions_used = sum(current_deductions.values())
        st.metric("Deductions Used", f"₹{total_deductions_used:,.0f}")
    
    with col4:
        potential_savings = abs(old_regime_tax.total_tax - new_regime_tax.total_tax)
        if old_regime_tax.total_tax < new_regime_tax.total_tax:
            optimization = tax_agent._optimize_deductions(gross_income, tax_profile)
            potential_savings += optimization.get("total_potential_savings", 0)
        st.metric("Potential Savings", f"₹{potential_savings:,.0f}")
    
    # Tax regime comparison
    st.subheader("🏛️ Tax Regime Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="regime-comparison">
            <h4>📜 Old Regime</h4>
            <p><strong>Tax Liability:</strong> ₹{old_regime_tax.total_tax:,.0f}</p>
            <p><strong>Effective Rate:</strong> {old_regime_tax.effective_tax_rate:.2f}%</p>
            <p><strong>Deductions Used:</strong> ₹{total_deductions_used:,.0f}</p>
            <p><strong>Taxable Income:</strong> ₹{old_regime_tax.taxable_income:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="regime-comparison">
            <h4>✨ New Regime</h4>
            <p><strong>Tax Liability:</strong> ₹{new_regime_tax.total_tax:,.0f}</p>
            <p><strong>Effective Rate:</strong> {new_regime_tax.effective_tax_rate:.2f}%</p>
            <p><strong>Deductions Used:</strong> ₹0 (No deductions)</p>
            <p><strong>Taxable Income:</strong> ₹{new_regime_tax.taxable_income:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recommended regime
    if old_regime_tax.total_tax < new_regime_tax.total_tax:
        savings = new_regime_tax.total_tax - old_regime_tax.total_tax
        st.markdown(f"""
        <div class="savings-highlight">
            <h3>🎯 Recommendation: OLD REGIME</h3>
            <p>You can save ₹{savings:,.0f} annually by staying with the old regime and maximizing deductions!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        savings = old_regime_tax.total_tax - new_regime_tax.total_tax
        st.markdown(f"""
        <div class="savings-highlight">
            <h3>✨ Recommendation: NEW REGIME</h3>
            <p>Switch to new regime and save ₹{savings:,.0f} annually with simplified tax structure!</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Deduction utilization chart
    st.subheader("📊 Deduction Utilization Analysis")
    
    deduction_data = {
        'Section': ['80C', '80CCD(1B)', '80D', '24(b)'],
        'Utilized': [
            deduction_analysis.get('section_80c', {}).get('utilized', 0),
            deduction_analysis.get('section_80ccd_1b', {}).get('utilized', 0),
            deduction_analysis.get('section_80d', {}).get('utilized', 0),
            current_deductions.get('24B', 0)
        ],
        'Limit': [150000, 50000, 75000, 200000],
        'Remaining': [
            deduction_analysis.get('section_80c', {}).get('remaining', 0),
            deduction_analysis.get('section_80ccd_1b', {}).get('remaining', 0),
            deduction_analysis.get('section_80d', {}).get('remaining', 0),
            200000 - current_deductions.get('24B', 0)
        ]
    }
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Utilized', x=deduction_data['Section'], y=deduction_data['Utilized'], marker_color='#667eea'))
    fig.add_trace(go.Bar(name='Remaining', x=deduction_data['Section'], y=deduction_data['Remaining'], marker_color='#ffa726'))
    
    fig.update_layout(
        title='Deduction Utilization vs Limits',
        xaxis_title='Tax Sections',
        yaxis_title='Amount (₹)',
        barmode='stack',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Current investments breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Current Tax-Saving Investments")
        investments = tax_profile.get('investments', {})
        
        # PPF
        ppf_data = investments.get('ppf', {})
        st.markdown(f"""
        <div class="deduction-item">
            <strong>PPF (Public Provident Fund)</strong><br>
            Current Year: ₹{ppf_data.get('current_year_contribution', 0):,.0f}<br>
            Total Balance: ₹{ppf_data.get('total_balance', 0):,.0f}<br>
            Remaining 80C: ₹{ppf_data.get('remaining_80c_limit', 0):,.0f}
        </div>
        """, unsafe_allow_html=True)
        
        # ELSS
        elss_data = investments.get('elss', {})
        st.markdown(f"""
        <div class="deduction-item">
            <strong>ELSS (Equity Linked Savings Scheme)</strong><br>
            Current Investment: ₹{elss_data.get('current_investments', 0):,.0f}<br>
            Market Value: ₹{elss_data.get('market_value', 0):,.0f}<br>
            Remaining 80C: ₹{elss_data.get('remaining_80c_limit', 0):,.0f}
        </div>
        """, unsafe_allow_html=True)
        
        # NPS
        nps_data = investments.get('nps', {})
        st.markdown(f"""
        <div class="deduction-item">
            <strong>NPS (National Pension System)</strong><br>
            Employee Contribution: ₹{nps_data.get('employee_contribution', 0):,.0f}<br>
            Additional 80CCD(1B): ₹{nps_data.get('additional_80ccd_1b', 0):,.0f}<br>
            Remaining Limit: ₹{nps_data.get('remaining_80ccd_1b_limit', 0):,.0f}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🏥 Insurance & Loans")
        
        # Health Insurance
        insurance = tax_profile.get('insurance', {})
        health_data = insurance.get('health_insurance', {})
        st.markdown(f"""
        <div class="deduction-item">
            <strong>Health Insurance (Section 80D)</strong><br>
            Self/Family Premium: ₹{health_data.get('self_family_premium', 0):,.0f}<br>
            Parents Premium: ₹{health_data.get('parents_premium', 0):,.0f}<br>
            Senior Citizen: {'Yes' if health_data.get('is_parents_senior_citizen') else 'No'}<br>
            Remaining 80D: ₹{health_data.get('remaining_80d_limit', 0):,.0f}
        </div>
        """, unsafe_allow_html=True)
        
        # Home Loan
        loans = tax_profile.get('loans', {})
        home_loan = loans.get('home_loan', {})
        st.markdown(f"""
        <div class="deduction-item">
            <strong>Home Loan (Section 24b)</strong><br>
            Outstanding: ₹{home_loan.get('outstanding_principal', 0):,.0f}<br>
            Interest Paid: ₹{home_loan.get('annual_interest_paid', 0):,.0f}<br>
            Principal Repayment: ₹{home_loan.get('principal_repayment', 0):,.0f}<br>
            Remaining 24b: ₹{home_loan.get('remaining_24b_limit', 0):,.0f}
        </div>
        """, unsafe_allow_html=True)
        
        # Education Loan
        edu_loan = loans.get('education_loan', {})
        if edu_loan.get('outstanding_amount', 0) > 0:
            st.markdown(f"""
            <div class="deduction-item">
                <strong>Education Loan (Section 80E)</strong><br>
                Outstanding: ₹{edu_loan.get('outstanding_amount', 0):,.0f}<br>
                Interest Paid: ₹{edu_loan.get('annual_interest_paid', 0):,.0f}<br>
                <em>No limit on deduction</em>
            </div>
            """, unsafe_allow_html=True)

def display_optimization_recommendations(fi_client, tax_agent):
    """Display optimization recommendations"""
    st.subheader("🎯 Tax Optimization Recommendations")
    
    tax_profile = fi_client.get_tax_profile_data()
    gross_income = tax_profile.get('annual_income', 0)
    optimization = tax_agent._optimize_deductions(gross_income, tax_profile)
    
    # Priority actions
    st.markdown("### 🚨 High Priority Actions")
    
    for rec in optimization.get('section_80c', []):
        if rec.get('tax_savings', 0) > 0:
            st.markdown(f"""
            <div class="urgent-action">
                <strong>Section 80C Optimization</strong><br>
                {rec['message']}<br>
                <strong>Potential Tax Savings: ₹{rec['tax_savings']:,.0f}</strong><br>
                <em>Suggestions:</em>
                <ul>
                    {"".join([f"<li>{suggestion}</li>" for suggestion in rec.get('suggestions', [])])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    for rec in optimization.get('section_80ccd_1b', []):
        if rec.get('tax_savings', 0) > 0:
            st.markdown(f"""
            <div class="urgent-action">
                <strong>Section 80CCD(1B) - NPS</strong><br>
                {rec['message']}<br>
                <strong>Potential Tax Savings: ₹{rec['tax_savings']:,.0f}</strong><br>
                <em>Additional NPS contribution provides extra deduction over 80C</em>
            </div>
            """, unsafe_allow_html=True)
    
    for rec in optimization.get('section_80d', []):
        if rec.get('tax_savings', 0) > 0:
            st.markdown(f"""
            <div class="urgent-action">
                <strong>Section 80D - Health Insurance</strong><br>
                {rec['message']}<br>
                <strong>Potential Tax Savings: ₹{rec['tax_savings']:,.0f}</strong><br>
                <em>Essential for family health security + tax benefits</em>
            </div>
            """, unsafe_allow_html=True)
    
    # Family tax planning
    family_profile = fi_client.get_family_tax_profile()
    if family_profile:
        st.markdown("### 👨‍👩‍👧‍👦 Family Tax Planning")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Family Income Analysis**")
            st.write(f"Total Family Income: ₹{family_profile.get('total_family_income', 0):,.0f}")
            st.write(f"Education Expenses: ₹{family_profile.get('education_expenses', 0):,.0f}")
            st.write(f"Healthcare Expenses: ₹{family_profile.get('healthcare_expenses', 0):,.0f}")
        
        with col2:
            optimization_potential = family_profile.get('optimization_potential', {})
            st.markdown("**Optimization Opportunities**")
            if optimization_potential.get('spouse_investments', 0) > 0:
                st.write(f"• Spouse 80C Investments: ₹{optimization_potential['spouse_investments']:,.0f}")
            if optimization_potential.get('children_education_deduction', 0) > 0:
                st.write(f"• Children Education Deduction: ₹{optimization_potential['children_education_deduction']:,.0f}")
            if optimization_potential.get('parents_health_deduction', 0) > 0:
                st.write(f"• Parents Health Deduction: ₹{optimization_potential['parents_health_deduction']:,.0f}")

def display_salary_optimization(fi_client):
    """Display salary structure optimization"""
    st.subheader("💼 Salary Structure Optimization")
    
    salary_data = fi_client.get_salary_structure_data()
    
    if salary_data:
        current_structure = salary_data.get('current_structure', {})
        gross_salary = salary_data.get('gross_salary', 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Current Salary Structure**")
            for component, amount in current_structure.items():
                component_name = component.replace('_', ' ').title()
                st.write(f"{component_name}: ₹{amount:,.0f}")
            st.write(f"**Total Gross: ₹{gross_salary:,.0f}**")
        
        with col2:
            st.markdown("**Optimization Suggestions**")
            suggestions = salary_data.get('optimization_suggestions', [])
            for suggestion in suggestions:
                st.write(f"• {suggestion}")
            
            # Show potential tax-efficient structure
            st.markdown("**Recommended Changes:**")
            st.write("• Maximize HRA to 50% of basic salary")
            st.write("• Utilize full LTA limit (₹15,000)")
            st.write("• Optimize food coupons to ₹26,400")
            st.write("• Increase mobile/internet reimbursement")

def display_tax_calendar():
    """Display tax calendar and important dates"""
    st.subheader("📅 Tax Calendar & Important Dates")
    
    current_date = datetime.now()
    current_year = current_date.year
    
    # Create timeline data
    timeline_data = [
        {"Date": f"{current_year}-04-01", "Event": "New Financial Year Begins", "Type": "Info"},
        {"Date": f"{current_year}-06-15", "Event": "Q1 Advance Tax Due", "Type": "Payment"},
        {"Date": f"{current_year}-07-31", "Event": "ITR Filing Deadline", "Type": "Compliance"},
        {"Date": f"{current_year}-09-15", "Event": "Q2 Advance Tax Due", "Type": "Payment"},
        {"Date": f"{current_year}-12-15", "Event": "Q3 Advance Tax Due", "Type": "Payment"},
        {"Date": f"{current_year+1}-01-31", "Event": "TDS Certificate (Form 16) Due", "Type": "Info"},
        {"Date": f"{current_year+1}-03-15", "Event": "Q4 Advance Tax Due", "Type": "Payment"},
        {"Date": f"{current_year+1}-03-31", "Event": "Tax Saving Investment Deadline", "Type": "Investment"},
    ]
    
    # Display as table
    df = pd.DataFrame(timeline_data)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Days from Now'] = (df['Date'] - current_date).dt.days
    
    # Color code based on urgency
    def color_rows(row):
        if row['Days from Now'] <= 30:
            return ['background-color: #ffcccb'] * len(row)
        elif row['Days from Now'] <= 90:
            return ['background-color: #ffffcc'] * len(row)
        else:
            return ['background-color: #ccffcc'] * len(row)
    
    styled_df = df.style.apply(color_rows, axis=1)
    st.dataframe(styled_df, use_container_width=True)
    
    # Urgent actions
    urgent_actions = df[df['Days from Now'] <= 60].copy()
    if not urgent_actions.empty:
        st.markdown("### ⚠️ Upcoming Deadlines (Next 60 Days)")
        for _, action in urgent_actions.iterrows():
            st.markdown(f"""
            <div class="urgent-action">
                <strong>{action['Event']}</strong><br>
                Date: {action['Date'].strftime('%B %d, %Y')}<br>
                Days Remaining: {action['Days from Now']} days
            </div>
            """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🧬💰 Tax Genome Agent</h1>', unsafe_allow_html=True)
    st.subheader("Your AI-Powered Tax Optimization Assistant")
    
    # Initialize
    fi_client, tax_agent = init_clients()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧬 Tax Genome Navigation")
        
        page = st.selectbox(
            "Choose Your Tax Analysis",
            ["📊 Tax Dashboard", "🎯 Optimization", "💼 Salary Structure", "📅 Tax Calendar", "💬 Tax Chat"]
        )
        
        # Quick stats
        st.markdown("---")
        st.subheader("Quick Stats")
        tax_profile = fi_client.get_tax_profile_data()
        if tax_profile:
            gross_income = tax_profile.get('annual_income', 0)
            st.metric("Annual Income", f"₹{gross_income:,.0f}")
            
            deduction_analysis = fi_client.get_deduction_analysis()
            total_deductions = deduction_analysis.get('total_deductions_used', 0)
            st.metric("Deductions Used", f"₹{total_deductions:,.0f}")
            
            # Calculate tax savings potential
            optimization = tax_agent._optimize_deductions(gross_income, tax_profile)
            potential_savings = optimization.get('total_potential_savings', 0)
            st.metric("Potential Savings", f"₹{potential_savings:,.0f}")
    
    # Main content based on page selection
    if page == "📊 Tax Dashboard":
        display_tax_dashboard(fi_client, tax_agent)
    
    elif page == "🎯 Optimization":
        display_optimization_recommendations(fi_client, tax_agent)
    
    elif page == "💼 Salary Structure":
        display_salary_optimization(fi_client)
    
    elif page == "📅 Tax Calendar":
        display_tax_calendar()
    
    elif page == "💬 Tax Chat":
        # Tax Chat Interface
        st.subheader("💬 Tax Consultation Chat")
        
        if "tax_messages" not in st.session_state:
            welcome_msg = """
👋 Hello! I'm your Tax Genome Agent - your personal AI tax optimization expert.

I can help you with:
• Tax regime comparison (Old vs New)
• Deduction optimization strategies
• Family tax planning
• Salary structure optimization
• Investment recommendations for tax savings
• Important tax deadlines and compliance

What would you like to know about your taxes today?
"""
            st.session_state.tax_messages = [
                {"role": "assistant", "content": welcome_msg}
            ]
        
        # Display chat messages
        for message in st.session_state.tax_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about tax optimization..."):
            # Add user message
            st.session_state.tax_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your tax situation..."):
                    # Generate comprehensive tax response
                    response = tax_agent.generate_comprehensive_tax_response(prompt)
                    st.markdown(response)
                    
                    # Show relevant data if specific sections mentioned
                    if "80c" in prompt.lower() or "deduction" in prompt.lower():
                        deduction_analysis = fi_client.get_deduction_analysis()
                        with st.expander("📊 Your Current Deduction Status"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("80C Used", f"₹{deduction_analysis.get('section_80c', {}).get('utilized', 0):,.0f}")
                            with col2:
                                st.metric("80CCD(1B) Used", f"₹{deduction_analysis.get('section_80ccd_1b', {}).get('utilized', 0):,.0f}")
                            with col3:
                                st.metric("80D Used", f"₹{deduction_analysis.get('section_80d', {}).get('utilized', 0):,.0f}")
                    
                    if "regime" in prompt.lower():
                        tax_profile = fi_client.get_tax_profile_data()
                        gross_income = tax_profile.get('annual_income', 0)
                        current_deductions = tax_profile.get('current_deductions', {})
                        
                        old_tax = tax_agent._calculate_tax_liability(
                            gross_income, TaxRegime.OLD, current_deductions
                        )
                        new_tax = tax_agent._calculate_tax_liability(
                            gross_income, TaxRegime.NEW, {}
                        )
                        
                        with st.expander("⚖️ Detailed Regime Comparison"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Old Regime**")
                                st.metric("Tax Liability", f"₹{old_tax.total_tax:,.0f}")
                                st.metric("Effective Rate", f"{old_tax.effective_tax_rate:.2f}%")
                            with col2:
                                st.markdown("**New Regime**")
                                st.metric("Tax Liability", f"₹{new_tax.total_tax:,.0f}")
                                st.metric("Effective Rate", f"{new_tax.effective_tax_rate:.2f}%")
            
            st.session_state.tax_messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()