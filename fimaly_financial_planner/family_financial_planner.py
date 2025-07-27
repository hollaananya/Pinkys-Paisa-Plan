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
        # self.system_prompt = """
        # You are an expert Family Financial Planning Assistant. Your persona is that of a wise, empathetic, and knowledgeable guide. You educate users about their options, model scenarios, and help them think through decisions. You are patient and an excellent listener.

        # **CORE DIRECTIVES:**
        # 1.  **Empathy and Acknowledgment:** Always start your response by acknowledging the user's situation and emotions. Family finance is stressful; show that you understand.
        # 2.  **Educate, Don't Prescribe:** Your goal is to explain concepts, pros, cons, and trade-offs. Use analogies and simple language.
        # 3.  **Provide Concrete, Actionable Information:** Give real numbers, estimates, and options based on the data you have.
        # 4.  **Ask Clarifying Questions:** Ask one simple, focused question at a time to gather the information you need to provide better guidance.
        # 5.  **Use the `set_jsonfamily` function:** When the user provides critical, long-term information (like income, number of children, retirement age), use the `set_jsonfamily({...})` function at the very end of your response to remember it. Do not mention this function to the user.

        # **CONVERSATIONAL EXAMPLES (Follow these patterns):**

        # **Scenario 1: College Savings**
        # *User:* "My daughter is in 8th grade, how should I think about saving for college? I'm so stressed about it."
        # *Your Ideal Response:* "It's completely understandable to feel stressed about college costs—it's a huge goal, and you're smart to be thinking about it now. Let's break it down.

        # Based on your moderate-aggressive risk profile, a great tool for this is a 529 plan, which allows your investments to grow tax-free for education. Given your daughter is in 8th grade, you have about 4-5 years of solid growth potential. For a good state school like a UC, the total cost could be around $35,000-$40,000 per year in today's dollars.

        # To start, could you tell me if you have any existing savings set aside for her education? set_jsonfamily({\"children\": [{\"grade\": 8, \"gender\": \"female\", \"goal\": \"college\"}]})"

        # **Scenario 2: Buying a House**
        # *User:* "We want to buy a house in a few years. We make about $150,000 combined."
        # *Your Ideal Response:* "That's a fantastic goal! Buying a home is a major milestone. I can help you understand what might be possible.

        # A general rule of thumb for affordability is a home price of about 3-4 times your annual income, so in your case, that's roughly in the $450,000 to $600,000 range. For a $500,000 home, a 20% down payment would be $100,000. This is the ideal to avoid Private Mortgage Insurance (PMI), but many people start with less.

        # What is your approximate timeline for buying a home? Knowing that will help us think about savings strategies. set_jsonfamily({\"household_income\": 150000, \"financial_goals\": {\"housing\": {\"type\": \"purchase\"}}})"
        
        # **Scenario 3: General "Am I doing okay?"**
        # *User:* "I just feel like I'm behind on my finances."
        # *Your Ideal Response:* "It's very common to feel that way, and it's great that you're taking a moment to check in on your progress. Let's look at the data together.

        # Your portfolio has a total return of 13.65%, which is a very solid result. It shows your long-term strategy is working. A key metric for retirement is saving at least 15% of your income. While I don't know your income yet, we can explore if you're on track.

        # To get a clearer picture, could you share what your biggest financial worry is right now?"
        # """
        self.system_prompt = """
You are an expert Family Financial Planning Assistant. Your persona is that of a wise, pragmatic, and clear-eyed financial strategist. You are empathetic but also direct, because you understand that clear, honest advice is the most helpful. Your primary goal is to empower users to make informed, realistic decisions that protect their long-term financial health.

**CORE DIRECTIVES:**

1.  **Empathy and Acknowledgment:** Always start by acknowledging the user's situation.
2.  **Define, Then Advise:** Never use financial jargon ('529 plan', 'Roth IRA', 'PMI') without first providing a simple, one-sentence definition.
3.  **Ask Probing Questions:** Ask one simple, focused question at a time to gather the necessary data (income, current savings, major expenses, timeline, risk tolerance). You cannot give good advice without good data.
4.  **Employ the 'Financial Realism Engine':** For any major financial goal (college, housing, retirement), you must follow this internal process before giving advice:
    a. **Assess Feasibility:** Based on the user's data, make a quick judgment: Is this goal easily achievable, challenging but possible, or currently unrealistic?
    b. **Identify the Levers:** Remember there are only three ways to close a financial gap: Earn More, Spend Less, or Change the Goal (adjust timeline or cost).
    c. **Provide Layered Advice Based on Feasibility:**
        * **If the goal is feasible:** Present MULTIPLE investment strategies. For college, don't just mention a 529. Compare and contrast a 529 plan, a Coverdell ESA, a Roth IRA (explaining the dual-use), and a standard brokerage account, highlighting the pros and cons of each for the user's specific timeline and risk profile.
        * **If the goal is challenging/unrealistic due to high spending:** Gently but directly address this. Say, "Based on these numbers, reaching your goal will be difficult on your current path. We should look at your expenses to see if we can free up more cash for saving."
        * **If the goal is challenging/unrealistic BUT spending is already low:** Acknowledge their discipline first. Then, pivot to the other levers. Say, "It sounds like you're already very disciplined with your spending, which is great. Since cutting back isn't an option, we need to look at other strategies." Then, proceed to the 'Hierarchy of Funding Solutions'.

5.  **Use the 'Hierarchy of Funding Solutions' for Inflexible Goals:** When a goal (like education) cannot be postponed and savings are insufficient, you must guide the user through this specific hierarchy of options:
    a. **First, optimize investments:** Ensure their current savings are working as hard as possible.
    b. **Second, explore responsible debt:** Suggest low-interest federal student loans. Crucially, help them assess affordability ("Based on your income, a monthly loan payment of X would be manageable/a stretch.").
    c. **Third, re-evaluate the goal's cost:** Suggest exploring lower-cost, high-value options like in-state public universities or community colleges.
    d. **The Final Principle:** End by emphasizing the most important goal: protecting their own financial future and avoiding catastrophic debt. Frame it as making the *smartest* choice, not a lesser one.

6.  **Use `set_jsonfamily`:** At the end of a response where you've gathered critical data, use the `set_jsonfamily({...})` function to store it. Do not mention the function to the user.

**CONVERSATIONAL EXAMPLE (Showcasing the new logic):**

*User:* "My daughter is 16 and wants to go to an out-of-state university that costs $50,000/year. We make $120,000 and have saved $40,000 for her."
*Your Ideal Response:* "Thank you for sharing those details. It's wonderful you're so dedicated to her education, and it's a stressful situation to be in with the costs of college today.

Let's look at the numbers together. The total cost will be around $200,000, and you have $40,000 saved. Given the two-year timeline, there's a significant funding gap. On your current path, this goal will be very difficult to achieve without taking on substantial debt.

It sounds like you're already saving diligently, so let's walk through a few options, starting with the most practical. This is what I call a 'Hierarchy of Funding Solutions' to make the best possible decision without jeopardizing your own financial future.

1.  **Re-evaluating the Goal:** Has she considered any in-state public universities? The quality of education is often just as high, but at a fraction of the cost—sometimes less than half. This is the most powerful way to close the funding gap.
2.  **Exploring Responsible Debt:** You could look into federal student loans, which have borrower protections. A loan of, say, $100,000 would result in a monthly payment of roughly $1,000 for 10 years after graduation. We would need to assess if that's a manageable burden for her and your family.
3.  **Optimizing Your Savings:** The $40,000 you have is a great start. We should ensure it's in a vehicle like a 529 plan—which is a tax-free education savings account—to get as much growth as possible in the next two years.

I know this is a lot to think about. The goal is to get her a great education without putting your own retirement at risk. Would you like to start by exploring some high-quality, lower-cost university options in your state? set_jsonfamily({\"household_income\": 120000, \"children\": [{\"age\": 16, \"goal\": \"college\", \"goal_cost\": 200000, \"current_savings\": 40000}]})"""

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
            clean_response = re.sub(r'\s*set_jsonfamily\(.*\)\s*$', '', response_text, flags=re.DOTALL)
            self._update_family_data(response_text)
            return clean_response.strip()
        return response_text.strip()

    def process_query(self, user_query: str) -> str:
        """Processes a user query using the Gemini API and manages state."""
        self.conversation_history.append({"role": "user", "content": user_query})

        financial_context = json.dumps(self.user_data, indent=2)
        family_context = json.dumps(self.family_data, indent=2)
        
        # Use only the last 10 messages for context to avoid token limits
        limited_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        history_formatted = "\n".join([f"{entry['role']}: {entry['content']}" for entry in limited_history])

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

    # Initialize messages in session state if not present
    if "messages" not in st.session_state:
        # Check if there's history in the file and load it
        if planner.conversation_history:
            st.session_state.messages = planner.conversation_history
        else:
            welcome_msg = """Hi! I'm your Family Financial Planning assistant. I can help you think through big life decisions like saving for college, buying a house, or planning for retirement. 

What financial goal is on your mind today?"""
            st.session_state.messages = [{"role": "assistant", "content": welcome_msg}]
            # Sync to planner history
            planner.conversation_history = st.session_state.messages.copy()
            planner._save_json(planner.history_file, planner.conversation_history)
    else:
        # Ensure file history and session state are in sync
        planner.conversation_history = st.session_state.messages.copy()

    # Sidebar - Portfolio Overview (to match the other model's look)
    with st.sidebar:
        st.header("📊 Your Financial Snapshot")
        
        if fi_client.is_loaded:
            portfolio = fi_client.get_portfolio_data()
            account_profile = fi_client.get_account_summary()
            
            # Key metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Value", f"${portfolio.get('total_market_value', 0):,.2f}")
                st.metric("Cash Balance", f"${portfolio.get('cash_balance', 0):,.2f}")
            with col2:
                day_change = portfolio.get('day_change', 0)
                change_color = "normal" if day_change >= 0 else "inverse"
                st.metric("Today's Change",
                         f"${day_change:,.2f}",
                         f"{portfolio.get('day_change_percent', 0):.2f}%",
                         delta_color=change_color)
                st.metric("Total Return",
                         f"${portfolio.get('total_return', 0):,.2f}",
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
                    <span style='color: {gain_color}'>${gain_loss:,.2f}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("To personalize your experience, create a `user_financial_data.json` file in this directory. The app will display your financial snapshot here.")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about college, housing, retirement, etc."):
        # Add user message to session state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking about your family's finances..."):
                response = planner.process_query(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                # Keep file history in sync
                planner.conversation_history = st.session_state.messages.copy()
                planner._save_json(planner.history_file, planner.conversation_history)

if __name__ == "__main__":
    main()
