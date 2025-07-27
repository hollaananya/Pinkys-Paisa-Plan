import streamlit as st
import os
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from utils.time_machine_fi_client import TimeMachineFiClient
from agents.time_machine_agent import TimeMachineAgent
import pandas as pd
from datetime import datetime, timedelta

load_dotenv()

# Page config
st.set_page_config(
    page_title="Time Machine Financial Planner",
    page_icon="🔮💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - matching the Investment Therapy Agent style
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
.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
}
.scenario-card {
    background: #f0f8ff;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #2196f3;
}
.goal-card {
    background: #f8f9fa;
    padding: 0.8rem;
    border-radius: 8px;
    margin: 0.3rem 0;
    border-left: 4px solid #4CAF50;
}
.impact-positive { border-left-color: #4caf50 !important; background: #e8f5e8; }
.impact-negative { border-left-color: #f44336 !important; background: #ffebee; }
.impact-neutral { border-left-color: #ff9800 !important; background: #fff8e1; }
/* REMOVED .timeline-improvement CSS block because we want to remove its styling, not the text */
/* REMOVED .calculation-result CSS styling, as these boxes will be removed too */
</style>
""", unsafe_allow_html=True)

# Initialize clients
@st.cache_resource
def init_time_machine_clients():
    fi_client = TimeMachineFiClient()
    time_machine_agent = TimeMachineAgent()
    return fi_client, time_machine_agent

def create_scenario_impact_charts(scenario_analysis: dict, scenario_type: str):
    """Create visualization charts for scenario impact"""
    
    if scenario_type == 'salary_hike' and 'goal_acceleration' in scenario_analysis:
        goals = []
        original_timelines = []
        accelerated_timelines = []
        
        for goal_name, data in scenario_analysis['goal_acceleration'].items():
            goals.append(goal_name.replace('_', ' ').title())
            original_timeline_val = data.get('original_timeline_years', 5.0) 
            
            original_timelines.append(original_timeline_val) 
            accelerated_timelines.append(max(0.1, original_timeline_val - (data['acceleration_months'] / 12))) 
        
        if not goals: 
            st.info("No specific goals to show acceleration for in this scenario.")
            return None

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Original Timeline', x=goals, y=original_timelines, marker_color='lightcoral'))
        fig.add_trace(go.Bar(name='Accelerated Timeline', x=goals, y=accelerated_timelines, marker_color='lightgreen'))
        
        fig.update_layout(
            title='Goal Timeline Acceleration (Years)',
            xaxis_title='Financial Goals',
            yaxis_title='Years to Complete',
            barmode='group',
            height=400
        )
        
        return fig
    
    elif scenario_type == 'house_purchase' and 'savings_analysis' in scenario_analysis:
        labels = ['Current Savings Corpus', 'Future Monthly SIPs', 'Required Down Payment']
        values = [
            scenario_analysis['savings_analysis']['current_available'], 
            scenario_analysis['savings_analysis']['future_savings'],    
            scenario_analysis['house_details']['down_payment_required']
        ]
        colors = ['#36A2EB', '#4BC0C0', '#FF6384']
        
        values = [max(0, v) for v in values]

        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f"₹{v:,.0f}" for v in values],
            textposition='auto'
        )])
        
        fig.update_layout(
            title='House Purchase Financial Breakdown',
            yaxis_title='Amount (₹)',
            height=400
        )
        
        return fig
    
    elif scenario_type == 'family_planning' and 'cost_analysis' in scenario_analysis:
        costs = scenario_analysis['cost_analysis']['immediate_costs']
        
        fig = px.pie(
            values=list(costs.values()),
            names=[name.replace('_', ' ').title() for name in costs.keys()],
            title='Immediate Baby-Related Costs Breakdown'
        )
        
        return fig
    
    elif scenario_type == 'job_switch' and 'retirement_impact' in scenario_analysis:
        categories = ['Current EPF Path (Projected)', 'New Job Path (Projected)']
        values = [
            scenario_analysis['retirement_projections']['with_epf'],
            scenario_analysis['retirement_projections']['with_private_investment'] 
        ]
        
        fig = go.Figure(data=[go.Bar(
            x=categories,
            y=values,
            marker_color=['#FF6384', '#36A2EB'],
            text=[f"₹{v:,.0f}" for v in values],
            textposition='auto'
        )])
        
        fig.update_layout(
            title=f'Retirement Corpus Projection ({scenario_analysis["retirement_projections"]["years_to_retirement"]} Years)',
            yaxis_title='Projected Amount (₹)',
            height=400
        )
        
        return fig
    
    elif scenario_type == 'education_goal' and 'funding_analysis' in scenario_analysis:
        labels = ['Covered by Existing Savings (FV)', 'Covered by New Monthly SIPs', 'Remaining Gap']
        
        total_future_cost = scenario_analysis['education_cost_future']
        
        covered_by_corpus = scenario_analysis['current_portfolio_contribution']
        covered_by_new_sip = scenario_analysis['total_investment_needed'] 

        covered_by_corpus = min(covered_by_corpus, total_future_cost)
        covered_by_new_sip = min(covered_by_new_sip, total_future_cost - covered_by_corpus)
        
        remaining_gap = max(0, total_future_cost - covered_by_corpus - covered_by_new_sip)
        
        chart_values = [covered_by_corpus, covered_by_new_sip, remaining_gap]
        chart_colors = ['#4CAF50', '#FFC107', '#F44336'] 

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=chart_values,
            marker_colors=chart_colors,
            hole=.3,
            textinfo='percent+label',
            insidetextorientation='radial'
        )])
        
        fig.update_layout(
            title=f'Funding Breakdown for Education Goal (Total: ₹{total_future_cost:,.0f})',
            height=400
        )
        
        return fig

    elif scenario_type == 'loan_prepayment' and 'scenarios' in scenario_analysis:
        labels = ['Prepayment Path Total Benefit', 'Continue EMI Path Net Wealth']
        values = [
            scenario_analysis['scenarios']['prepayment'].get('total_benefit_prepayment_path', 0),
            scenario_analysis['scenarios']['continue_emi'].get('net_wealth_continue_emi_path', 0)
        ]
        colors = ['#4CAF50', '#FF9800'] 

        values = [max(0, v) for v in values]

        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f"₹{v:,.0f}" for v in values],
            textposition='auto'
        )])

        fig.update_layout(
            title='Loan Prepayment vs. Investing Comparison',
            yaxis_title='Projected Financial Outcome (₹)',
            height=400
        )
        return fig
    
    return None


def display_scenario_results(scenario_analysis: dict, scenario_type: str):
    """Display scenario analysis results"""
    
    if scenario_type == 'salary_hike':
        st.markdown("### 💰 Salary Hike Impact Analysis")
        
        # Removed the st.metric lines for New Monthly Income, Additional Savings Potential, Hike Percentage
        # income_data = scenario_analysis.get('income_change', {})
        # savings_data = scenario_analysis.get('savings_impact', {})
        # col1, col2, col3 = st.columns(3)
        # with col1:
        #     st.metric(
        #         "New Monthly Income", 
        #         f"₹{income_data.get('new_monthly', 0):,.0f}",
        #         f"+₹{income_data.get('additional_monthly', 0):,.0f}"
        #     )
        # with col2:
        #     st.metric(
        #         "Additional Savings Potential",
        #         f"₹{savings_data.get('additional_savings_potential', 0):,.0f}",
        #         f"+{savings_data.get('savings_rate_improvement', 0):.1f}%"
        #     )
        # with col3:
        #     st.metric(
        #         "Hike Percentage",
        #         f"{income_data.get('percentage_increase', 0):.0f}%"
        #     )
        
        # Removed the 'Recommended Allocation' header along with the boxes
        # st.markdown("#### 🎯 Recommended Allocation of Additional Income")
        
        # Removed the three 'calculation-result' markdown blocks
        # col1, col2, col3 = st.columns(3)
        # with col1:
        #     st.markdown(f"""
        #     <div class="calculation-result">
        #         <strong>Investment Increase (SIP)</strong><br>
        #         ₹{recommendations.get('investment_increase', 0):,.0f}/month<br>
        #         <small>50% of additional income</small>
        #     </div>
        #     """, unsafe_allow_html=True)
        
        # with col2:
        #     st.markdown(f"""
        #     <div class="calculation-result">
        #         <strong>Lifestyle Upgrade Limit</strong><br>
        #         ₹{recommendations.get('lifestyle_inflation_limit', 0):,.0f}/month<br>
        #         <small>30% of additional income</small>
        #     </div>
        #     """, unsafe_allow_html=True)
        
        # with col3:
        #     st.markdown(f"""
        #     <div class="calculation-result">
        #         <strong>Emergency Fund Boost</strong><br>
        #         ₹{recommendations.get('emergency_fund_boost', 0):,.0f}/month<br>
        #         <small>20% of additional income</small>
        #     </div>
        #     """, unsafe_allow_html=True)
        
        if 'goal_acceleration_impact' in scenario_analysis:
            acceleration = scenario_analysis['goal_acceleration_impact']
            if acceleration.get('acceleration_months', 0) > 0:
                # Kept the text, removed its specific styling div and class
                st.markdown(f"""
                This additional saving could accelerate your ₹{acceleration.get('house_price', 0):,.0f} home goal by approximately **{acceleration.get('acceleration_months', 0):.0f} months**!
                """)
            elif acceleration.get('acceleration_months', 0) == 0 and acceleration.get('original_timeline_years', float('inf')) == float('inf'):
                st.info("Your current savings plan for a home goal needs significant boost to become achievable.")


    
    elif scenario_type == 'house_purchase':
        st.markdown("### 🏠 House Purchase Feasibility")
        
        house_data = scenario_analysis.get('house_details', {})
        savings_data = scenario_analysis.get('savings_analysis', {})
        loan_data = scenario_analysis.get('loan_analysis', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "House Price (Future)", 
                f"₹{house_data.get('future_price', 0):,.0f}",
                f"₹{house_data.get('future_price', 0) - house_data.get('current_price', 0):,.0f} inflation impact"
            )
            st.metric(
                "Down Payment Required",
                f"₹{house_data.get('down_payment_required', 0):,.0f}"
            )
        
        with col2:
            st.metric(
                "Total Available for DP",
                f"₹{savings_data.get('total_available', 0):,.0f}",
                f"₹{savings_data.get('shortfall_surplus', 0):,.0f} {'surplus' if savings_data.get('shortfall_surplus', 0) >= 0 else 'shortfall'}"
            )
            st.metric(
                "Estimated Monthly EMI",
                f"₹{loan_data.get('monthly_emi', 0):,.0f}",
                f"{loan_data.get('emi_to_income_ratio', 0):.1f}% of income"
            )
        
        affordability = loan_data.get('affordability_status', 'unknown')
        if affordability == 'affordable':
            st.markdown('<div class="impact-positive">✅ House purchase appears affordable with your current plan and income!</div>', unsafe_allow_html=True)
        elif affordability == 'stretched':
            st.markdown('<div class="impact-neutral">⚠️ Your plan is tight but potentially manageable. Careful expense monitoring is crucial.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="impact-negative">❌ The current plan may be too aggressive. Reassessment is needed.</div>', unsafe_allow_html=True)
        
        recommendations = scenario_analysis.get('recommendation', [])
        if recommendations:
            st.markdown("#### 💡 Recommendations")
            for rec in recommendations:
                st.markdown(f"• {rec}")
    
    elif scenario_type == 'family_planning':
        st.markdown("### 👶 Family Planning Financial Impact")
        
        cost_data = scenario_analysis.get('cost_analysis', {})
        emergency_data = scenario_analysis.get('emergency_fund_impact', {})
        preparation_data = scenario_analysis.get('preparation_plan', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Estimated Immediate Costs",
                f"₹{cost_data.get('total_immediate', 0):,.0f}"
            )
            st.metric(
                "New Monthly Expenses Increase",
                f"₹{cost_data.get('total_monthly_increase', 0):,.0f}"
            )
        
        with col2:
            st.metric(
                "Emergency Fund Gap",
                f"₹{emergency_data.get('gap', 0):,.0f}",
                "Needed for 6 months of new expenses"
            )
            st.metric(
                "Monthly Preparation Target",
                f"₹{preparation_data.get('monthly_target', 0):,.0f}",
                f"Over {preparation_data.get('preparation_timeline_months', 0):.0f} months"
            )
        
        st.markdown("#### 💰 Immediate Costs Breakdown")
        immediate_costs = cost_data.get('immediate_costs', {})
        for cost_type, amount in immediate_costs.items():
            st.markdown(f"• **{cost_type.replace('_', ' ').title()}**: ₹{amount:,.0f}")
        
        st.markdown("#### 💡 Key Financial Adjustments")
        st.markdown(f"• **Target Immediate Savings**: You need to save **₹{scenario_analysis['recommendations']['immediate_savings_target']:,.0f}** before the baby arrives to cover initial costs and emergency fund boost.")
        st.markdown(f"• **Monthly Budget Adjustment**: Your regular monthly budget needs to increase by **₹{scenario_analysis['recommendations']['monthly_savings_adjustment']:,.0f}** to cover ongoing baby expenses and future education savings.")
        st.markdown(f"• **Insurance Review**: It's crucial to **{scenario_analysis['recommendations']['insurance_review']}** to protect your growing family.")

    elif scenario_type == 'job_switch':
        st.markdown("### 💼 Job Switch Financial Analysis")
        
        salary_data = scenario_analysis.get('salary_impact', {})
        epf_data = scenario_analysis.get('epf_impact', {})
        retirement_data = scenario_analysis.get('retirement_impact', {})
        net_benefit = scenario_analysis.get('net_benefit', {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "New Monthly Income",
                f"₹{salary_data.get('new_salary', 0):,.0f}",
                f"Salary Hike: {salary_data.get('percentage_change', 0):+.1f}%"
            )
        
        with col2:
            st.metric(
                "Lost EPF Contribution",
                f"₹{epf_data.get('lost_epf_monthly', 0):,.0f}/month",
                "Total (Employee + Employer)"
            )
        
        with col3:
            st.metric(
                "Net Monthly Benefit",
                f"₹{net_benefit.get('monthly_net_benefit', 0):,.0f}",
                "After accounting for private investments"
            )
        
        st.markdown("#### 🎯 Long-Term Retirement Impact")
        retirement_change = retirement_data.get('difference', 0)
        years_to_retirement = retirement_data.get('years_to_retirement', 0)

        if retirement_change > 0:
            st.markdown(f'<div class="impact-positive">✅ Your **projected retirement corpus could increase** by ₹{retirement_change:,.0f} over {years_to_retirement} years with diligent private investment.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="impact-negative">⚠️ Your **projected retirement corpus could decrease** by ₹{abs(retirement_change):,.0f} over {years_to_retirement} years if private investment does not compensate for lost EPF.</div>', unsafe_allow_html=True)

        st.markdown("#### 💡 Key Takeaways & Recommendations")
        if not epf_data.get('epf_available_new_job', True):
            alternatives = scenario_analysis.get('recommendations', {})
            st.markdown(f"""
            Since your new job does not offer EPF, it's crucial to proactively manage your retirement savings. You should aim to invest at least **₹{epf_data.get('required_private_investment_monthly', 0):,.0f} per month** to potentially match your previous EPF growth. Consider allocating these funds as follows:
            - **PPF**: Up to ₹{alternatives.get('ppf_investment_annual', 0):,.0f} annually for tax-free growth and safety.
            - **NPS**: Around ₹{alternatives.get('nps_option_annual', 0):,.0f} annually for dedicated retirement savings with tax benefits.
            - **Equity Mutual Fund SIP**: The remaining amount (approx. ₹{alternatives.get('mutual_fund_sip_annual', 0):,.0f} annually) can be invested in diversified equity mutual funds for higher growth potential.
            """)
        
        st.markdown(f"""
        Overall, the job switch is **{net_benefit.get('recommendation', '').upper()}** from a purely financial standpoint. However, consider non-financial aspects like work-life balance, career growth, and job security as well.
        """)
        
    elif scenario_type == 'education_goal':
        st.markdown("### 🎓 Education Goal Planning")
        
        cost_data = scenario_analysis.get('cost_analysis', {})
        funding_data = scenario_analysis.get('funding_analysis', {})
        strategy_data = scenario_analysis.get('investment_strategy', {})
        risks = scenario_analysis.get('risk_factors', {})

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Future Education Cost",
                f"₹{cost_data.get('total_future_cost', 0):,.0f}",
                f"Projected over {cost_data.get('timeline_years', 0):.0f} years"
            )
            st.metric(
                "Adjusted Monthly SIP Needed",
                f"₹{funding_data.get('adjusted_monthly_sip', 0):,.0f}",
                "To meet remaining goal after existing corpus"
            )
        
        with col2:
            st.metric(
                "Current Corpus Future Value",
                f"₹{funding_data.get('current_portfolio_contribution', 0):,.0f}",
                "Contribution from existing savings"
            )
            st.metric(
                "Total Monthly SIP (from scratch)",
                f"₹{funding_data.get('monthly_sip_required', 0):,.0f}",
                "If you started with no existing savings"
            )
        
        if funding_data.get('shortfall_monthly', 0) > 0:
            st.markdown(f'<div class="impact-negative">⚠️ You have a monthly shortfall of ₹{funding_data.get("shortfall_monthly", 0):,.0f}. You need to increase your current monthly allocation to meet this goal.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="impact-positive">✅ Your current savings plan, with proposed adjustments, appears on track for this goal.</div>', unsafe_allow_html=True)

        st.markdown("#### 📊 Recommended Investment Strategy")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="calculation-result">
                <strong>Target Asset Allocation</strong><br>
                Equity: {strategy_data.get('equity_allocation', 0)*100:.0f}%<br>
                Debt: {strategy_data.get('debt_allocation', 0)*100:.0f}%
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            funds = strategy_data.get('recommended_funds', [])
            st.markdown("**Suggested Fund Categories:**")
            for fund in funds:
                st.markdown(f"• {fund}")
        
        st.markdown("#### 🛡️ Risk Factors & Mitigation")
        for strategy in risks.get('mitigation_strategies', []):
            st.markdown(f"• {strategy}")
        
    elif scenario_type == 'loan_prepayment':
        st.markdown("### 💳 Loan Prepayment Analysis")
        
        loan_data = scenario_analysis.get('loan_details', {})
        scenarios = scenario_analysis.get('scenarios', {})
        recommendation = scenario_analysis.get('recommendation', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Outstanding Loan",
                f"₹{loan_data.get('outstanding_amount', 0):,.0f}"
            )
            st.metric(
                "Current EMI",
                f"₹{loan_data.get('current_emi', 0):,.0f}"
            )
        
        with col2:
            st.metric(
                "Interest Rate",
                f"{loan_data.get('interest_rate', 0):.1f}% p.a."
            )
            st.metric(
                "Remaining Interest",
                f"₹{loan_data.get('total_interest_remaining', 0):,.0f}",
                "If loan runs full term"
            )
        
        st.markdown("#### 📈 Scenario Comparison")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="calculation-result {'impact-positive' if recommendation.get('decision') == 'prepay' else ''}">
                <strong>Prepayment Path</strong><br>
                Immediate Outflow: ₹{scenarios['prepayment']['immediate_outflow']:,.0f}<br>
                Future Wealth (from investing freed EMI): ₹{scenarios['prepayment']['future_wealth_from_emi_investment']:,.0f}<br>
                <strong>Total Benefit: ₹{scenarios['prepayment']['total_benefit_prepayment_path']:,.0f}</strong>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="calculation-result {'impact-positive' if recommendation.get('decision') == 'continue_emi' else ''}">
                <strong>Continue EMI Path</strong><br>
                Total Interest Cost: ₹{scenarios['continue_emi']['total_interest_cost']:,.0f}<br>
                Future Wealth (from investing lump sum): ₹{scenarios['continue_emi']['investment_returns_on_lumpsum']:,.0f}<br>
                <strong>Net Wealth: ₹{scenarios['continue_emi']['net_wealth_continue_emi_path']:,.0f}</strong>
            </div>
            """, unsafe_allow_html=True)

        decision = recommendation.get('decision', 'unknown')
        confidence = recommendation.get('confidence_level', 'medium')
        
        if decision == 'prepay':
            st.markdown(f'<div class="impact-positive">✅ **Recommendation: Prepay the loan** (Confidence: {confidence.upper()})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="impact-neutral">📊 **Recommendation: Continue EMI and invest** (Confidence: {confidence.upper()})</div>', unsafe_allow_html=True)
        
        st.markdown(f"**Rationale**: {recommendation.get('rationale', 'Analysis based on interest rate vs investment returns')}")


def main():
    st.session_state.current_time = datetime.now()
    
    if st.button("🔄 Refresh System", help="Click if responses seem cached"):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown('<h1 class="main-header">🔮💰 Time Machine Financial Planner</h1>', unsafe_allow_html=True)
    st.subheader("Simulate Your Financial Future - Plan Today for Tomorrow's Goals")
    
    fi_client, time_machine_agent = init_time_machine_clients()
    
    with st.sidebar:
        st.header("📊 Current Financial Snapshot")
        
        current_snapshot = fi_client.get_current_financial_snapshot()
        
        assets = current_snapshot['assets']
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Portfolio Value", f"₹{assets['total_portfolio_value']:,.0f}")
            st.metric("Emergency Fund", f"₹{assets['emergency_fund']:,.0f}")
        with col2:
            st.metric("Real Estate", f"₹{assets['real_estate']:,.0f}")
            st.metric("Other Assets", f"₹{assets['other_assets']:,.0f}")
        
        income = current_snapshot['income']
        expenses = current_snapshot['expenses']
        st.subheader("💰 Monthly Cash Flow")
        st.metric("Monthly Income", f"₹{income['total_monthly_income']:,.0f}")
        st.metric("Monthly Expenses", f"₹{expenses['monthly_expenses']:,.0f}")
        
        savings = current_snapshot['savings']
        savings_rate = (savings['current_monthly_savings'] / income['total_monthly_income']) * 100 if income['total_monthly_income'] > 0 else 0
        st.metric("Monthly Savings", f"₹{savings['current_monthly_savings']:,.0f}", f"{savings_rate:.1f}%")
        
        st.subheader("🎯 Active Goals")
        goals = current_snapshot['goals']
        if goals:
            for goal_name, goal_data in goals.items():
                progress_pct = (goal_data['current_progress'] / goal_data['target_amount']) * 100 if goal_data['target_amount'] > 0 else 0
                st.markdown(f"""
                <div class="goal-card">
                    <strong>{goal_name.replace('_', ' ').title()}</strong><br>
                    Target: ₹{goal_data['target_amount']:,.0f}<br>
                    Progress: {progress_pct:.1f}% (₹{goal_data['current_progress']:,.0f})<br>
                    Timeline: {goal_data['timeline_years']:.1f} years
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No active goals found in your financial data.")
        
        st.subheader("⚡ Quick Scenarios")
        quick_scenarios = [
            ("💰 25% Salary Hike", "If I get a 25% salary hike next month, how should I adjust my investments?"),
            ("🏠 House in 3 Years", "Can I afford a ₹50 lakh house in 3 years saving ₹30,000/month?"),
            ("👶 New Baby Planning", "We're expecting a baby next year. How should I plan financially?"),
            ("🎓 MBA Abroad", "I want to do MBA in US in 4 years costing ₹80 lakhs. How to save?"),
            ("💼 Job Switch", "Moving to startup with 30% hike but no EPF. Still on track for retirement?"),
            ("💳 Prepay Loan", "Should I prepay my ₹10 lakh loan or continue EMI and invest the difference?") 
        ]
        
        for scenario_name, scenario_query in quick_scenarios:
            if st.button(scenario_name, key=scenario_name):
                st.session_state.quick_scenario = scenario_query
                st.rerun() 

    tab1, tab2, tab3, tab4 = st.tabs(["🔮 Time Machine", "📊 Scenario Analysis", "📈 Goal Projections", "🎯 What-If Calculator"])
    
    with tab1:
        st.markdown("### 🔮 Ask Your Financial Future")
        st.markdown("Describe your financial scenario, and I'll show you the future impact with detailed calculations!")
        
        with st.expander("💡 Example Scenarios", expanded=False):
            example_scenarios = [
                "**Salary Hike**: If I get a 25% salary hike next month, how should I adjust my savings and investments?",
                "**House Purchase**: Can I afford a ₹50 lakh house in 3 years if I save ₹30,000/month?",
                "**Family Planning**: We're expecting a baby next year. How should I plan financially from now?",
                "**Job Switch**: I'm moving to a startup with 30% higher salary but no EPF. Will I still be on track for retirement?",
                "**Education Goal**: I want to do an MBA in the US in 4 years. It'll cost ₹80 lakhs. What's the best way to start saving?",
                "**Loan Prepayment**: Should I pay off my ₹10L loan early or continue EMI and invest the difference?"
            ]
            
            for scenario in example_scenarios:
                st.markdown(f"• {scenario}")
        
        if "messages" not in st.session_state:
            welcome_msg = f"""Hi! I'm your Time Machine Financial Planner. I can simulate various financial scenarios and show you their impact on your goals.

**Your Current Financial Status:**
• Portfolio Value: ₹{current_snapshot['assets']['total_portfolio_value']:,.0f}
• Monthly Income: ₹{current_snapshot['income']['total_monthly_income']:,.0f}
• Monthly Savings: ₹{current_snapshot['savings']['current_monthly_savings']:,.0f}
• Active Goals: {len(current_snapshot['goals'])} goals being tracked

I can help you with:
🔮 **"What-if" Scenarios** - See how life changes impact your finances
📊 **Goal Timeline Analysis** - Check if you're on track for your dreams
💰 **Investment Optimization** - Adjust strategy based on future plans
🎯 **Risk Assessment** - Understand financial implications of major decisions

Try asking: "What if I get a 25% salary hike?" or "Can I buy a house in 3 years?"
"""
            
            st.session_state.messages = [
                {"role": "assistant", "content": welcome_msg}
            ]
        
        if hasattr(st.session_state, 'quick_scenario') and st.session_state.quick_scenario:
            prompt = st.session_state.quick_scenario
            st.session_state.messages.append({"role": "user", "content": prompt})
            del st.session_state.quick_scenario 

            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("🔮 Analyzing your financial future and calculating scenarios..."):
                    
                    response_data = time_machine_agent.generate_comprehensive_scenario_analysis(prompt)
                    
                    st.markdown(response_data["main_response"])
                    
                    if response_data["scenario_analysis"]:
                        scenario_type = response_data["classification"]["primary_scenario"]
                        
                        with st.expander("📊 Detailed Scenario Analysis", expanded=True):
                            display_scenario_results(response_data["scenario_analysis"], scenario_type)
                        
                        chart = create_scenario_impact_charts(response_data["scenario_analysis"], scenario_type)
                        if chart:
                            with st.expander("📈 Visual Analysis", expanded=False):
                                st.plotly_chart(chart, use_container_width=True)
                    
                    if response_data["action_plan"]:
                        with st.expander("🎯 Action Plan", expanded=False):
                            for i, action in enumerate(response_data["action_plan"], 1):
                                st.markdown(f"{i}. {action}")
                    
                    if response_data["financial_projections"]:
                        with st.expander("💰 Financial Projections", expanded=False):
                            projections = response_data["financial_projections"]
                            for key, value in projections.items():
                                if isinstance(value, (int, float)):
                                    st.metric(key.replace('_', ' ').title(), f"₹{value:,.0f}")
                                else:
                                    st.markdown(f"**{key.replace('_', ' ').title()}**: {value}")
                
                st.session_state.messages.append({"role": "assistant", "content": response_data["main_response"]})
                st.session_state.last_processed_prompt = prompt


        if prompt := st.chat_input("Ask about your financial future..."):
            if hasattr(st.session_state, 'last_processed_prompt') and st.session_state.last_processed_prompt == prompt:
                pass 
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("🔮 Analyzing your financial future and calculating scenarios..."):
                        response_data = time_machine_agent.generate_comprehensive_scenario_analysis(prompt)
                        st.markdown(response_data["main_response"])
                        
                        if response_data["scenario_analysis"]:
                            scenario_type = response_data["classification"]["primary_scenario"]
                            with st.expander("📊 Detailed Scenario Analysis", expanded=True):
                                display_scenario_results(response_data["scenario_analysis"], scenario_type)
                            chart = create_scenario_impact_charts(response_data["scenario_analysis"], scenario_type)
                            if chart:
                                with st.expander("📈 Visual Analysis", expanded=False):
                                    st.plotly_chart(chart, use_container_width=True)
                        
                        st.session_state.messages.append({"role": "assistant", "content": response_data["main_response"]})
                        st.session_state.last_processed_prompt = prompt 

    with tab2:
        st.header("📊 Scenario Impact Analysis")
        st.markdown("Select a scenario type to see detailed impact analysis on your financial goals.")
        
        scenario_type_tab2 = st.selectbox(
            "Choose Scenario Type",
            ["salary_hike", "house_purchase", "family_planning", "job_switch", "education_goal", "loan_prepayment"],
            format_func=lambda x: {
                "salary_hike": "💰 Salary Hike Impact",
                "house_purchase": "🏠 House Purchase Planning",
                "family_planning": "👶 Family Planning",
                "job_switch": "💼 Job Switch Analysis",
                "education_goal": "🎓 Education Goal Planning",
                "loan_prepayment": "💳 Loan Prepayment Decision"
            }[x],
            key="tab2_scenario_selector" 
        )
        
        parameters = {}
        
        if scenario_type_tab2 == "salary_hike":
            col1, col2 = st.columns(2)
            with col1:
                parameters['hike_percentage'] = st.slider("Salary Hike Percentage", 10, 100, 25, 5, key="sh_hike_pct")
            with col2:
                parameters['effective_date'] = st.date_input("Effective Date", value=datetime.now().date(), key="sh_effective_date")
        
        elif scenario_type_tab2 == "house_purchase":
            col1, col2 = st.columns(2)
            with col1:
                parameters['house_price'] = st.number_input("House Price Today (₹)", 1000000, 20000000, 5000000, 100000, key="hp_price")
                parameters['timeline_years'] = st.slider("Purchase Timeline (Years)", 1, 10, 3, key="hp_timeline")
            with col2:
                parameters['location_factor'] = st.slider("Location Price Factor", 0.5, 2.0, 1.0, 0.1, key="hp_location_factor")
                parameters['monthly_savings'] = st.number_input("Monthly Savings for House (₹)", 5000, 100000, 30000, 1000, key="hp_monthly_savings")
        
        elif scenario_type_tab2 == "family_planning":
            col1, col2 = st.columns(2)
            with col1:
                parameters['expected_date'] = st.date_input("Expected Date", value=datetime.now().date() + timedelta(days=270), key="fp_expected_date")
            with col2:
                parameters['preparation_months'] = st.slider("Preparation Period (Months)", 6, 18, 9, key="fp_prep_months")
        
        elif scenario_type_tab2 == "job_switch":
            col1, col2 = st.columns(2)
            with col1:
                current_salary = current_snapshot['income']['monthly_salary']
                parameters['new_salary'] = st.number_input("New Monthly Salary (₹)", current_salary, current_salary*2, int(current_salary*1.3), 1000, key="js_new_salary")
            with col2:
                parameters['epf_available'] = st.checkbox("EPF Available in New Job", value=False, key="js_epf_available")
        
        elif scenario_type_tab2 == "education_goal":
            col1, col2 = st.columns(2)
            with col1:
                parameters['course_cost'] = st.number_input("Total Course Cost (₹)", 1000000, 20000000, 8000000, 100000, key="eg_cost")
                parameters['timeline_years'] = st.slider("Timeline (Years)", 1, 10, 4, key="eg_timeline")
            with col2:
                parameters['is_abroad'] = st.checkbox("Studying Abroad", value=True, key="eg_is_abroad")
                parameters['currency'] = st.selectbox("Currency", ["USD", "EUR", "GBP", "CAD"], key="eg_currency") if parameters.get('is_abroad') else "INR"
        
        elif scenario_type_tab2 == "loan_prepayment":
            col1, col2 = st.columns(2)
            with col1:
                parameters['loan_amount'] = st.number_input("Outstanding Loan (₹)", 100000, 10000000, 1000000, 10000, key="lp_amount")
                parameters['interest_rate'] = st.slider("Interest Rate (% per annum)", 6.0, 18.0, 10.0, 0.1, key="lp_rate") / 100
            with col2:
                parameters['current_emi'] = st.number_input("Current EMI (₹)", 5000, 100000, 15000, 500, key="lp_emi")
                parameters['remaining_tenure'] = st.slider("Remaining Tenure (Years)", 1, 30, 15, key="lp_tenure")
        
        if st.button("🔮 Analyze Scenario Impact", type="primary", key="analyze_scenario_button"):
            with st.spinner("Analyzing scenario impact..."):
                impact_analysis = fi_client.get_scenario_impact_analysis(scenario_type_tab2, parameters)
                
                if 'error' in impact_analysis:
                    st.error(f"Error: {impact_analysis['error']}")
                else:
                    display_scenario_results(impact_analysis, scenario_type_tab2)
                    
                    chart = create_scenario_impact_charts(impact_analysis, scenario_type_tab2)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
    
    with tab3:
        st.header("🎯 Goal Timeline Projections")
        
        goals = current_snapshot['goals']
        
        if not goals:
            st.info("No active goals found. Set up your financial goals to see projections.")
        else:
            selected_goal = st.selectbox(
                "Select Goal to Analyze",
                list(goals.keys()),
                format_func=lambda x: x.replace('_', ' ').title(),
                key="goal_selector"
            )
            
            goal_data = goals[selected_goal]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Target Amount", f"₹{goal_data['target_amount']:,.0f}")
            with col2:
                progress_pct = (goal_data['current_progress'] / goal_data['target_amount']) * 100 if goal_data['target_amount'] > 0 else 0
                st.metric("Current Progress", f"₹{goal_data['current_progress']:,.0f}", f"{progress_pct:.1f}%")
            with col3:
                st.metric("Current Timeline", f"{goal_data['timeline_years']:.1f} years")
            
            st.subheader("📈 'What-If' Scenarios for Your Goal")
            
            current_monthly_goal_allocation = goal_data['monthly_allocation']
            st.metric("Current Monthly Allocation to Goal", f"₹{current_monthly_goal_allocation:,.0f}")
            
            col1, col2 = st.columns(2)
            with col1:
                new_monthly_allocation = st.number_input(
                    "New Monthly Allocation (₹)", 
                    0, 
                    200000, 
                    int(current_monthly_goal_allocation), 
                    500,
                    key="new_monthly_alloc"
                )
            with col2:
                one_time_boost = st.number_input("One-time Lump Sum Boost (₹)", 0, 5000000, 0, 10000, key="one_time_boost")
            
            display_years_current = goal_data['timeline_years'] if goal_data['timeline_years'] != float('inf') else time_machine_agent._years_to_reach_target(
                target=goal_data['target_amount'],
                monthly_sip=current_monthly_goal_allocation,
                annual_return=time_machine_agent.SIP_RETURN_RATE
            )
            display_years_current = min(display_years_current, 999.0) 
            
            adjusted_target_for_new_sip = max(0, goal_data['target_amount'] - (goal_data['current_progress'] + one_time_boost))
            
            display_years_new = time_machine_agent._years_to_reach_target(
                target=adjusted_target_for_new_sip,
                monthly_sip=new_monthly_allocation,
                annual_return=time_machine_agent.SIP_RETURN_RATE
            )
            display_years_new = min(display_years_new, 999.0)

            acceleration_years = display_years_current - display_years_new
            if display_years_new == float('inf') or display_years_current == float('inf') or new_monthly_allocation <=0:
                acceleration_text = "N/A (timeline too long or not enough savings)"
            elif acceleration_years > 0:
                acceleration_text = f"{acceleration_years:.1f} years faster"
            elif acceleration_years < 0:
                acceleration_text = f"{abs(acceleration_years):.1f} years slower"
            else:
                acceleration_text = "No change"
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="calculation-result">
                    <h4>Current Plan Est.</h4>
                    <p><strong>Timeline:</strong> {display_years_current:.1f} years</p>
                    <p><strong>Monthly:</strong> ₹{current_monthly_goal_allocation:,.0f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="calculation-result">
                    <h4>New Plan Est.</h4>
                    <p><strong>Timeline:</strong> {display_years_new:.1f} years</p>
                    <p><strong>Monthly:</strong> ₹{new_monthly_allocation:,.0f}</p>
                    <p><strong>Acceleration:</strong> {acceleration_text}</p>
                </div>
                """, unsafe_allow_html=True)
            
            if display_years_current != float('inf') and display_years_new != float('inf') and display_years_current > 0 and display_years_new > 0:
                timeline_data = {
                    'Scenario': ['Current Plan', 'New Plan'],
                    'Years': [display_years_current, display_years_new],
                    'Monthly Allocation': [current_monthly_goal_allocation, new_monthly_allocation]
                }
                
                fig = px.bar(
                    timeline_data, 
                    x='Scenario', 
                    y='Years',
                    title=f'{selected_goal.replace("_", " ").title()} - Estimated Timeline Comparison',
                    color='Monthly Allocation',
                    text='Years'
                )
                fig.update_traces(texttemplate='%{text:.1f} years', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.header("🧮 What-If Financial Calculator")
        st.markdown("Quick calculations for common financial scenarios")
        
        calc_type = st.selectbox(
            "Choose Calculator",
            ["sip_calculator", "loan_emi", "inflation_impact", "retirement_corpus"],
            format_func=lambda x: {
                "sip_calculator": "📈 SIP Future Value Calculator",
                "loan_emi": "💳 Loan EMI Calculator", 
                "inflation_impact": "📊 Inflation Impact Calculator",
                "retirement_corpus": "🎯 Retirement Corpus Calculator"
            }[x],
            key="calc_type_selector" 
        )
        
        if calc_type == "sip_calculator":
            st.subheader("📈 SIP Future Value Calculator")
            
            col1, col2 = st.columns(2)
            with col1:
                monthly_sip = st.number_input("Monthly SIP Amount (₹)", 500, 200000, 10000, 500, key="sip_amt")
                investment_years = st.slider("Investment Period (Years)", 1, 40, 10, key="sip_years")
            with col2:
                annual_return = st.slider("Expected Annual Return (%)", 1.0, 25.0, 12.0, 0.5, key="sip_return")
                
            monthly_return_rate = annual_return / 100 / 12
            months = investment_years * 12
            
            if monthly_return_rate > 0:
                future_value = monthly_sip * (((1 + monthly_return_rate) ** months - 1) / monthly_return_rate)
            else:
                future_value = monthly_sip * months
            
            total_invested = monthly_sip * months
            gains = future_value - total_invested
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Future Value", f"₹{future_value:,.0f}")
            with col2:
                st.metric("Total Invested", f"₹{total_invested:,.0f}")
            with col3:
                st.metric("Gains", f"₹{gains:,.0f}", f"{(gains/total_invested)*100:.1f}%" if total_invested > 0 else "0.0%")
        
        elif calc_type == "loan_emi":
            st.subheader("💳 Loan EMI Calculator")
            
            col1, col2 = st.columns(2)
            with col1:
                loan_amount = st.number_input("Loan Amount (₹)", 100000, 50000000, 2500000, 100000, key="loan_amt")
                interest_rate = st.slider("Interest Rate (% per annum)", 6.0, 20.0, 8.5, 0.1, key="loan_rate")
            with col2:
                loan_tenure = st.slider("Loan Tenure (Years)", 1, 30, 20, key="loan_tenure")
            
            monthly_rate = interest_rate / 100 / 12
            months = loan_tenure * 12
            
            if monthly_rate > 0:
                emi = time_machine_agent.calculate_loan_emi(loan_amount, interest_rate / 100, loan_tenure)
            else:
                emi = loan_amount / months if months > 0 else 0
            
            total_payment = emi * months
            total_interest = total_payment - loan_amount
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Monthly EMI", f"₹{emi:,.0f}")
            with col2:
                st.metric("Total Interest", f"₹{total_interest:,.0f}")
            with col3:
                st.metric("Total Payment", f"₹{total_payment:,.0f}")
        
        elif calc_type == "inflation_impact":
            st.subheader("📊 Inflation Impact Calculator")
            
            col1, col2 = st.columns(2)
            with col1:
                current_cost = st.number_input("Current Cost (₹)", 1000, 10000000, 100000, 1000, key="inf_cost")
                inflation_rate = st.slider("Inflation Rate (% per annum)", 1.0, 15.0, 6.0, 0.5, key="inf_rate")
            with col2:
                time_period = st.slider("Time Period (Years)", 1, 50, 10, key="inf_years")
            
            future_cost = time_machine_agent.project_inflation_adjusted_cost(current_cost, time_period, inflation_rate / 100)
            increase = future_cost - current_cost
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Cost", f"₹{current_cost:,.0f}")
            with col2:
                st.metric("Future Cost", f"₹{future_cost:,.0f}")
            with col3:
                st.metric("Increase", f"₹{increase:,.0f}", f"{((future_cost/current_cost)-1)*100:.1f}%" if current_cost > 0 else "0.0%")
        
        elif calc_type == "retirement_corpus":
            st.subheader("🎯 Retirement Corpus Calculator")
            
            col1, col2 = st.columns(2)
            with col1:
                current_age = st.slider("Current Age", 20, 65, 30, key="rc_curr_age")
                retirement_age = st.slider("Retirement Age", current_age + 1, 70, 60, key="rc_ret_age")
                current_expenses = st.number_input("Current Monthly Expenses (₹)", 10000, 500000, 50000, 1000, key="rc_curr_exp")
            with col2:
                inflation_rate = st.slider("Inflation Rate (% per annum)", 1.0, 10.0, 6.0, 0.5, key="rc_inf_rate")
                return_rate = st.slider("Investment Return (%)", 1.0, 20.0, 12.0, 0.5, key="rc_ret_rate")
                replacement_ratio = st.slider("Expense Replacement Ratio (%)", 50, 100, 75, 5, key="rc_replace_ratio")
            
            years_to_retirement = retirement_age - current_age
            
            future_monthly_expenses = current_expenses * ((1 + inflation_rate / 100) ** years_to_retirement)
            required_monthly_expenses = future_monthly_expenses * (replacement_ratio / 100)
            
            required_corpus = required_monthly_expenses * 12 / 0.04
            
            required_monthly_sip = time_machine_agent._calculate_sip_for_target(
                target_amount=required_corpus,
                years=years_to_retirement,
                annual_return=return_rate / 100
            )
            
            st.markdown("#### 📊 Retirement Planning Results")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Years to Retirement", f"{years_to_retirement}")
            with col2:
                st.metric("Future Monthly Need", f"₹{required_monthly_expenses:,.0f}")
            with col3:
                st.metric("Required Corpus", f"₹{required_corpus:,.0f}")
            with col4:
                st.metric("Monthly SIP Needed", f"₹{required_monthly_sip:,.0f}")
            
            current_sip = current_snapshot['savings']['monthly_sip']
            sip_gap = max(0, required_monthly_sip - current_sip)
            
            if sip_gap > 0:
                st.warning(f"⚠️ You need to increase your SIP by ₹{sip_gap:,.0f} to meet retirement goals")
            else:
                st.success("✅ Your current SIP appears sufficient for retirement goals!")

if __name__ == "__main__":
    main()