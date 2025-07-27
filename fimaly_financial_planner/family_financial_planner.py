import streamlit as st
import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, List, Any

# Load environment variables from a .env file
load_dotenv()

# --- Helper Classes (Combined from your files) ---

class FiMCPClient:
    """
    A client to simulate fetching financial data. In a real application,
    this would connect to a database or API. For this example, it reads
    from a local JSON file.
    """
    def __init__(self, fi_data_file: str = "user_financial_data.json"):
        self.fi_data_file = fi_data_file
        self.fi_data = None
        self.is_loaded = False
        self._load_fi_data()

    def _load_fi_data(self):
        """
        Loads financial data from the JSON file.
        If the file doesn't exist, it sets the client to an unloaded state.
        The UI will handle guiding the user.
        """
        if not os.path.exists(self.fi_data_file):
            # The file is optional. The app will run, and the UI will adapt.
            self.is_loaded = False
            return

        try:
            with open(self.fi_data_file, 'r') as f:
                self.fi_data = json.load(f)
            self.is_loaded = True
        except Exception as e:
            st.error(f"Error loading financial data from '{self.fi_data_file}': {e}")
            self.is_loaded = False

    def get_portfolio_data(self) -> Dict[str, Any]:
        """Gets portfolio data."""
        if not self.is_loaded: return {}
        return self.fi_data.get('portfolio', {})

    def get_account_summary(self) -> Dict[str, Any]:
        """Gets user account and profile summary."""
        if not self.is_loaded: return {}
        summary = self.fi_data.get('account', {})
        summary.update(self.fi_data.get('user_profile', {}))
        return summary

    def get_market_data(self) -> Dict[str, Any]:
        """Gets market context data."""
        if not self.is_loaded: return {}
        return self.fi_data.get('market_data', {})


