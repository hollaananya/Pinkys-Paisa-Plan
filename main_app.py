import streamlit as st
import os
import sys
import subprocess
from pathlib import Path
import importlib.util

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="AI Financial Assistant Hub",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for the hub
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 1rem 0;
        color: white;
        transition: all 0.3s ease;
    }
    
    .agent-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.2);
    }
    
    .agent-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
        text-align: center;
    }
    
    .agent-title {
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
        color: white;
    }
    
    .agent-description {
        text-align: center;
        opacity: 0.9;
        font-size: 1rem;
        line-height: 1.4;
        color: white;
    }
    
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .feature-item {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .feature-item h4 {
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .quick-action-btn {
        width: 100%;
        margin: 0.5rem 0;
        padding: 0.75rem;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
    }
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active { background-color: #4CAF50; }
    .status-inactive { background-color: #f44336; }
</style>
""", unsafe_allow_html=True)

def load_real_data():
    """Load data from your existing JSON files"""
    data = {
        # Default values from your screenshots
        'portfolio_value': 100000.00,
        'available_cash': 5000.00,
        'todays_change': -500.00,
        'todays_change_percent': -0.50,
        'total_return': 5000.00,
        'total_return_percent': 5.26,
        'portfolio_risk_score': 5.0,
        'total_portfolio': 1500000,
        'real_estate': 0,
        'emergency_fund': 600000,
        'other_assets': 100000,
        'monthly_income': 110000,
        'monthly_expenses': 70000,
        'monthly_savings': 40000,
        'net_worth': 2200000,
        'savings_rate': 36.4,
        'debt_balance': 0,
        'retirement_progress': 42.5,
        'active_agent': None
    }
    
    # Try to load from your existing files based on actual structure
    try:
        # Investment data from investment-therapy-agent/fi_data/enhanced_user_data.json
        investment_paths = [
            "investment-therapy-agent/fi_data/enhanced_user_data.json",
            "enhanced_user_data.json"
        ]
        
        for path in investment_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    investment_data = json.load(f)
                    portfolio = investment_data.get('portfolio', {})
                    
                    data['portfolio_value'] = portfolio.get('total_market_value', data['portfolio_value'])
                    data['available_cash'] = investment_data.get('account', {}).get('available_cash', data['available_cash'])
                    data['todays_change'] = portfolio.get('day_change', data['todays_change'])
                    data['todays_change_percent'] = portfolio.get('day_change_percent', data['todays_change_percent'])
                    data['total_return'] = portfolio.get('total_return', data['total_return'])
                    data['total_return_percent'] = portfolio.get('total_return_percent', data['total_return_percent'])
                    data['net_worth'] = investment_data.get('account', {}).get('net_worth', data['net_worth'])
                break
        
        # Family financial data from fimaly_financial_planner/user_financial_data.json
        family_paths = [
            "fimaly_financial_planner/user_financial_data.json",
            "user_financial_data.json"
        ]
        
        for path in family_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    family_data = json.load(f)
                    
                    snapshot = family_data.get('financial_snapshot', {})
                    income = family_data.get('income', {})
                    expenses = family_data.get('expenses', {})
                    
                    data['total_portfolio'] = snapshot.get('portfolio_value', data['total_portfolio'])
                    data['emergency_fund'] = snapshot.get('emergency_fund', data['emergency_fund'])
                    data['other_assets'] = snapshot.get('other_assets', data['other_assets'])
                    data['monthly_income'] = income.get('total_monthly_income', data['monthly_income'])
                    data['monthly_expenses'] = expenses.get('total_monthly_expenses', data['monthly_expenses'])
                    data['monthly_savings'] = data['monthly_income'] - data['monthly_expenses']
                    data['savings_rate'] = (data['monthly_savings'] / data['monthly_income']) * 100 if data['monthly_income'] > 0 else 0
                break
        
        # Tax data from TaxGenomeAgent/fi_data/user_tax_data.json
        tax_paths = [
            "TaxGenomeAgent/fi_data/user_tax_data.json",
            "TaxGenomeAgent/user_tax_data.json",
            "user_tax_data.json"
        ]
        
        for path in tax_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    tax_data = json.load(f)
                    income_data = tax_data.get('income', {})
                    if 'annual_salary' in income_data:
                        annual_salary = income_data['annual_salary']
                        data['monthly_income'] = annual_salary / 12
                        data['monthly_savings'] = data['monthly_income'] - data['monthly_expenses']
                        data['savings_rate'] = (data['monthly_savings'] / data['monthly_income']) * 100
                break
        
        # Time machine data
        time_paths = [
            "time-machine-agent/time_machine_user_data.json",
            "time_machine_user_data.json"
        ]
        
        for path in time_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    time_data = json.load(f)
                    time_portfolio = time_data.get('portfolio', {})
                    time_income = time_data.get('income', {})
                    
                    if time_portfolio.get('total_market_value'):
                        data['total_portfolio'] = time_portfolio['total_market_value']
                    if time_income.get('monthly_salary'):
                        data['monthly_income'] = time_income['monthly_salary']
                break
        
    except Exception as e:
        # If any error occurs, use default values
        pass
    
    return data

# Initialize session state with real data
if 'user_data' not in st.session_state:
    st.session_state.user_data = load_real_data()

# Agent configurations based on your EXACT file structure
AGENTS = {
    'family_planner': {
        'title': 'Family Financial Planner',
        'icon': '👨‍👩‍👧‍👦💰',
        'description': 'Comprehensive family financial planning with goal coordination and household budgeting',
        'features': ['Family Goals', 'Budget Coordination', 'Kids Planning', 'Emergency Fund'],
        'app_file': 'fimaly_financial_planner/family_financial_planner.py',
        'folder': 'fimaly_financial_planner',
        'color': '#f093fb',
        'port': 8501,
        'status': 'available'
    },
    'investment_therapy': {
        'title': 'Investment Therapy Agent',
        'icon': '🧠💰',
        'description': 'Emotionally intelligent investment coaching with behavioral analysis and personalized recommendations',
        'features': ['Behavioral Analysis', 'Market Timing', 'Emotional Support', 'Risk Assessment'],
        'app_file': 'investment-therapy-agent/app.py',
        'folder': 'investment-therapy-agent',
        'color': '#667eea',
        'port': 8502,
        'status': 'available'
    },
    'tax_genome': {
        'title': 'Tax Genome Agent',
        'icon': '📊🧬',
        'description': 'Advanced tax optimization and strategic planning with genomic-level analysis',
        'features': ['Tax Optimization', 'Deduction Mining', 'Strategy Planning', 'Compliance'],
        'app_file': 'TaxGenomeAgent/app.py',
        'folder': 'TaxGenomeAgent',
        'color': '#4facfe',
        'port': 8503,
        'status': 'available'
    },
    'time_machine': {
        'title': 'Time Machine Agent',
        'icon': '⏰🔮',
        'description': 'Future scenario modeling and what-if analysis for financial planning',
        'features': ['Scenario Modeling', 'Future Projections', 'What-If Analysis', 'Risk Planning'],
        'app_file': 'time-machine-agent/app.py',
        'folder': 'time-machine-agent',
        'color': '#43e97b',
        'port': 8504,
        'status': 'available'
    }
}

def check_agent_status(agent_key):
    """Check if agent files exist and are accessible - improved detection"""
    agent_config = AGENTS[agent_key]
    app_path = Path(agent_config['app_file'])
    folder_path = Path(agent_config['folder'])
    
    # Check if both folder and app file exist
    folder_exists = folder_path.exists() and folder_path.is_dir()
    app_exists = app_path.exists() and app_path.is_file()
    
    if app_exists and folder_exists:
        # Additional check: see if it's a valid Python file
        try:
            with open(app_path, 'r') as f:
                content = f.read()
                if 'streamlit' in content and ('def main' in content or 'st.' in content):
                    return 'available'
                else:
                    return 'needs_setup'
        except:
            return 'needs_setup'
    elif folder_exists:
        return 'needs_setup'
    else:
        return 'missing'

def launch_agent_in_new_tab(agent_key):
    """Launch agent in a new browser tab using subprocess with better error handling"""
    agent_config = AGENTS[agent_key]
    app_path = agent_config['app_file']
    port = agent_config['port']
    
    try:
        # Check if the app file exists
        if not os.path.exists(app_path):
            st.error(f"❌ Agent file not found: {app_path}")
            st.info("Please check that your agent files are in the correct locations.")
            return False
        
        # Check if port is already in use
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            # Port is already in use
            agent_url = f"http://localhost:{port}"
            st.warning(f"⚠️ {agent_config['title']} may already be running")
            st.markdown(f"**Try this URL:** [Open {agent_config['title']}]({agent_url})")
            return True
        
        # Launch Streamlit app in background
        cmd = [
            "streamlit", "run", app_path,
            "--server.port", str(port),
            "--server.headless", "true",
            "--server.address", "localhost"
        ]
        
        # Start the process
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            cwd=os.getcwd()  # Set working directory
        )
        
        # Wait a moment for startup
        import time
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            # Generate the URL
            agent_url = f"http://localhost:{port}"
            
            st.success(f"🚀 {agent_config['title']} launched successfully!")
            st.markdown(f"**Click to open:** [Open {agent_config['title']}]({agent_url})")
            st.code(f"Direct URL: {agent_url}")
            
            # Store process info in session state for tracking
            if 'running_agents' not in st.session_state:
                st.session_state.running_agents = {}
            st.session_state.running_agents[agent_key] = {
                'process': process,
                'port': port,
                'url': agent_url
            }
            
            return True
        else:
            st.error(f"❌ Failed to start {agent_config['title']}")
            st.info("The agent may have startup issues. Try running it individually first.")
            return False
        
    except FileNotFoundError:
        st.error("❌ Streamlit not found. Please install streamlit: `pip install streamlit`")
        return False
    except Exception as e:
        st.error(f"❌ Error launching {agent_config['title']}: {str(e)}")
        st.info("Try running the agent individually to debug the issue.")
        return False

def render_agent_card(agent_key, agent_config):
    """Render an agent selection card"""
    status = check_agent_status(agent_key)
    
    # Determine card color based on status
    if status == 'available':
        gradient = f"linear-gradient(135deg, {agent_config['color']} 0%, {agent_config['color']}CC 100%)"
        status_color = "status-active"
        status_text = "Ready"
    elif status == 'needs_setup':
        gradient = "linear-gradient(135deg, #ff9800 0%, #ff9800CC 100%)"
        status_color = "status-inactive"
        status_text = "Setup Required"
    else:
        gradient = "linear-gradient(135deg, #9e9e9e 0%, #9e9e9eCC 100%)"
        status_color = "status-inactive"
        status_text = "Not Found"
    
    st.markdown(f"""
    <div class="agent-card" style="background: {gradient};">
        <div class="agent-icon">{agent_config['icon']}</div>
        <div class="agent-title">{agent_config['title']}</div>
        <div class="agent-description">{agent_config['description']}</div>
        <div style="margin-top: 1rem; text-align: center;">
            <span class="status-indicator {status_color}"></span>
            <small>{status_text}</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if status == 'available':
            if st.button(f"🚀 Launch {agent_config['title']}", key=f"launch_{agent_key}", type="primary"):
                launch_agent_in_new_tab(agent_key)
        else:
            st.button(f"❌ Unavailable", key=f"unavailable_{agent_key}", disabled=True)
    
    with col2:
        if st.button(f"ℹ️ Info", key=f"info_{agent_key}"):
            with st.expander(f"📋 {agent_config['title']} Details", expanded=True):
                st.markdown(f"**File:** `{agent_config['app_file']}`")
                st.markdown(f"**Port:** `{agent_config['port']}`")
                st.markdown(f"**Status:** {status_text}")
                st.markdown("**Features:**")
                for feature in agent_config['features']:
                    st.markdown(f"• {feature}")

def format_inr(amount):
    """Format amount in Indian Rupee style with ₹ symbol"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} L"
    elif amount >= 1000:    # thousands
        return f"₹{amount/1000:.0f}K"
    else:
        return f"₹{amount:,.0f}"

def render_dashboard():
    """Render the main dashboard with Indian financial data"""
    st.markdown('<h1 class="main-header">🏦 AI Financial Assistant Hub</h1>', unsafe_allow_html=True)
    
    # Investment Profile Section
    st.markdown("## 📊 Your Investment Profile")
    
    # First row - Investment metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value">{format_inr(st.session_state.user_data['portfolio_value'])}</div>
            <div class="metric-label">Portfolio Value</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        change_color = "#f44336" if st.session_state.user_data['todays_change'] < 0 else "#4CAF50"
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value" style="color: {change_color}">{format_inr(st.session_state.user_data['todays_change'])}</div>
            <div class="metric-label">Today's Change ({st.session_state.user_data['todays_change_percent']:.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value" style="color: #4CAF50">{format_inr(st.session_state.user_data['total_return'])}</div>
            <div class="metric-label">Total Return ({st.session_state.user_data['total_return_percent']:.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        risk_color = "#ff9800" if st.session_state.user_data['portfolio_risk_score'] > 6 else "#4CAF50"
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value" style="color: {risk_color}">{st.session_state.user_data['portfolio_risk_score']:.1f}/10</div>
            <div class="metric-label">Risk Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Second row - Financial Snapshot
    st.markdown("## 💰 Current Financial Snapshot")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value">{format_inr(st.session_state.user_data['total_portfolio'])}</div>
            <div class="metric-label">Total Portfolio</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value">{format_inr(st.session_state.user_data['emergency_fund'])}</div>
            <div class="metric-label">Emergency Fund</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value">{format_inr(st.session_state.user_data['net_worth'])}</div>
            <div class="metric-label">Net Worth</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value">{format_inr(st.session_state.user_data['monthly_savings'])}</div>
            <div class="metric-label">Monthly Savings</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Third row - Cash Flow
    st.markdown("## 💸 Monthly Cash Flow")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value" style="color: #4CAF50">{format_inr(st.session_state.user_data['monthly_income'])}</div>
            <div class="metric-label">Monthly Income</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value" style="color: #f44336">{format_inr(st.session_state.user_data['monthly_expenses'])}</div>
            <div class="metric-label">Monthly Expenses</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <div class="metric-value" style="color: #667eea">{st.session_state.user_data['savings_rate']:.1f}%</div>
            <div class="metric-label">Savings Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Agent selection grid
    st.markdown("## 🤖 Choose Your AI Financial Assistant")
    st.markdown("Click 'Launch' to open any agent in a new browser tab:")
    
    # Create 2x2 grid for agents
    col1, col2 = st.columns(2)
    
    agent_keys = list(AGENTS.keys())
    
    with col1:
        # Investment Therapy Agent
        if len(agent_keys) > 0:
            render_agent_card(agent_keys[0], AGENTS[agent_keys[0]])
        
        # Tax Genome Agent
        if len(agent_keys) > 2:
            render_agent_card(agent_keys[2], AGENTS[agent_keys[2]])
    
    with col2:
        # Family Planner
        if len(agent_keys) > 1:
            render_agent_card(agent_keys[1], AGENTS[agent_keys[1]])
        
        # Time Machine Agent
        if len(agent_keys) > 3:
            render_agent_card(agent_keys[3], AGENTS[agent_keys[3]])
    
    # Platform features
    st.markdown("---")
    st.markdown("## ✨ Platform Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-item">
            <h4>🧠 Multi-Agent Intelligence</h4>
            <p>Specialized AI agents for different financial domains working together</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-item">
            <h4>🔄 Seamless Integration</h4>
            <p>Launch any agent in a new tab while maintaining your hub session</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-item">
            <h4>📊 Unified Dashboard</h4>
            <p>Central control panel for all your financial AI assistants</p>
        </div>
        """, unsafe_allow_html=True)

def render_sidebar():
    """Render sidebar with navigation and utilities"""
    with st.sidebar:
        st.markdown("### 🏠 Control Panel")
        
        # Quick launch buttons
        st.markdown("#### ⚡ Quick Launch")
        
        for agent_key, agent_config in AGENTS.items():
            status = check_agent_status(agent_key)
            if status == 'available':
                if st.button(f"{agent_config['icon']} {agent_config['title']}", key=f"quick_{agent_key}"):
                    launch_agent_in_new_tab(agent_key)
            else:
                st.button(f"❌ {agent_config['title']}", key=f"quick_disabled_{agent_key}", disabled=True)
        
        st.markdown("---")
        
        # System status with better diagnostics
        st.markdown("#### 🔍 System Status")
        
        total_agents = len(AGENTS)
        available_agents = sum(1 for key in AGENTS.keys() if check_agent_status(key) == 'available')
        
        st.metric("Available Agents", f"{available_agents}/{total_agents}")
        
        # Show running agents
        if 'running_agents' in st.session_state and st.session_state.running_agents:
            st.markdown("**🟢 Currently Running:**")
            for agent_key, info in st.session_state.running_agents.items():
                agent_name = AGENTS[agent_key]['title']
                st.markdown(f"• {agent_name} - [Open](http://localhost:{info['port']})")
        
        # Agent status details
        with st.expander("Agent Status Details"):
            for agent_key, agent_config in AGENTS.items():
                status = check_agent_status(agent_key)
                if status == 'available':
                    status_emoji = "✅"
                    status_text = "Ready to launch"
                elif status == 'needs_setup':
                    status_emoji = "⚠️" 
                    status_text = "Found but needs setup"
                else:
                    status_emoji = "❌"
                    status_text = "Not found"
                
                st.markdown(f"{status_emoji} **{agent_config['title']}**: {status_text}")
                st.markdown(f"   📁 Expected: `{agent_config['app_file']}`")
        
        # Data file status based on your actual structure
        with st.expander("Data Files Status"):
            data_files = {
                "Investment Data": "investment-therapy-agent/fi_data/enhanced_user_data.json",
                "Family Data": "fimaly_financial_planner/user_financial_data.json", 
                "Tax Data": "TaxGenomeAgent/fi_data/user_tax_data.json",
                "Alt Family Data": "fimaly_financial_planner/user_family.json",
                "Conversation History": "conversation_history.json"
            }
            
            for name, path in data_files.items():
                exists = "✅" if os.path.exists(path) else "❌"
                st.markdown(f"{exists} {name}")
                if not os.path.exists(path):
                    st.markdown(f"   📁 Expected: `{path}`")
                    
            # Show files that DO exist in your structure
            st.markdown("**Found Files:**")
            found_files = []
            check_paths = [
                "fimaly_financial_planner/user_financial_data.json",
                "TaxGenomeAgent/fi_data/user_tax_data.json",
                "investment-therapy-agent/fi_data/enhanced_user_data.json",
                "conversation_history.json"
            ]
            
            for path in check_paths:
                if os.path.exists(path):
                    found_files.append(f"✅ {path}")
            
            if found_files:
                for file in found_files:
                    st.markdown(f"  {file}")
            else:
                st.markdown("  No data files found - using screenshot defaults")
        
        st.markdown("---")
        
        # User profile summary
        st.markdown("#### 👤 Your Profile")
        user_data = st.session_state.user_data
        
        # Key metrics in Indian format
        net_worth = user_data['net_worth']
        monthly_surplus = user_data['monthly_income'] - user_data['monthly_expenses']
        
        st.metric("Net Worth", format_inr(net_worth))
        st.metric("Monthly Surplus", format_inr(monthly_surplus))
        st.metric("Available Cash", format_inr(user_data['available_cash']))
        
        # Progress bars
        st.markdown("**Savings Rate**")
        savings_rate_decimal = min(user_data['savings_rate'] / 100, 1.0)
        st.progress(savings_rate_decimal)
        st.text(f"{user_data['savings_rate']:.1f}%")
        
        st.markdown("**Investment vs Emergency Fund**")
        total_liquid = user_data['portfolio_value'] + user_data['emergency_fund']
        if total_liquid > 0:
            investment_ratio = user_data['portfolio_value'] / total_liquid
            st.progress(investment_ratio)
            st.text(f"Investment: {investment_ratio*100:.1f}%")
        
        # Risk profile
        st.markdown("**Portfolio Risk**")
        risk_percentage = user_data['portfolio_risk_score'] / 10
        st.progress(risk_percentage)
        st.text(f"Risk Score: {user_data['portfolio_risk_score']:.1f}/10")
        
        st.markdown("---")
        
        # Asset breakdown
        st.markdown("#### 🏠 Asset Breakdown")
        total_assets = user_data['total_portfolio'] + user_data['emergency_fund'] + user_data['other_assets']
        
        if total_assets > 0:
            portfolio_pct = (user_data['total_portfolio'] / total_assets) * 100
            emergency_pct = (user_data['emergency_fund'] / total_assets) * 100
            other_pct = (user_data['other_assets'] / total_assets) * 100
            
            st.markdown(f"**Portfolio:** {format_inr(user_data['total_portfolio'])} ({portfolio_pct:.1f}%)")
            st.markdown(f"**Emergency Fund:** {format_inr(user_data['emergency_fund'])} ({emergency_pct:.1f}%)")
            st.markdown(f"**Other Assets:** {format_inr(user_data['other_assets'])} ({other_pct:.1f}%)")
        
        st.markdown("---")
        
        # Monthly cash flow summary
        st.markdown("#### 💸 Monthly Flow")
        st.markdown(f"**Income:** {format_inr(user_data['monthly_income'])}")
        st.markdown(f"**Expenses:** {format_inr(user_data['monthly_expenses'])}")
        st.markdown(f"**Savings:** {format_inr(user_data['monthly_savings'])}")
        st.markdown(f"**Rate:** {user_data['savings_rate']:.1f}%")
        
        st.markdown("---")
        
        # Utilities with better functionality
        st.markdown("#### 🛠️ Utilities")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Status"):
                # Clear cached data and rerun
                if 'user_data' in st.session_state:
                    st.session_state.user_data = load_real_data()
                st.rerun()
        
        with col2:
            if st.button("🌐 Show URLs"):
                st.markdown("**Agent URLs:**")
                for agent_key, agent_config in AGENTS.items():
                    if check_agent_status(agent_key) == 'available':
                        url = f"http://localhost:{agent_config['port']}"
                        st.code(f"{agent_config['title']}: {url}")
        
        # Stop running agents
        if 'running_agents' in st.session_state and st.session_state.running_agents:
            if st.button("🛑 Stop All Agents"):
                stopped_count = 0
                for agent_key, info in list(st.session_state.running_agents.items()):
                    try:
                        info['process'].terminate()
                        stopped_count += 1
                    except:
                        pass
                st.session_state.running_agents.clear()
                st.success(f"Stopped {stopped_count} agents")
                st.rerun()
        
        # Environment info
        with st.expander("Environment Info"):
            st.markdown(f"**Python:** {sys.version.split()[0]}")
            st.markdown(f"**Streamlit:** {st.__version__}")
            st.markdown(f"**Working Dir:** {os.getcwd()}")
            st.markdown(f"**Platform:** {sys.platform}")
            
            # Show current data sources based on actual file structure
            st.markdown("**Data loaded from:**")
            data_sources = []
            check_files = [
                "investment-therapy-agent/fi_data/enhanced_user_data.json",
                "fimaly_financial_planner/user_financial_data.json", 
                "TaxGenomeAgent/fi_data/user_tax_data.json",
                "conversation_history.json"
            ]
            
            for path in check_files:
                if os.path.exists(path):
                    data_sources.append(f"✅ {path}")
                else:
                    data_sources.append(f"❌ {path} (using defaults)")
            
            for source in data_sources:
                st.markdown(f"  {source}")

def main():
    """Main application entry point"""
    render_sidebar()
    render_dashboard()
    
    # Instructions at the bottom
    st.markdown("---")
    st.markdown("## 📖 How to Use")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 Launching Agents
        1. **Check Status**: Green dot = Ready to launch
        2. **Click Launch**: Opens agent in new browser tab
        3. **Use Both**: Keep this hub open while using agents
        4. **Quick Access**: Use sidebar for fast launching
        """)
    
    with col2:
        st.markdown("""
        ### 🔧 Troubleshooting
        - **Red Status**: Check if agent files exist
        - **Port Issues**: Each agent uses different ports
        - **Refresh**: Use refresh button to update status
        - **Multiple Tabs**: Each agent runs independently
        """)

if __name__ == "__main__":
    main()