import os
os.environ['STREAMLIT_SERVER_PORT'] = '8502'
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
import streamlit as st
import os
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from utils.enhanced_fi_client import EnhancedFiMCPClient
from agents.advanced_therapy_agent import AdvancedInvestmentTherapyAgent
import pandas as pd

load_dotenv()

# Page config
st.set_page_config(
    page_title="Advanced Investment Therapy Agent",
    page_icon="🧠💰",
    layout="wide",
    initial_sidebar_state="expanded"
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
.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
}
.holding-item {
    background: #f8f9fa;
    padding: 0.8rem;
    border-radius: 8px;
    margin: 0.3rem 0;
    border-left: 4px solid #4CAF50;
}
.risk-high { border-left-color: #f44336 !important; }
.risk-medium { border-left-color: #ff9800 !important; }
.risk-low { border-left-color: #4caf50 !important; }
.stress-indicator {
    padding: 0.5rem;
    border-radius: 5px;
    margin: 0.5rem 0;
}
.stress-high { background: #ffebee; border-left: 4px solid #f44336; }
.stress-medium { background: #fff8e1; border-left: 4px solid #ff9800; }
.stress-low { background: #e8f5e8; border-left: 4px solid #4caf50; }
.recommendation-card {
    background: #f0f7ff;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #2196f3;
}
</style>
""", unsafe_allow_html=True)

# Initialize clients
@st.cache_resource
def init_clients():
    fi_client = EnhancedFiMCPClient()
    therapy_agent = AdvancedInvestmentTherapyAgent()
    return fi_client, therapy_agent

def create_portfolio_charts(portfolio_data, risk_analysis):
    """Create portfolio visualization charts"""
    
    # Holdings allocation chart
    holdings_df = pd.DataFrame([
        {
            'Symbol': h['symbol'],
            'Value': h['market_value'],
            'Allocation': h['allocation_percentage'],
            'P&L': h['unrealized_gain_loss'],
            'Risk': h['risk_level']
        }
        for h in portfolio_data['holdings']
    ])
    
    # Pie chart for allocation
    fig_allocation = px.pie(
        holdings_df, 
        values='Allocation', 
        names='Symbol',
        title='Portfolio Allocation',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_allocation.update_traces(textposition='inside', textinfo='percent+label')
    
    # Risk distribution chart
    risk_data = {
        'Risk Level': ['High Risk', 'Medium Risk', 'Low Risk'],
        'Percentage': [
            risk_analysis['high_risk_percent'],
            risk_analysis['medium_risk_percent'],
            risk_analysis['low_risk_percent']
        ]
    }
    
    fig_risk = px.bar(
        risk_data,
        x='Risk Level',
        y='Percentage',
        title='Risk Distribution',
        color='Risk Level',
        color_discrete_map={
            'High Risk': '#f44336',
            'Medium Risk': '#ff9800',
            'Low Risk': '#4caf50'
        }
    )
    
    return fig_allocation, fig_risk

def display_behavioral_insights(behavioral_analysis):
    """Display behavioral analysis insights"""
    stress_level = behavioral_analysis.get('stress_level', 5)
    confidence_level = behavioral_analysis.get('confidence_level', 5)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if stress_level > 7:
            st.error(f"🚨 **High Stress Detected: {stress_level}/10**")
        elif stress_level > 4:
            st.warning(f"⚠️ **Moderate Stress: {stress_level}/10**")
        else:
            st.success(f"😌 **Low Stress: {stress_level}/10**")
    
    with col2:
        if confidence_level > 6:
            st.success(f"💪 **Confidence: {confidence_level}/10**")
        elif confidence_level > 3:
            st.warning(f"💪 **Confidence: {confidence_level}/10**")
        else:
            st.error(f"💪 **Confidence: {confidence_level}/10**")
    
    with col3:
        decision_risk = behavioral_analysis.get('decision_quality_risk', 'medium')
        if decision_risk == "high":
            st.error(f"🔴 **Decision Risk: {decision_risk.title()}**")
        elif decision_risk == "medium":
            st.warning(f"🟡 **Decision Risk: {decision_risk.title()}**")
        else:
            st.success(f"🟢 **Decision Risk: {decision_risk.title()}**")
    
    # Display behavioral biases if detected
    biases = behavioral_analysis.get('behavioral_biases', [])
    if biases:
        st.markdown("**🧠 Detected Behavioral Patterns:**")
        for bias in biases:
            st.markdown(f"• {bias.replace('_', ' ').title()}")
        
    # Display emotional state
    emotional_state = behavioral_analysis.get('emotional_state', [])
    if emotional_state:
        st.markdown(f"**😊 Current Emotional State:** {', '.join(emotional_state).title()}")
        
    # Display key insights
    key_insights = behavioral_analysis.get('key_insights', [])
    if key_insights:
        st.markdown("**💡 Key Insights:**")
        for insight in key_insights:
            st.markdown(f"• {insight}")

def display_recommendations(recommendations):
    """Display investment recommendations"""
    if not recommendations:
        return
    
    st.markdown("### 💡 Personalized Investment Recommendations")
    
    for i, rec in enumerate(recommendations[:3]):
        fund = rec['fund']
        score = rec['suitability_score']
        rationale = rec['rationale']
        
        # Color code by suitability score
        if score >= 8:
            border_color = "#4caf50"  # Green
            score_color = "#4caf50"
        elif score >= 6:
            border_color = "#ff9800"  # Orange
            score_color = "#ff9800"
        else:
            border_color = "#f44336"  # Red
            score_color = "#f44336"
        
        # Use Streamlit's built-in container instead of custom HTML
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**#{i+1} {fund['symbol']} - {fund['name']}**")
                st.write(f"**Category:** {fund['category'].replace('_', ' ').title()}")
                st.write(f"**Risk Level:** {fund['risk_level'].title()}")
                st.write(f"**Expense Ratio:** {fund['expense_ratio']:.2f}%")
                st.write(f"**Why this fits you:** {rationale}")
                st.write(f"*{fund['description']}*")
            
            with col2:
                st.metric("Suitability Score", f"{score:.1f}/10")
            
            st.divider()

def main():
    if st.button("🔄 Refresh System", help="Click if responses seem cached"):
        st.cache_resource.clear()
        st.rerun()
    # Header
    st.markdown('<h1 class="main-header">🧠💰 Advanced Investment Therapy Agent</h1>', unsafe_allow_html=True)
    st.subheader("Your AI-Powered Behavioral Investment Coach with Personalized Recommendations")
    
    # Initialize clients
    fi_client, therapy_agent = init_clients()
    
    # Sidebar - Enhanced Portfolio Overview
    with st.sidebar:
        st.header("📊 Your Investment Profile")
        
        # Load data
        portfolio = fi_client.get_portfolio_data()
        account_profile = fi_client.get_account_summary()
        behavioral_history = fi_client.get_behavioral_history()
        risk_analysis = fi_client.analyze_portfolio_risk()
        
        # Key metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Value", f"₹{portfolio['total_value']:,.2f}")
            st.metric("Available Cash", f"₹{account_profile['available_cash']:,.2f}")
        with col2:
            change_color = "normal" if portfolio['performance']['day_change'] >= 0 else "inverse"
            st.metric("Today's Change", 
                     f"₹{portfolio['performance']['day_change']:,.2f}",
                     f"{portfolio['performance']['day_change_percentage']:.2f}%",
                     delta_color=change_color)
            st.metric("Total Return", 
                     f"₹{portfolio['performance']['total_return']:,.2f}",
                     f"{portfolio['performance']['total_return_percentage']:.2f}%")
        
        # Risk Analysis
        st.subheader("⚖️ Risk Profile")
        st.metric("Portfolio Risk Score", f"{risk_analysis['risk_score']:.1f}/10")
        
        risk_col1, risk_col2, risk_col3 = st.columns(3)
        with risk_col1:
            st.metric("High Risk", f"{risk_analysis['high_risk_percent']:.1f}%")
        with risk_col2:
            st.metric("Medium Risk", f"{risk_analysis['medium_risk_percent']:.1f}%")
        with risk_col3:
            st.metric("Low Risk", f"{risk_analysis['low_risk_percent']:.1f}%")
        
        # User profile
        st.subheader("👤 Your Profile")
        st.write(f"**Risk Tolerance:** {account_profile['risk_tolerance'].replace('_', ' ').title()}")
        st.write(f"**Experience:** {account_profile['investment_experience'].title()}")
        st.write(f"**Time Horizon:** {account_profile['time_horizon']}")
        st.write(f"**Goals:** {', '.join(account_profile['investment_goals'])}")
        
        # Behavioral insights
        emotional_patterns = behavioral_history.get('emotional_patterns', {})
        if emotional_patterns:
            st.subheader("🧠 Behavioral Profile")
            st.write(f"**Risk Comfort:** {emotional_patterns.get('risk_comfort', 'Unknown').replace('_', ' ').title()}")
            st.write(f"**Volatility Tolerance:** {emotional_patterns.get('volatility_tolerance', 5)}/10")
            st.write(f"**FOMO Tendency:** {emotional_patterns.get('fomo_tendency', 5)}/10")
            st.write(f"**Loss Aversion:** {emotional_patterns.get('loss_aversion_score', 5)}/10")
        
        # Top holdings with risk indicators
        st.subheader("🏢 Top Holdings")
        for holding in portfolio['holdings'][:5]:
            gain_loss = holding['unrealized_gain_loss']
            gain_color = "green" if gain_loss > 0 else "red"
            risk_class = f"risk-{holding['risk_level']}"
            
            st.markdown(f"""
            <div class="holding-item {risk_class}">
                <strong>{holding['symbol']}</strong> ({holding['allocation_percentage']:.1f}%)<br>
                <span style='color: {gain_color}'>₹{gain_loss:,.2f}</span><br>
                <small>{holding['risk_level'].title()} Risk</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Market context
        market_data = fi_client.get_market_data()
        st.subheader("📈 Market Pulse")
        fear_greed = market_data['market_indicators']['fear_greed_index']
        fg_color = "green" if fear_greed > 60 else "red" if fear_greed < 40 else "orange"
        st.write(f"Fear/Greed: <span style='color: {fg_color}'>{fear_greed}/100</span>", unsafe_allow_html=True)
        st.write(f"VIX: {market_data['market_indicators']['vix']}")
        print(f"DEBUG - market_trend type: {type(market_data['market_indicators']['market_trend'])}")
        print(f"DEBUG - market_trend value: {market_data['market_indicators']['market_trend']}")
        trend = market_data['market_indicators'].get('market_trend', 'neutral')
        if isinstance(trend, str):
            st.write(f"Trend: {trend.replace('_', ' ').title()}")
        else:
            st.write(f"Trend: {str(trend).title()}")
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat Therapy", "📊 Portfolio Analysis", "📈 Investment Recommendations"])
    
    with tab1:
        # Main Chat Interface
        if "messages" not in st.session_state:
            welcome_msg = f"""Hi! I'm your Advanced Investment Therapy Agent. I'm here to help you make emotionally intelligent investment decisions by understanding your behavioral patterns and providing personalized guidance.

I can see you have a ₹{portfolio['total_value']:,.2f} portfolio with {len(portfolio['holdings'])} holdings. Your risk profile shows {risk_analysis['risk_score']:.1f}/10 risk score, and you're focused on {', '.join(account_profile['investment_goals'])}.

I can help you with:
• **Investment Recommendations** - Tell me an amount you want to invest (e.g., "I want to invest ₹500")
• **Emotional Support** - Share your investment worries or concerns
• **Portfolio Analysis** - Ask about your current holdings and performance
• **Behavioral Insights** - Understand your investment patterns and biases

How are you feeling about your investments today?"""
            
            st.session_state.messages = [
                {"role": "assistant", "content": welcome_msg}
            ]
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Share your investment thoughts, ask for recommendations, or tell me an amount you want to invest..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate comprehensive response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your emotions, behavioral patterns, and generating personalized guidance..."):
                    
                    
                    # Get comprehensive response
                    response_data = therapy_agent.generate_comprehensive_response(prompt)
                    
                    # Display main response
                    st.markdown(response_data["main_response"])
                    
                    # Display behavioral insights
                    if response_data["behavioral_analysis"]:
                        with st.expander("🧠 Behavioral Analysis", expanded=False):
                            display_behavioral_insights(response_data["behavioral_analysis"])
                    
                    # Display investment recommendations if available
                    if response_data["recommendations"]:
                        with st.expander("💡 Investment Recommendations", expanded=True):
                            display_recommendations(response_data["recommendations"])
                    
                    # Show coping strategies if needed
                    if response_data["coping_strategies"]:
                        with st.expander("🛠️ Coping Strategies", expanded=True):
                            for strategy in response_data["coping_strategies"]:
                                st.markdown(f"• {strategy}")
                    
                    # Crisis intervention warning
                    if response_data["requires_intervention"]:
                        st.error("🚨 **High stress detected!** Consider taking a break before making any investment decisions. Your emotional state may impact your judgment.")
                
                st.session_state.messages.append({"role": "assistant", "content": response_data["main_response"]})
    
    with tab2:
        # Portfolio Analysis Tab
        st.header("📊 Portfolio Analysis")
        
        # Create visualizations
        fig_allocation, fig_risk = create_portfolio_charts(portfolio, risk_analysis)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_allocation, use_container_width=True)
        with col2:
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Portfolio performance metrics
        st.subheader("📈 Performance Metrics")
        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
        
        with perf_col1:
            st.metric("Total Return", f"₹{portfolio['performance']['total_return']:,.2f}", 
                     f"{portfolio['performance']['total_return_percentage']:.2f}%")
        with perf_col2:
            st.metric("Today's Change", f"₹{portfolio['performance']['day_change']:,.2f}",
                     f"{portfolio['performance']['day_change_percentage']:.2f}%")
        with perf_col3:
            st.metric("YTD Change", f"₹{portfolio['performance']['ytd_change']:,.2f}")
        with perf_col4:
            st.metric("Risk Score", f"{risk_analysis['risk_score']:.1f}/10")
        
        # Holdings breakdown
        st.subheader("📋 Holdings Breakdown")
        holdings_df = pd.DataFrame([
            {
                'Symbol': h['symbol'],
                'Company': h['company_name'],
                'Shares': h['quantity'],
                'Price': f"₹{h['current_price']:.2f}",
                'Value': f"₹{h['market_value']:,.2f}",
                'P&L': f"₹{h['unrealized_gain_loss']:,.2f}",
                'Allocation': f"{h['allocation_percentage']:.1f}%",
                'Risk': h['risk_level'].title(),
                'Sector': h['sector']
            }
            for h in portfolio['holdings']
        ])
        st.dataframe(holdings_df, use_container_width=True)
    
    with tab3:
        # Investment Recommendations Tab
        st.header("💡 Investment Recommendations")
        
        # Investment amount input
        col1, col2 = st.columns([2, 1])
        with col1:
            investment_amount = st.number_input(
                "How much would you like to invest?", 
                min_value=100, 
                max_value=50000, 
                value=1000, 
                step=100,
                help="Enter the amount you want to invest for personalized recommendations"
            )
        with col2:
            if st.button("Get Recommendations", type="primary"):
                st.session_state.show_recommendations = True
        
        # Show recommendations if requested
        if hasattr(st.session_state, 'show_recommendations') and st.session_state.show_recommendations:
            with st.spinner("Generating personalized recommendations..."):
                recommendations = fi_client.get_personalized_recommendations(investment_amount)
                
                if recommendations:
                    st.success(f"Here are personalized recommendations for ₹{investment_amount:,.2f}:")
                    display_recommendations(recommendations)
                    
                    # Additional behavioral guidance
                    st.markdown("### 🧠 Behavioral Considerations")
                    behavioral = fi_client.get_behavioral_history()
                    emotional_patterns = behavioral.get('emotional_patterns', {})
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Your Investment Tendencies:**")
                        st.write(f"• FOMO Level: {emotional_patterns.get('fomo_tendency', 5)}/10")
                        st.write(f"• Loss Aversion: {emotional_patterns.get('loss_aversion_score', 5)}/10")
                        st.write(f"• Patience Level: {emotional_patterns.get('patience_level', 5)}/10")
                    
                    with col2:
                        st.markdown("**Recommended Approach:**")
                        if emotional_patterns.get('fomo_tendency', 5) > 7:
                            st.write("• Consider dollar-cost averaging to reduce FOMO impact")
                        if emotional_patterns.get('loss_aversion_score', 5) > 7:
                            st.write("• Focus on low-volatility options to reduce stress")
                        st.write("• Stick to your systematic investment plan")
                        st.write("• Review your emotional state before investing")
                else:
                    st.warning("No suitable recommendations found for this amount.")

if __name__ == "__main__":
    main()