class FamilyFinancialPlanner:
    """
    The agent for providing family financial advice. It uses the Gemini API
    and maintains conversation history and family context.
    """
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            st.error("Missing GEMINI_API_KEY in your environment variables.")
            raise ValueError("Missing GEMINI_API_KEY")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        # File paths for storing state
        self.history_file = "conversation_history.json"
        self.family_data_file = "user_family.json"
        self.user_data_file = "user_financial_data.json"

        # Load data, creating files if they don't exist
        self.conversation_history = self._load_json(self.history_file, default=[])
        self.family_data = self._load_json(self.family_data_file, default={})
        self.user_data = self._load_json(self.user_data_file, default={})

        # --- REVAMPED SYSTEM PROMPT ---
        self.system_prompt = """
        You are an expert Family Financial Planning Assistant. Your persona is that of a wise, empathetic, and knowledgeable guide. You educate users about their options, model scenarios, and help them think through decisions. You are patient and an excellent listener.

        **CORE DIRECTIVES:**
        1.  **Empathy and Acknowledgment:** Always start your response by acknowledging the user's situation and emotions. Family finance is stressful; show that you understand.
        2.  **Educate, Don't Prescribe:** Your goal is to explain concepts, pros, cons, and trade-offs. Use analogies and simple language.
        3.  **Provide Concrete, Actionable Information:** Give real numbers, estimates, and options based on the data you have.
        4.  **Ask Clarifying Questions:** Ask one simple, focused question at a time to gather the information you need to provide better guidance.
        5.  **Use the `set_jsonfamily` function:** When the user provides critical, long-term information (like income, number of children, retirement age), use the `set_jsonfamily({...})` function at the very end of your response to remember it. Do not mention this function to the user.

        **CONVERSATIONAL EXAMPLES (Follow these patterns):**

        **Scenario 1: College Savings**
        *User:* "My daughter is in 8th grade, how should I think about saving for college? I'm so stressed about it."
        *Your Ideal Response:* "It's completely understandable to feel stressed about college costs—it's a huge goal, and you're smart to be thinking about it now. Let's break it down.

        Based on your moderate-aggressive risk profile, a great tool for this is a 529 plan, which allows your investments to grow tax-free for education. Given your daughter is in 8th grade, you have about 4-5 years of solid growth potential. For a good state school like a UC, the total cost could be around ₹35,000-₹40,000 per year in today's dollars.

        To start, could you tell me if you have any existing savings set aside for her education? set_jsonfamily({\"children\": [{\"grade\": 8, \"gender\": \"female\", \"goal\": \"college\"}]})"

        **Scenario 2: Buying a House**
        *User:* "We want to buy a house in a few years. We make about ₹150,000 combined."
        *Your Ideal Response:* "That's a fantastic goal! Buying a home is a major milestone. I can help you understand what might be possible.

        A general rule of thumb for affordability is a home price of about 3-4 times your annual income, so in your case, that's roughly in the ₹450,000 to ₹600,000 range. For a ₹500,000 home, a 20% down payment would be ₹100,000. This is the ideal to avoid Private Mortgage Insurance (PMI), but many people start with less.

        What is your approximate timeline for buying a home? Knowing that will help us think about savings strategies. set_jsonfamily({\"household_income\": 150000, \"financial_goals\": {\"housing\": {\"type\": \"purchase\"}}})"
        
        **Scenario 3: General "Am I doing okay?"**
        *User:* "I just feel like I'm behind on my finances."
        *Your Ideal Response:* "It's very common to feel that way, and it's great that you're taking a moment to check in on your progress. Let's look at the data together.

        Your portfolio has a total return of 13.65%, which is a very solid result. It shows your long-term strategy is working. A key metric for retirement is saving at least 15% of your income. While I don't know your income yet, we can explore if you're on track.

        To get a clearer picture, could you share what your biggest financial worry is right now?"
        """

    def _load_json(self, file_path: str, default: Any) -> Any:
        """Loads data from a JSON file, creating it with a default value if it doesn't exist."""
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default, f, indent=2)
            return default
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default

    def _save_json(self, file_path: str, data: Any):
        """Saves data to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _update_family_data(self, new_data_str: str):
        """Updates family data based on the model's function call."""
        try:
            match = re.search(r'set_jsonfamily\((.*)\)', new_data_str, re.DOTALL)
            if match:
                json_str = match.group(1)
                new_data = json.loads(json_str)
                # Deep merge logic
                stack = [(self.family_data, new_data)]
                while stack:
                    d, u = stack.pop()
                    for k, v in u.items():
                        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                            stack.append((d[k], v))
                        else:
                            d[k] = v
                self._save_json(self.family_data_file, self.family_data)
        except Exception as e:
            print(f"Error updating family data: {e}") # Log for debugging

    def _process_response(self, response_text: str) -> str:
        """Processes the response to handle function calls and returns the clean text for display."""
        if "set_jsonfamily" in response_text:
            clean_response = re.sub(r'\s*set_jsonfamily\(.*\)\s*₹', '', response_text, flags=re.DOTALL)
            self._update_family_data(response_text)
            return clean_response.strip()
        return response_text.strip()

    def process_query(self, user_query: str) -> str:
        """Processes a user query using the Gemini API and manages state."""
        self.conversation_history.append({"role": "user", "content": user_query})

        financial_context = json.dumps(self.user_data, indent=2)
        family_context = json.dumps(self.family_data, indent=2)
        history_formatted = "\n".join([f"{entry['role']}: {entry['content']}" for entry in self.conversation_history])

        full_prompt = f"{self.system_prompt}\n\nUSER FINANCIAL DATA:\n{financial_context}\n\nUSER FAMILY CONTEXT:\n{family_context}\n\nCONVERSATION HISTORY:\n{history_formatted}\n\nCurrent user query: {user_query}"

        try:
            response = self.model.generate_content(full_prompt)
            assistant_response = self._process_response(response.text)
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            self._save_json(self.history_file, self.conversation_history)
            return assistant_response
        except Exception as e:
            error_message = f"Sorry, I encountered an error: {str(e)}"
            self.conversation_history.append({"role": "assistant", "content": error_message})
            self._save_json(self.history_file, self.conversation_history)
            return error_message


# --- Streamlit App ---

# Page config
st.set_page_config(
    page_title="Family Financial Planner",
    page_icon="👨‍👩‍👧‍👦💰",
    layout="wide"
)

# Custom CSS to match the other models
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
.holding-item {
    background: #f8f9fa;
    padding: 0.8rem;
    border-radius: 8px;
    margin: 0.3rem 0;
    border-left: 4px solid #667eea;
}
</style>
""", unsafe_allow_html=True)

# Initialize clients (cached for performance)
@st.cache_resource
def init_clients():
    """Initializes the financial client and the planning agent."""
    fi_client = FiMCPClient()
    planner = FamilyFinancialPlanner()
    return fi_client, planner

def main():
    """Main function to run the Streamlit application."""
    # Header
    st.markdown('<h1 class="main-header">👨‍👩‍👧‍👦💰 Family Financial Planner</h1>', unsafe_allow_html=True)
    st.subheader("Your AI-Powered Guide to Family Finances")

    # Initialize
    try:
        fi_client, planner = init_clients()
    except ValueError as e:
        st.stop() # Stop the app if initialization fails (e.g., missing API key)

    # Sidebar - Portfolio Overview (to match the other model's look)
    with st.sidebar:
        st.header("📊 Your Financial Snapshot")
        
        if fi_client.is_loaded:
            portfolio = fi_client.get_portfolio_data()
            account_profile = fi_client.get_account_summary()
            
            # Key metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Value", f"₹{portfolio.get('total_market_value', 0):,.2f}")
                st.metric("Cash Balance", f"₹{portfolio.get('cash_balance', 0):,.2f}")
            with col2:
                day_change = portfolio.get('day_change', 0)
                change_color = "normal" if day_change >= 0 else "inverse"
                st.metric("Today's Change",
                         f"₹{day_change:,.2f}",
                         f"{portfolio.get('day_change_percent', 0):.2f}%",
                         delta_color=change_color)
                st.metric("Total Return",
                         f"₹{portfolio.get('total_return', 0):,.2f}",
                         f"{portfolio.get('total_return_percent', 0):.2f}%")

            # User profile
            st.subheader("👤 Your Profile")
            st.write(f"**Risk Tolerance:** {account_profile.get('risk_tolerance', 'N/A').replace('_', ' ').title()}")
            st.write(f"**Experience:** {account_profile.get('investment_experience', 'N/A').title()}")
            st.write(f"**Time Horizon:** {account_profile.get('time_horizon', 'N/A')}")

            # Top holdings
            st.subheader("🏢 Top Holdings")
            holdings = portfolio.get('holdings', [])
            if not holdings:
                st.write("No holdings data available.")
            for holding in holdings[:3]:
                gain_loss = holding.get('unrealized_pnl', 0)
                gain_color = "green" if gain_loss >= 0 else "red"
                st.markdown(f"""
                <div class="holding-item">
                    <strong>{holding.get('symbol', 'N/A')}</strong> ({holding.get('allocation_percent', 0):.1f}%)<br>
                    <span style='color: {gain_color}'>₹{gain_loss:,.2f}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("To personalize your experience, create a `user_financial_data.json` file in this directory. The app will display your financial snapshot here.")

    # Main Chat Interface
    if "messages" not in st.session_state:
        welcome_msg = """Hi! I'm your Family Financial Planning assistant. I can help you think through big life decisions like saving for college, buying a house, or planning for retirement. 

What financial goal is on your mind today?"""
        st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about college, housing, retirement, etc."):
        # Add and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking about your family's finances..."):
                response = planner.process_query(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
