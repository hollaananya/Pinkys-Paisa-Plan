import google.generativeai as genai
import json
import re
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
from utils.enhanced_fi_client import EnhancedFiMCPClient

load_dotenv()

class AdvancedInvestmentTherapyAgent:
    def __init__(self):
        # Configure Gemini API
        self.gemini_available = False
        self.model = None
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Test connection
                test_response = self.model.generate_content("Hello")
                self.gemini_available = True
                print("✅ Gemini API connected successfully!")
                
            except Exception as e:
                print(f"⚠️ Gemini API error: {e}")
                self.gemini_available = False
        else:
            print("⚠️ No Gemini API key found")
            self.gemini_available = False
        
        self.fi_client = EnhancedFiMCPClient()
        
        # Enhanced stock symbol mapping for better recognition
        self.common_stocks = {
            'apple': 'AAPL', 'microsoft': 'MSFT', 'tesla': 'TSLA', 'amazon': 'AMZN',
            'google': 'GOOGL', 'alphabet': 'GOOGL', 'meta': 'META', 'facebook': 'META',
            'netflix': 'NFLX', 'nvidia': 'NVDA', 'intel': 'INTC', 'amd': 'AMD',
            'disney': 'DIS', 'boeing': 'BA', 'walmart': 'WMT', 'visa': 'V',
            'mastercard': 'MA', 'jpmorgan': 'JPM', 'goldman': 'GS', 'coca cola': 'KO',
            'pepsi': 'PEP', 'johnson': 'JNJ', 'pfizer': 'PFE', 'exxon': 'XOM',
            'berkshire': 'BRK.B', 'salesforce': 'CRM', 'oracle': 'ORCL', 'ibm': 'IBM'
        }
    
    def extract_stock_symbols(self, user_message: str) -> List[str]:
        """Enhanced stock symbol extraction with company name mapping"""
        message_lower = user_message.lower()
        extracted_symbols = []
        
        # First, check for company names
        for company_name, symbol in self.common_stocks.items():
            if company_name in message_lower:
                extracted_symbols.append(symbol)
        
        # Then check for explicit symbols (2-5 letters, all caps)
        symbols = re.findall(r'\b[A-Z]{2,5}\b', user_message.upper())
        
        # Filter out common words that might be mistaken for symbols
        common_words = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAS', 
            'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'USE', 'MAN', 'NEW', 
            'NOW', 'OLD', 'SEE', 'HIM', 'TWO', 'HOW', 'ITS', 'WHO', 'SIT', 'SET', 
            'MAY', 'WAY', 'TOO', 'BUY', 'SELL', 'HOLD', 'STOP', 'LOSS', 'GAIN',
            'TAKE', 'GIVE', 'MAKE', 'CALL', 'PUT', 'TIME', 'YEAR', 'WEEK', 'MONTH'
        }
        
        filtered_symbols = [s for s in symbols if s not in common_words]
        extracted_symbols.extend(filtered_symbols)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(extracted_symbols))
    
    def extract_investment_amount(self, user_message: str) -> Optional[float]:
        """Extract investment amount from user message"""
        # Pattern for ₹1000, ₹1,000, ₹1000.00, etc.
        dollar_patterns = [
            r'\₹(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # ₹1,000.00
            r'\₹(\d+(?:\.\d{2})?)',                  # ₹1000.00
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?) dollars?',  # 1000 dollars
            r'(\d+(?:\.\d{2})?) dollars?',           # 1000 dollars
            r'(\d+)k',                               # 5k
            r'(\d+) thousand'                        # 5 thousand
        ]
        
        for pattern in dollar_patterns:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            if matches:
                amount_str = matches[0].replace(',', '')
                try:
                    amount = float(amount_str)
                    # Handle 'k' notation
                    if 'k' in user_message.lower():
                        amount *= 1000
                    elif 'thousand' in user_message.lower():
                        amount *= 1000
                    return amount
                except ValueError:
                    continue
        
        return None
    
    def classify_question(self, user_message: str) -> Dict[str, Any]:
        """Enhanced compound question classification for all investment therapy scenarios"""
        message_lower = user_message.lower()
        
        # Detect various elements
        has_portfolio = any(word in message_lower for word in [
            'portfolio', 'my investments', 'my holdings', 'my stocks', 'my positions',
            'my money', 'my assets', 'allocation'
        ])
        
        has_market = any(word in message_lower for word in [
            'market', 'today', 'current environment', 'market conditions', 'volatility',
            'trends', 'market today', 'today\'s market', 'current market', 'environment',
            'given today'
        ])
        
        has_emotional = any(word in message_lower for word in [
            'worried', 'anxious', 'scared', 'nervous', 'stressed', 'panic', 'uncertain',
            'confused', 'frustrated', 'overwhelmed', 'fearful', 'terrified', 'angry'
        ])
        
        has_behavioral = any(word in message_lower for word in [
            'why do i', 'pattern', 'mistake', 'decision', 'behavior', 'tendency', 'habit',
            'always', 'keep', 'irrational', 'emotional', 'bad timing', 'wrong time'
        ])
        
        has_timing = any(word in message_lower for word in [
            'when', 'timing', 'now', 'should i', 'right time', 'good time', 'best time',
            'when to', 'is it time', 'given today', 'current conditions'
        ])
        
        has_risk = any(word in message_lower for word in [
            'risk', 'safe', 'volatile', 'conservative', 'aggressive', 'diversify',
            'risky', 'dangerous', 'secure', 'stability', 'too much risk'
        ])
        
        # Extract data
        extracted_amount = self.extract_investment_amount(user_message)
        extracted_symbols = self.extract_stock_symbols(user_message)
        
        has_investment_amount = extracted_amount is not None
        has_stock_symbol = len(extracted_symbols) > 0
        
        # COMPOUND CLASSIFICATIONS (Priority order for comprehensive coverage)
        
        # 1. Portfolio + Market + Emotional (Triple compound)
        if has_portfolio and has_market and has_emotional:
            return {
                'type': 'portfolio_market_emotional',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.95,
                'requires_market_data': True,
                'emotional_content': True,
                'requires_recommendations': False
            }
        
        # 2. Investment + Market + Behavioral
        if has_investment_amount and has_market and has_behavioral:
            return {
                'type': 'investment_market_behavioral',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.95,
                'requires_market_data': True,
                'emotional_content': True,
                'requires_recommendations': True
            }
        
        # 3. Stock + Market + Timing
        if has_stock_symbol and has_market and has_timing:
            return {
                'type': 'stock_market_timing',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.95,
                'requires_market_data': True,
                'emotional_content': False,
                'requires_recommendations': False
            }
        
        # 4. Portfolio + Market Context
        if has_portfolio and has_market:
            return {
                'type': 'portfolio_with_market_context',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.9,
                'requires_market_data': True,
                'emotional_content': False,
                'requires_recommendations': False
            }
        
        # 5. Investment + Emotional + Risk
        if has_investment_amount and has_emotional and has_risk:
            return {
                'type': 'investment_emotional_risk',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.9,
                'requires_market_data': True,
                'emotional_content': True,
                'requires_recommendations': True
            }
        
        # 6. Stock + Behavioral + Emotional
        if has_stock_symbol and has_behavioral and has_emotional:
            return {
                'type': 'stock_behavioral_emotional',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.9,
                'requires_market_data': True,
                'emotional_content': True,
                'requires_recommendations': False
            }
        
        # 7. Portfolio + Behavioral
        if has_portfolio and has_behavioral:
            return {
                'type': 'portfolio_behavioral',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.85,
                'requires_market_data': True,
                'emotional_content': True,
                'requires_recommendations': False
            }
        
        # 8. Investment + Market + Timing
        if has_investment_amount and has_market and has_timing:
            return {
                'type': 'investment_market_timing',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.85,
                'requires_market_data': True,
                'emotional_content': False,
                'requires_recommendations': True
            }
        
        # 9. Stock + Emotional
        if has_stock_symbol and has_emotional:
            return {
                'type': 'stock_emotional',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.85,
                'requires_market_data': True,
                'emotional_content': True,
                'requires_recommendations': False
            }
        
        # 10. Portfolio + Risk Analysis
        if has_portfolio and has_risk:
            return {
                'type': 'portfolio_risk_analysis',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.8,
                'requires_market_data': True,
                'emotional_content': False,
                'requires_recommendations': False
            }
        
        # SINGLE CATEGORY FALLBACKS
        
        # Market conditions (only if no portfolio mentioned)
        if has_market and not has_portfolio:
            return {
                'type': 'market_conditions',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.9,
                'requires_market_data': True,
                'emotional_content': False,
                'requires_recommendations': False
            }
        
        # Investment request
        if has_investment_amount:
            return {
                'type': 'investment_request',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.8,
                'requires_market_data': False,
                'emotional_content': False,
                'requires_recommendations': True
            }
        
        # Stock analysis
        if has_stock_symbol:
            return {
                'type': 'stock_analysis',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.8,
                'requires_market_data': True,
                'emotional_content': False,
                'requires_recommendations': False
            }
        
        # Portfolio review
        if has_portfolio:
            return {
                'type': 'portfolio_review',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.8,
                'requires_market_data': False,
                'emotional_content': False,
                'requires_recommendations': False
            }
        
        # Emotional support
        if has_emotional:
            return {
                'type': 'emotional_support',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.8,
                'requires_market_data': False,
                'emotional_content': True,
                'requires_recommendations': False
            }
        
        # Behavioral analysis
        if has_behavioral:
            return {
                'type': 'behavioral_insight',
                'extracted_amount': extracted_amount,
                'extracted_symbols': extracted_symbols,
                'confidence': 0.8,
                'requires_market_data': False,
                'emotional_content': True,
                'requires_recommendations': False
            }
        
        # Default fallback
        return {
            'type': 'general',
            'extracted_amount': extracted_amount,
            'extracted_symbols': extracted_symbols,
            'confidence': 0.5,
            'requires_market_data': False,
            'emotional_content': False,
            'requires_recommendations': False
        }
    
    def analyze_behavioral_patterns(self, user_message: str) -> Dict[str, Any]:
        """Analyze user's behavioral patterns using Gemini and historical data"""
        if not self.gemini_available:
            return self._basic_behavioral_analysis(user_message)
        
        behavioral_history = self.fi_client.get_behavioral_history()
        psychological_profile = self.fi_client.get_psychological_profile()
        transactions = self.fi_client.get_transaction_history()
        portfolio = self.fi_client.get_portfolio_data()
        
        analysis_prompt = f"""
You are an expert behavioral finance analyst. Analyze this investor's message and behavioral patterns:

USER MESSAGE: "{user_message}"

BEHAVIORAL HISTORY:
- Stress Triggers: {behavioral_history.get('stress_triggers', [])}
- Emotional Patterns: {behavioral_history.get('emotional_patterns', {})}
- Investment Behavior: {behavioral_history.get('investment_behavior', {})}

PSYCHOLOGICAL PROFILE:
- Personality: {psychological_profile.get('personality_type', 'unknown')}
- Stress Indicators: {psychological_profile.get('stress_indicators', [])}
- Confidence Boosters: {psychological_profile.get('confidence_boosters', [])}

RECENT TRANSACTIONS (last 3):
{transactions[:3] if transactions else 'No recent transactions'}

CURRENT PORTFOLIO:
- Total Value: ₹{portfolio['total_value']:,.2f}
- Today's Change: {portfolio['performance']['day_change_percentage']:.2f}%
- Holdings: {len(portfolio['holdings'])} positions

Return ONLY a JSON object with this structure:
{{
    "emotional_state": ["primary_emotion", "secondary_emotion"],
    "stress_level": 1-10,
    "behavioral_biases": ["detected_biases"],
    "confidence_level": 1-10,
    "decision_quality_risk": "low/medium/high",
    "recommended_action": "immediate_support/guided_reflection/proceed_normally",
    "key_insights": ["behavioral_insights"],
    "intervention_needed": true/false
}}

Focus on: loss aversion, FOMO, overconfidence, panic selling, herding bias, anchoring.
"""
        
        try:
            response = self.model.generate_content(analysis_prompt)
            response_text = response.text.strip()
            
            # Extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end]
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end]
            
            response_text = response_text.strip()
            if not response_text.startswith('{'):
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != 0:
                    response_text = response_text[start:end]
            
            analysis = json.loads(response_text)
            return analysis
            
        except Exception as e:
            print(f"Error in behavioral analysis: {e}")
            return self._basic_behavioral_analysis(user_message)
    
    def _basic_behavioral_analysis(self, user_message: str) -> Dict:
        """Fallback behavioral analysis"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['panic', 'scared', 'terrified', 'disaster']):
            return {
                "emotional_state": ["panic", "fear"],
                "stress_level": 9,
                "behavioral_biases": ["panic_selling", "loss_aversion"],
                "confidence_level": 2,
                "decision_quality_risk": "high",
                "recommended_action": "immediate_support",
                "intervention_needed": True,
                "key_insights": ["High stress detected"]
            }
        elif any(word in message_lower for word in ['worried', 'anxious', 'nervous', 'concerned', 'stressed']):
            return {
                "emotional_state": ["anxious", "uncertain"],
                "stress_level": 7,
                "behavioral_biases": ["loss_aversion"],
                "confidence_level": 4,
                "decision_quality_risk": "medium",
                "recommended_action": "guided_reflection",
                "intervention_needed": False,
                "key_insights": ["Moderate anxiety detected"]
            }
        elif any(word in message_lower for word in ['invest', 'buy', 'money']):
            return {
                "emotional_state": ["focused", "analytical"],
                "stress_level": 4,
                "behavioral_biases": ["confirmation_bias"],
                "confidence_level": 7,
                "decision_quality_risk": "medium",
                "recommended_action": "guided_reflection",
                "intervention_needed": False,
                "key_insights": ["Investment focused mindset"]
            }
        else:
            return {
                "emotional_state": ["calm", "curious"],
                "stress_level": 3,
                "behavioral_biases": [],
                "confidence_level": 6,
                "decision_quality_risk": "low",
                "recommended_action": "proceed_normally",
                "intervention_needed": False,
                "key_insights": ["Balanced emotional state"]
            }
    
    def generate_comprehensive_response(self, user_message: str) -> Dict[str, Any]:
        """Main method to handle any investment question with enhanced routing"""
        
        # Classify the question
        classification = self.classify_question(user_message)
        
        # Analyze behavioral patterns
        behavioral_analysis = self.analyze_behavioral_patterns(user_message)
        
        response_data = {
            "classification": classification,
            "behavioral_analysis": behavioral_analysis,
            "main_response": "",
            "recommendations": [],
            "coping_strategies": [],
            "requires_intervention": behavioral_analysis.get('intervention_needed', False)
        }
        
        # Route to appropriate handler based on classification
        if classification['type'] == 'stock_market_timing' and classification['extracted_symbols']:
            symbol = classification['extracted_symbols'][0]
            response_data["main_response"] = self.generate_stock_market_timing_response(symbol, user_message)
        
        elif classification['type'] == 'portfolio_market_emotional':
            response_data["main_response"] = self._generate_portfolio_market_emotional_response(user_message)
        
        elif classification['type'] == 'investment_market_behavioral':
            amount = classification['extracted_amount']
            response_data["main_response"] = self._generate_investment_market_behavioral_response(amount, user_message)
            response_data["recommendations"] = self.fi_client.get_personalized_recommendations(amount)
        
        elif classification['type'] == 'portfolio_with_market_context':
            response_data["main_response"] = self._generate_portfolio_with_market_analysis(user_message)
        
        elif classification['type'] == 'investment_emotional_risk':
            amount = classification['extracted_amount']
            response_data["main_response"] = self._generate_investment_emotional_risk_response(amount, user_message)
            response_data["recommendations"] = self.fi_client.get_personalized_recommendations(amount)
        
        elif classification['type'] == 'stock_behavioral_emotional' and classification['extracted_symbols']:
            symbol = classification['extracted_symbols'][0]
            response_data["main_response"] = self._generate_stock_behavioral_emotional_response(symbol, user_message)
        
        elif classification['type'] == 'portfolio_behavioral':
            response_data["main_response"] = self._generate_portfolio_behavioral_response(user_message)
        
        elif classification['type'] == 'investment_market_timing':
            amount = classification['extracted_amount']
            response_data["main_response"] = self._generate_investment_market_timing_response(amount, user_message)
            response_data["recommendations"] = self.fi_client.get_personalized_recommendations(amount)
        
        elif classification['type'] == 'stock_emotional' and classification['extracted_symbols']:
            symbol = classification['extracted_symbols'][0]
            response_data["main_response"] = self._generate_stock_emotional_response(symbol, user_message)
        
        elif classification['type'] == 'portfolio_risk_analysis':
            response_data["main_response"] = self._generate_portfolio_risk_analysis_response(user_message)
        
        # Single category handlers
        elif classification['type'] == 'market_conditions':
            response_data["main_response"] = self._generate_market_conditions_response(user_message)
        
        elif classification['type'] == 'investment_request' and classification['extracted_amount']:
            amount = classification['extracted_amount']
            response_data["main_response"] = self.generate_investment_recommendations(amount, user_message)
            response_data["recommendations"] = self.fi_client.get_personalized_recommendations(amount)
        
        elif classification['type'] == 'stock_analysis' and classification['extracted_symbols']:
            symbol = classification['extracted_symbols'][0]
            response_data["main_response"] = self.get_stock_analysis_with_therapy(symbol, user_message)
        
        elif classification['type'] == 'portfolio_review':
            response_data["main_response"] = self._generate_portfolio_analysis(user_message)
        
        else:
            # Default to emotional analysis and therapeutic response
            response_data["main_response"] = self.generate_therapeutic_response(user_message, behavioral_analysis)
        
        # Add coping strategies if stress is detected
        if behavioral_analysis.get('stress_level', 5) > 6:
            primary_emotion = behavioral_analysis.get('emotional_state', ['anxious'])[0]
            response_data["coping_strategies"] = self.get_coping_strategies(primary_emotion)
        
        return response_data
    
    def generate_stock_market_timing_response(self, symbol: str, user_message: str) -> str:
        """Handle stock + market + timing compound questions"""
        if not self.gemini_available:
            return self._generate_fallback_stock_response(symbol, user_message)
        
        portfolio = self.fi_client.get_portfolio_data()
        market_data = self.fi_client.get_market_data()
        behavioral = self.fi_client.get_behavioral_history()
        
        # Check if user already owns this stock
        current_position = None
        for holding in portfolio['holdings']:
            if holding['symbol'].upper() == symbol.upper():
                current_position = holding
                break
        
        prompt = f"""
You are an Investment Therapy Agent analyzing a stock purchase decision with market timing considerations.

USER QUESTION: "{user_message}"
STOCK: {symbol}
CURRENT POSITION: {f"₹{current_position['market_value']:,.2f} (P&L: ₹{current_position['unrealized_gain_loss']:,.2f})" if current_position else "None"}

CURRENT MARKET CONDITIONS:
- Market Trend: {market_data['market_indicators']['market_trend']}
- VIX (Volatility): {market_data['market_indicators']['vix']}
- Fear/Greed Index: {market_data['market_indicators']['fear_greed_index']}/100
- Market Summary: {market_data['market_indicators'].get('market_summary', 'Current market conditions analyzed')}

USER'S PORTFOLIO CONTEXT:
- Total Portfolio: ₹{portfolio['total_value']:,.2f}
- Today's Performance: {portfolio['performance']['day_change_percentage']:.2f}%
- Risk Tolerance: {self.fi_client.get_account_summary()['risk_tolerance']}

USER BEHAVIORAL PATTERNS:
- Loss Aversion: {behavioral.get('emotional_patterns', {}).get('loss_aversion_score', 5)}/10
- FOMO Tendency: {behavioral.get('emotional_patterns', {}).get('fomo_tendency', 5)}/10

Provide comprehensive analysis that:

1. **Market Timing Assessment**: 
   - Analyze whether current market conditions favor buying {symbol}
   - Consider VIX levels and Fear/Greed sentiment for this stock type
   - Address the specific timing question in their message

2. **Stock-Specific Outlook**: 
   - How {symbol} typically performs in current market environment
   - Recent performance trends and factors affecting the stock
   - Sector considerations and market correlations

3. **Risk & Portfolio Impact**:
   - How adding/increasing {symbol} would affect their portfolio
   - Risk considerations given current market volatility
   - Position sizing recommendations if appropriate

4. **Emotional & Behavioral Guidance**:
   - Address the psychological aspects of market timing decisions
   - Help them distinguish between FOMO and genuine opportunity
   - Encourage systematic vs. emotional decision-making

Communication Style:
- Balance analytical insights with emotional support
- Avoid direct buy/sell recommendations
- Focus on education and decision-making process
- Reference their specific situation and market context
- Use 3-4 paragraphs with clear, actionable guidance

Remember: You're helping them make a well-informed decision, not making the decision for them.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in stock market timing analysis: {e}")
            return self._generate_fallback_stock_response(symbol, user_message)
    
    def _generate_fallback_stock_response(self, symbol: str, user_message: str) -> str:
        """Enhanced fallback response for stock-related questions"""
        return f"""I understand you're considering {symbol} in the current market environment. When evaluating any stock purchase, especially with timing concerns, it's important to separate the emotional impulse from the strategic decision.

Market timing is notoriously difficult, even for professional investors. Rather than trying to perfectly time your entry, consider your long-term investment goals and risk tolerance. What's driving your interest in {symbol} right now - is it based on fundamental analysis, recent news, or perhaps fear of missing out?

Before making any decision about {symbol}, I'd encourage you to reflect on: 1) How this fits into your overall portfolio strategy, 2) Whether you're comfortable with the volatility that comes with individual stock ownership, and 3) What specific timeframe you're considering for this investment. These factors matter more than trying to perfectly time the market."""
    
    def _generate_portfolio_market_emotional_response(self, user_message: str) -> str:
        """Handle portfolio + market + emotional compound questions"""
        if not self.gemini_available:
            return self._generate_fallback_compound_response("portfolio_market_emotional", user_message)
        
        portfolio = self.fi_client.get_portfolio_data()
        market_data = self.fi_client.get_market_data()
        behavioral = self.fi_client.get_behavioral_history()
        
        prompt = f"""
User asked: "{user_message}" - This combines portfolio analysis, market context, and emotional support.

PORTFOLIO DATA:
- Value: ₹{portfolio['total_value']:,.2f}
- Performance: {portfolio['performance']['total_return_percentage']:.2f}% total return
- Today: {portfolio['performance']['day_change_percentage']:.2f}%
- Holdings: {[f"{h['symbol']}: {h['allocation_percentage']:.1f}% ({h['unrealized_gain_loss']:+.0f})" for h in portfolio['holdings'][:5]]}

CURRENT MARKET CONDITIONS:
- Trend: {market_data['market_indicators']['market_trend']}
- VIX: {market_data['market_indicators']['vix']}
- Fear/Greed: {market_data['market_indicators']['fear_greed_index']}/100

USER EMOTIONAL PATTERNS:
- Loss Aversion: {behavioral.get('emotional_patterns', {}).get('loss_aversion_score', 5)}/10
- FOMO Tendency: {behavioral.get('emotional_patterns', {}).get('fomo_tendency', 5)}/10
- Stress Triggers: {[t['trigger'] for t in behavioral.get('stress_triggers', [])]}

Provide a response that:
1. Acknowledges their emotional state with empathy
2. Analyzes their portfolio performance in today's market context
3. Addresses how current market conditions affect their specific holdings
4. Provides emotional guidance based on their behavioral patterns
5. Offers actionable steps considering both market and emotional factors

Keep response supportive but data-driven. 3-4 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in compound response: {e}")
            return self._generate_fallback_compound_response("portfolio_market_emotional", user_message)
    
    def _generate_investment_market_behavioral_response(self, amount: float, user_message: str) -> str:
        """Handle investment + market + behavioral compound questions"""
        if not self.gemini_available:
            return self._generate_fallback_compound_response("investment_market_behavioral", user_message)
        
        market_data = self.fi_client.get_market_data()
        behavioral = self.fi_client.get_behavioral_history()
        recommendations = self.fi_client.get_personalized_recommendations(amount)
        
        prompt = f"""
User wants to invest ₹{amount:,.2f} and asked: "{user_message}" - This requires investment advice with market timing and behavioral considerations.

CURRENT MARKET CONDITIONS:
- Trend: {market_data['market_indicators']['market_trend']}
- VIX: {market_data['market_indicators']['vix']}
- Fear/Greed: {market_data['market_indicators']['fear_greed_index']}/100

BEHAVIORAL PATTERNS:
- Past behavior: {behavioral.get('investment_behavior', {})}
- Emotional patterns: {behavioral.get('emotional_patterns', {})}
- Stress triggers: {[t['trigger'] for t in behavioral.get('stress_triggers', [])]}

RECOMMENDATIONS:
{[f"{r['fund']['symbol']}: {r['fund']['name']} (Score: {r['suitability_score']:.1f}/10)" for r in recommendations[:3]]}

Provide investment guidance that:
1. Addresses their specific behavioral patterns and past investment decisions
2. Considers current market timing for the ₹{amount:,.2f} investment
3. Explains how their emotional tendencies might affect this decision
4. Provides specific recommendations with behavioral safeguards
5. Includes market-timing considerations

Focus on behavioral finance principles. 3-4 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in compound response: {e}")
            return self._generate_fallback_compound_response("investment_market_behavioral", user_message)
    
    def _generate_portfolio_with_market_analysis(self, user_message: str) -> str:
        """Enhanced portfolio analysis with market context"""
        if not self.gemini_available:
            return self._generate_fallback_compound_response("portfolio_with_market_context", user_message)
        
        portfolio = self.fi_client.get_portfolio_data()
        market_data = self.fi_client.get_market_data()
        behavioral = self.fi_client.get_behavioral_history()
        risk_analysis = self.fi_client.analyze_portfolio_risk()
        
        prompt = f"""
User asked: "{user_message}" - This requires detailed portfolio analysis with current market context.

PORTFOLIO DETAILS:
- Total Value: ₹{portfolio['total_value']:,.2f}
- Total Return: {portfolio['performance']['total_return_percentage']:.2f}% (₹{portfolio['performance']['total_return']:,.2f})
- Today's Change: {portfolio['performance']['day_change_percentage']:.2f}% (₹{portfolio['performance']['day_change']:,.2f})
- Risk Score: {risk_analysis['risk_score']:.1f}/10
- Holdings Breakdown:
{[f"  • {h['symbol']}: {h['allocation_percentage']:.1f}% = ₹{h['market_value']:,.2f} (P&L: ₹{h['unrealized_gain_loss']:+,.2f})" for h in portfolio['holdings']]}

CURRENT MARKET ENVIRONMENT:
- Market Trend: {market_data['market_indicators']['market_trend']}
- VIX (Volatility): {market_data['market_indicators']['vix']}
- Fear/Greed Index: {market_data['market_indicators']['fear_greed_index']}/100
- Market Summary: {market_data['market_indicators'].get('market_summary', 'Current market analysis')}

USER BEHAVIORAL CONTEXT:
- Risk Comfort: {behavioral.get('emotional_patterns', {}).get('risk_comfort', 'moderate')}
- Rebalancing Pattern: {behavioral.get('investment_behavior', {}).get('rebalancing_frequency', 'unknown')}

Provide comprehensive analysis that:
1. Evaluates how each major holding is performing in today's market environment
2. Assesses portfolio risk level relative to current market volatility
3. Analyzes whether the portfolio is well-positioned for current market trend
4. Identifies any holdings that may need attention given market conditions
5. Provides actionable insights for portfolio optimization in current environment

Use specific portfolio data and current market metrics. 4-5 paragraphs with detailed analysis.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in portfolio market analysis: {e}")
            return self._generate_fallback_compound_response("portfolio_with_market_context", user_message)
    
    def _generate_investment_emotional_risk_response(self, amount: float, user_message: str) -> str:
        """Handle investment + emotional + risk compound questions"""
        if not self.gemini_available:
            return f"I understand you want to invest ₹{amount:,.2f} but are feeling uncertain about the risks. Let's work through your concerns together and find an approach that matches your comfort level."
        
        portfolio = self.fi_client.get_portfolio_data()
        behavioral = self.fi_client.get_behavioral_history()
        recommendations = self.fi_client.get_personalized_recommendations(amount)
        
        prompt = f"""
User wants to invest ₹{amount:,.2f} and is expressing emotional concerns about risk: "{user_message}"

PORTFOLIO CONTEXT:
- Current Value: ₹{portfolio['total_value']:,.2f}
- Risk Score: {self.fi_client.analyze_portfolio_risk()['risk_score']:.1f}/10

BEHAVIORAL PATTERNS:
- Loss Aversion: {behavioral.get('emotional_patterns', {}).get('loss_aversion_score', 5)}/10
- Risk Comfort: {behavioral.get('emotional_patterns', {}).get('risk_comfort', 'moderate')}

RECOMMENDED OPTIONS:
{[f"{r['fund']['symbol']}: {r['fund']['name']} (Risk: {r['fund']['risk_level']})" for r in recommendations[:3]]}

Provide guidance that:
1. Acknowledges their emotional concerns about risk
2. Explains risk in context of their portfolio and experience
3. Suggests specific low-risk options for the ₹{amount:,.2f}
4. Addresses their emotional state with practical risk management
5. Builds confidence through education about risk mitigation

Focus on emotional support while being practical about risk. 3 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return f"I understand your concerns about risk with your ₹{amount:,.2f} investment. Given your current portfolio of ₹{portfolio['total_value']:,.2f}, we can explore lower-risk options that align with your comfort level while still working toward your goals."
    
    def _generate_stock_behavioral_emotional_response(self, symbol: str, user_message: str) -> str:
        """Handle stock + behavioral + emotional compound questions"""
        portfolio = self.fi_client.get_portfolio_data()
        behavioral = self.fi_client.get_behavioral_history()
        
        # Check current position
        current_position = None
        for holding in portfolio['holdings']:
            if holding['symbol'].upper() == symbol.upper():
                current_position = holding
                break
        
        position_text = f"You currently hold ₹{current_position['market_value']:,.2f} worth, with a P&L of ₹{current_position['unrealized_gain_loss']:,.2f}" if current_position else "You don't currently own this stock"
        
        stress_triggers = behavioral.get('stress_triggers', [])
        past_action = stress_triggers[0].get('action', 'reacted emotionally') if stress_triggers else 'shown emotional responses'
        
        return f"""I can see you're having some complex feelings about {symbol}. {position_text}, and it's natural for emotions to run high when money is involved.

Your behavioral patterns show {behavioral.get('emotional_patterns', {}).get('loss_aversion_score', 5)}/10 loss aversion, which means {symbol}'s volatility might be triggering some anxiety. Past patterns suggest you've {past_action} during market stress.

Let's explore what's really driving your feelings about {symbol} right now. Are you worried about missing out, concerned about losses, or feeling uncertain about when to act? Understanding these emotions will help us make a decision that aligns with both your financial goals and emotional well-being."""
    
    def _generate_portfolio_behavioral_response(self, user_message: str) -> str:
        """Handle portfolio + behavioral compound questions"""
        portfolio = self.fi_client.get_portfolio_data()
        behavioral = self.fi_client.get_behavioral_history()
        
        return f"""Looking at your ₹{portfolio['total_value']:,.2f} portfolio through a behavioral lens, I can see some interesting patterns in your investment approach. Your {portfolio['performance']['total_return_percentage']:.2f}% total return reflects the impact of both your strategic decisions and emotional responses to market events.

Your behavioral history shows {behavioral.get('investment_behavior', {}).get('panic_sell_frequency', 'occasional')} instances of panic selling and an {behavioral.get('investment_behavior', {}).get('sip_consistency', 0.85)*100:.0f}% consistency rate with systematic investments. This suggests you have good long-term discipline but sometimes struggle with short-term emotional reactions, particularly around {', '.join([t['trigger'] for t in behavioral.get('stress_triggers', [])][:2])}.

The key insight here is that your {behavioral.get('emotional_patterns', {}).get('patience_level', 5)}/10 patience level and {behavioral.get('emotional_patterns', {}).get('loss_aversion_score', 5)}/10 loss aversion are creating a pattern where you make excellent systematic investments but occasionally undermine them with emotional decisions. What specific behavioral patterns have you noticed in your own investment journey?"""
    
    def _generate_investment_market_timing_response(self, amount: float, user_message: str) -> str:
        """Handle investment + market + timing compound questions"""
        market_data = self.fi_client.get_market_data()
        recommendations = self.fi_client.get_personalized_recommendations(amount)
        
        return f"""Given your ₹{amount:,.2f} investment and the timing question you've raised, let's analyze current market conditions. The market is showing a {market_data['market_indicators']['market_trend']} trend with VIX at {market_data['market_indicators']['vix']} and Fear/Greed at {market_data['market_indicators']['fear_greed_index']}/100.

From a timing perspective, {'this appears to be a favorable environment' if market_data['market_indicators']['fear_greed_index'] < 60 and market_data['market_indicators']['vix'] < 25 else 'we should exercise some caution given current conditions'}. The recommended allocations for your ₹{amount:,.2f} would be {recommendations[0]['fund']['symbol']} ({recommendations[0]['fund']['name']}) for {'stability' if recommendations[0]['fund']['risk_level'] == 'low' else 'growth potential'}.

However, remember that timing the market perfectly is nearly impossible. Instead of trying to find the perfect moment, consider dollar-cost averaging your ₹{amount:,.2f} over the next few months. This approach reduces timing risk while still getting you invested during {'this favorable period' if market_data['market_indicators']['market_trend'] == 'bullish' else 'these uncertain times'}."""
    
    def _generate_stock_emotional_response(self, symbol: str, user_message: str) -> str:
        """Handle stock + emotional compound questions"""
        portfolio = self.fi_client.get_portfolio_data()
        
        # Check current position
        current_position = None
        for holding in portfolio['holdings']:
            if holding['symbol'].upper() == symbol.upper():
                current_position = holding
                break
        
        return f"""I can hear the emotional weight in your question about {symbol}. {f'Your current position of ₹{current_position["market_value"]:,.2f} with a {current_position["unrealized_gain_loss"]:+,.2f} P&L' if current_position else f'Your interest in {symbol}'} is clearly stirring up some feelings, and that's completely natural when our financial future is involved.

Emotional investing often leads us to buy high during periods of excitement and sell low during periods of fear. {'The fact that you are currently showing a loss on this position' if current_position and current_position['unrealized_gain_loss'] < 0 else 'Your emotional connection to this stock'} might be triggering some of these natural psychological responses.

Let's take a step back from the emotions and focus on the facts. What specifically about {symbol} is causing you to feel this way right now? Are you worried about further losses, excited about potential gains, or feeling uncertain about what to do next? Understanding the emotion behind the question will help us make a more rational decision."""
    
    def _generate_portfolio_risk_analysis_response(self, user_message: str) -> str:
        """Handle portfolio + risk compound questions"""
        portfolio = self.fi_client.get_portfolio_data()
        risk_analysis = self.fi_client.analyze_portfolio_risk()
        
        return f"""Your ₹{portfolio['total_value']:,.2f} portfolio currently has a risk score of {risk_analysis['risk_score']:.1f}/10, with {risk_analysis['high_risk_percent']:.1f}% in high-risk investments, {risk_analysis['medium_risk_percent']:.1f}% in medium-risk, and {risk_analysis['low_risk_percent']:.1f}% in low-risk positions.

Looking at your risk distribution, your largest positions are {portfolio['holdings'][0]['symbol']} ({portfolio['holdings'][0]['allocation_percentage']:.1f}% - {portfolio['holdings'][0]['risk_level']} risk) and {portfolio['holdings'][1]['symbol']} ({portfolio['holdings'][1]['allocation_percentage']:.1f}% - {portfolio['holdings'][1]['risk_level']} risk). This suggests {'a well-balanced approach' if risk_analysis['risk_score'] < 6 else 'a more aggressive stance' if risk_analysis['risk_score'] > 7 else 'a moderate risk profile'}.

Given your {portfolio['performance']['total_return_percentage']:.2f}% total return, your risk level appears to be {'appropriate for your returns' if portfolio['performance']['total_return_percentage'] > 10 else 'conservative, which may be limiting your growth potential'}. What specific risk concerns do you have about your current allocation, and what changes are you considering?"""
    
    def _generate_market_conditions_response(self, user_message: str) -> str:
        """Generate real-time market conditions response using Gemini"""
        if not self.gemini_available:
            return "I'd be happy to check current market conditions, but I don't have access to real-time market data right now."
        
        market_data = self.fi_client.get_market_data()
        
        market_prompt = f"""
The user asked: "{user_message}"

Current market data:
- VIX: {market_data['market_indicators']['vix']}
- Fear/Greed Index: {market_data['market_indicators']['fear_greed_index']}/100
- Market Trend: {market_data['market_indicators']['market_trend']}
- Market Summary: {market_data['market_indicators'].get('market_summary', 'Market analysis available')}

Provide a comprehensive analysis of current market conditions in 2-3 paragraphs. Include:
1. Overall market sentiment and direction
2. Volatility levels and what they mean for investors
3. Key factors driving today's market
4. What investors should be aware of right now

Be informative and analytical, like a professional market analyst providing current market intelligence.
"""
        
        try:
            response = self.model.generate_content(market_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating market conditions response: {e}")
            market_indicators = market_data['market_indicators']
            return f"""Current market conditions show a VIX of {market_indicators['vix']}, indicating {'elevated' if market_indicators['vix'] > 20 else 'normal'} volatility levels. The Fear/Greed Index is at {market_indicators['fear_greed_index']}/100, suggesting {'fearful' if market_indicators['fear_greed_index'] < 40 else 'greedy' if market_indicators['fear_greed_index'] > 60 else 'neutral'} market sentiment.

The overall market trend appears {market_indicators['market_trend']}, which reflects the current economic environment and investor positioning. These conditions suggest {'caution' if market_indicators['vix'] > 25 else 'a balanced approach'} for new investments."""
    
    def generate_investment_recommendations(self, amount: float, user_context: str) -> str:
        """Generate DYNAMIC investment recommendations using Gemini market intelligence"""
        if not self.gemini_available:
            return self._basic_investment_recommendations(amount, user_context)
        
        portfolio = self.fi_client.get_portfolio_data()
        behavioral = self.fi_client.get_behavioral_history()
        account = self.fi_client.get_account_summary()
        
        # Get REAL-TIME recommendations from Gemini
        dynamic_recommendations = self.fi_client.get_personalized_recommendations(amount)
        real_time_market = self.fi_client.get_market_data()
        
        # Get market sentiment for this specific investment
        market_sentiment = self.fi_client.get_market_sentiment_for_investment(user_context, amount)
        
        investment_prompt = f"""
You are an Investment Therapy Agent providing personalized investment recommendations using REAL-TIME market intelligence from Gemini.

USER REQUEST: "{user_context}"
INVESTMENT AMOUNT: ₹{amount:,.2f}

CURRENT PORTFOLIO ANALYSIS:
- Total Value: ₹{portfolio['total_value']:,.2f}
- Available Cash: ₹{account['available_cash']:,.2f}
- Current Holdings: {[f"{h['symbol']}: {h['allocation_percentage']:.1f}%" for h in portfolio['holdings'][:5]]}

USER PROFILE:
- Risk Tolerance: {account['risk_tolerance']}
- Experience: {account['investment_experience']}
- Time Horizon: {account['time_horizon']}
- Goals: {', '.join(account['investment_goals'])}

BEHAVIORAL PATTERNS:
- Risk Comfort: {behavioral.get('emotional_patterns', {}).get('risk_comfort', 'unknown')}
- Volatility Tolerance: {behavioral.get('emotional_patterns', {}).get('volatility_tolerance', 5)}/10
- FOMO Tendency: {behavioral.get('emotional_patterns', {}).get('fomo_tendency', 5)}/10
- Loss Aversion: {behavioral.get('emotional_patterns', {}).get('loss_aversion_score', 5)}/10

LIVE MARKET INTELLIGENCE (from Gemini):
- VIX (Market Volatility): {real_time_market['market_indicators']['vix']}
- Fear/Greed Index: {real_time_market['market_indicators']['fear_greed_index']}/100
- Current Market Trend: {real_time_market['market_indicators']['market_trend']}
- Market Summary: {real_time_market['market_indicators'].get('market_summary', 'Market conditions analyzed')}

MARKET TIMING ANALYSIS:
{market_sentiment}

GEMINI-POWERED INVESTMENT RECOMMENDATIONS:
{self._format_gemini_recommendations(dynamic_recommendations)}

Provide a comprehensive response that:
1. **Current Market Context**: Explain what today's market intelligence means for this investment
2. **Specific Recommendations**: Discuss the Gemini-generated recommendations with current market timing
3. **Behavioral Considerations**: Address their emotional patterns given current market conditions
4. **Risk Assessment**: How current market intelligence affects their risk profile
5. **Timing Considerations**: Why now is or isn't a good time based on real market analysis

Communication Style:
- Reference the REAL market intelligence from Gemini
- Use the LIVE recommendations with current market context
- Address market timing based on actual current analysis
- Include specific dollar amounts and current market insights
- Focus on behavioral guidance with real market backdrop
- 3-4 paragraphs maximum

Remember: You're using REAL market intelligence from Gemini to provide timely, relevant investment therapy.
"""
        
        try:
            response = self.model.generate_content(investment_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating Gemini-powered recommendations: {e}")
            return self._basic_investment_recommendations(amount, user_context)
    
    def _format_gemini_recommendations(self, recommendations: List[Dict]) -> str:
        """Format Gemini-powered recommendations for prompt"""
        if not recommendations:
            return "No recommendations available from market analysis"
        
        formatted = []
        for rec in recommendations:
            fund = rec['fund']
            formatted.append(
                f"• {fund['symbol']} ({fund['name']}): "
                f"Suitability: {rec['suitability_score']:.1f}/10, "
                f"Market Outlook: {fund.get('current_outlook', 'Neutral')}, "
                f"Risk Level: {fund['risk_level']}, "
                f"Rationale: {rec.get('rationale', 'Market-based selection')}"
            )
        
        return "\n".join(formatted)
    
    def _basic_investment_recommendations(self, amount: float, user_context: str) -> str:
        """Fallback investment recommendations"""
        portfolio = self.fi_client.get_portfolio_data()
        recommendations = self.fi_client.get_personalized_recommendations(amount)
        
        if recommendations:
            top_rec = recommendations[0]
            return f"""Based on your ₹{portfolio['total_value']:,.2f} portfolio and ₹{amount:,.2f} investment amount, I'd suggest considering {top_rec['fund']['name']} ({top_rec['fund']['symbol']}).

This recommendation fits your profile because: {top_rec['rationale']}. With your current portfolio allocation, this would add good diversification while maintaining your risk comfort level.

Before proceeding, consider: What's motivating this investment decision right now? Are you feeling confident about this choice, or is there any emotional pressure influencing your thinking?"""
        
        return f"I'd be happy to help you invest ₹{amount:,.2f}. Let's first understand what's driving this decision - are you looking to diversify, take advantage of an opportunity, or following a systematic investment plan?"
    
    def get_stock_analysis_with_therapy(self, symbol: str, user_context: str) -> str:
        """Analyze stock with therapeutic guidance using Gemini API"""
        if not self.gemini_available:
            return f"I'd love to help you analyze {symbol}, but I don't have access to real-time stock data right now. However, I can help you explore what's driving your interest in {symbol}. What specific concerns or hopes do you have about this stock?"
        
        portfolio = self.fi_client.get_portfolio_data()
        account = self.fi_client.get_account_summary()
        
        # Check if user already owns this stock
        current_position = None
        for holding in portfolio['holdings']:
            if holding['symbol'].upper() == symbol.upper():
                current_position = holding
                break
        
        stock_analysis_prompt = f"""
You are an Investment Therapy Agent analyzing a stock request with both informational and therapeutic guidance.

USER REQUEST: "{user_context}"
STOCK SYMBOL: {symbol}

USER'S PORTFOLIO CONTEXT:
- Total Portfolio: ₹{portfolio['total_value']:,.2f}
- Risk Tolerance: {account['risk_tolerance']}
- Experience Level: {account['investment_experience']}
- Current Position in {symbol}: {"₹" + str(current_position['market_value']) + " (P&L: ₹" + str(current_position['unrealized_gain_loss']) + ")" if current_position else "None"}

Please provide a response that includes:

1. **Stock Information**: Brief overview of {symbol} (you can use general knowledge)
2. **Portfolio Fit**: How this might fit their risk profile and current portfolio
3. **Emotional Considerations**: 
   - Why might they be asking about this stock now?
   - What emotions might be driving this (FOMO, fear, overconfidence)?
   - How does their current position (if any) affect their psychology?
4. **Behavioral Guidance**: 
   - Questions to help them reflect on their motivations
   - Encourage thoughtful decision-making process
   - Reference their investment goals and time horizon
5. **Therapeutic Support**: Be warm and supportive while educating

Remember: 
- Don't give direct buy/sell advice
- Focus on helping them understand their emotions and decision-making process
- Be supportive but encourage thoughtful reflection
- Keep response conversational and empathetic (2-3 paragraphs)
"""
        
        try:
            response = self.model.generate_content(stock_analysis_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error in stock analysis: {e}")
            return f"I'd be happy to help you think through your interest in {symbol}. What's drawing you to this stock right now? Are you feeling optimistic about its prospects, or perhaps worried about missing out? Understanding your emotional connection to this investment can help us explore whether it aligns with your overall strategy."
    
    def _generate_portfolio_analysis(self, user_message: str) -> str:
        """Generate portfolio analysis"""
        if self.gemini_available:
            portfolio = self.fi_client.get_portfolio_data()
            account = self.fi_client.get_account_summary()
            
            portfolio_prompt = f"""
Provide a therapeutic portfolio analysis for this user:

PORTFOLIO:
- Value: ₹{portfolio['total_value']:,.2f}
- Return: {portfolio['performance']['total_return_percentage']:.2f}%
- Today: {portfolio['performance']['day_change_percentage']:.2f}%
- Holdings: {len(portfolio['holdings'])} positions

USER: {account['risk_tolerance']} risk tolerance, {account['investment_experience']} experience

Request: "{user_message}"

Focus on emotional and behavioral aspects, not specific investment advice.
Provide supportive analysis in 2-3 paragraphs.
"""
            
            try:
                response = self.model.generate_content(portfolio_prompt)
                return response.text.strip()
            except:
                pass
        
        # Fallback
        portfolio = self.fi_client.get_portfolio_data()
        return f"""
Looking at your ₹{portfolio['total_value']:,.2f} portfolio, I can see you've built a solid foundation with {len(portfolio['holdings'])} holdings and a {portfolio['performance']['total_return_percentage']:.2f}% overall return.

Today's {portfolio['performance']['day_change_percentage']:.2f}% change might feel significant, but remember that daily fluctuations are normal. Your long-term progress is what truly matters for your financial goals.

How are you feeling about your portfolio's performance? Are there specific holdings or aspects that are causing you concern or giving you confidence?
"""
    
    def generate_therapeutic_response(self, user_message: str, emotional_analysis: Dict) -> str:
        """Generate therapeutic response using Gemini API"""
        if not self.gemini_available:
            return self._generate_fallback_response(user_message, emotional_analysis)
        
        portfolio = self.fi_client.get_portfolio_data()
        account = self.fi_client.get_account_summary()
        transactions = self.fi_client.get_transaction_history()
        
        therapeutic_prompt = f"""
You are a skilled Investment Therapy Agent - a specialized AI coach focused on behavioral finance and emotional support for investors.

USER MESSAGE: "{user_message}"

EMOTIONAL ANALYSIS:
- Stress Level: {emotional_analysis['stress_level']}/10
- Primary Emotions: {', '.join(emotional_analysis.get('emotional_state', []))}
- Urgency: {emotional_analysis.get('urgency', 5)}/10
- Key Concerns: {', '.join(emotional_analysis.get('key_concerns', []))}
- Intervention Needed: {emotional_analysis.get('intervention_needed', False)}

CURRENT PORTFOLIO CONTEXT:
- Total Value: ₹{portfolio['total_value']:,.2f}
- Today's Change: {portfolio['performance']['day_change_percentage']:.2f}% (₹{portfolio['performance']['day_change']:,.2f})
- Total Return: {portfolio['performance']['total_return_percentage']:.2f}% (₹{portfolio['performance']['total_return']:,.2f})
- Holdings: {len(portfolio['holdings'])} positions

USER PROFILE:
- Risk Tolerance: {account['risk_tolerance'].replace('_', ' ').title()}
- Investment Experience: {account['investment_experience'].title()}
- Time Horizon: {account['time_horizon']}
- Investment Goals: {', '.join(account['investment_goals'])}

RECENT ACTIVITY:
- {len(transactions)} transactions in last 30 days

Provide a therapeutic response that:
1. Acknowledges their emotional state with genuine empathy
2. Contextualizes their concerns with their actual portfolio performance
3. Addresses any behavioral biases detected
4. Provides practical, actionable coping strategies
5. Encourages healthy investment behavior aligned with their goals
6. References their specific portfolio situation when helpful
7. If intervention_needed is true, provide crisis support

Communication style:
- Warm, empathetic, non-judgmental like a skilled therapist
- Use behavioral finance concepts naturally
- Ask probing questions to understand underlying emotions
- 2-3 paragraphs maximum
- Focus on emotions and psychology, NOT direct investment advice

Remember: You're a therapist who specializes in investment behavior, not a financial advisor.
"""
        
        try:
            response = self.model.generate_content(therapeutic_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error in Gemini therapeutic response: {e}")
            return self._generate_fallback_response(user_message, emotional_analysis)
    
    def _generate_fallback_response(self, user_message: str, emotional_analysis: Dict) -> str:
        """Enhanced fallback response"""
        portfolio = self.fi_client.get_portfolio_data()
        account = self.fi_client.get_account_summary()
        stress_level = emotional_analysis['stress_level']
        
        if stress_level > 8:
            return f"""
I can sense the high level of stress in your message, and I want you to know that these feelings are completely valid. When our financial security feels threatened, intense emotions are a natural human response.

Let's pause for a moment and breathe together. Your portfolio is currently worth ₹{portfolio['total_value']:,.2f}, and while today's {portfolio['performance']['day_change_percentage']:.2f}% change feels overwhelming, your overall {portfolio['performance']['total_return_percentage']:.2f}% return shows that your long-term strategy is working.

Before making any decisions, I strongly encourage a 24-hour cooling-off period. This isn't about the market—it's about giving your rational mind time to catch up with your emotional response. What specific fear is driving the most anxiety for you right now?
"""
        
        elif stress_level > 6:
            return f"""
I can hear the concern in your message, and it's completely understandable to feel this way about your investments. Managing a ₹{portfolio['total_value']:,.2f} portfolio involves emotional ups and downs—it's part of being a thoughtful investor.

Your {portfolio['performance']['total_return_percentage']:.2f}% total return demonstrates that your approach is sound, even though today's {portfolio['performance']['day_change_percentage']:.2f}% movement might feel unsettling. Remember, your {account['risk_tolerance'].replace('_', ' ')} risk tolerance and {account['time_horizon']} time horizon provide important context for these daily fluctuations.

What specific aspect of your current situation is causing you the most concern? Let's explore it together and find some strategies to help you feel more grounded.
"""
        
        else:
            return f"""
Thank you for sharing your thoughts about your investments. This kind of self-reflection shows real emotional intelligence and is exactly what separates successful long-term investors from those who get caught up in market noise.

Your ₹{portfolio['total_value']:,.2f} portfolio and {portfolio['performance']['total_return_percentage']:.2f}% return reflect your commitment to building wealth over time. The fact that you're thinking thoughtfully about your investments rather than reacting impulsively is a genuine strength.

What aspect of your investment journey would you like to explore together today? I'm here to help you understand any patterns or emotions that might be influencing your decisions.
"""
    
    def _generate_fallback_compound_response(self, compound_type: str, user_message: str) -> str:
        """Fallback responses for compound questions when Gemini is unavailable"""
        portfolio = self.fi_client.get_portfolio_data()
        market_data = self.fi_client.get_market_data()
        
        fallback_responses = {
            "portfolio_market_emotional": f"""I understand you're feeling concerned about your portfolio in today's market environment. Your ₹{portfolio['total_value']:,.2f} portfolio is showing a {portfolio['performance']['total_return_percentage']:.2f}% total return, which demonstrates solid long-term performance despite today's {portfolio['performance']['day_change_percentage']:.2f}% change.

With the current market trend being {market_data['market_indicators']['market_trend']} and VIX at {market_data['market_indicators']['vix']}, it's natural to feel some anxiety. Your diversified holdings across {len(portfolio['holdings'])} positions provide good protection against market volatility.

Remember that emotional reactions to market movements are normal, but your long-term strategy has served you well. How can we work together to manage these feelings while staying focused on your investment goals?""",
            
            "portfolio_with_market_context": f"""Looking at your ₹{portfolio['total_value']:,.2f} portfolio in today's {market_data['market_indicators']['market_trend']} market environment, your holdings are positioned well for current conditions. Your major positions include {portfolio['holdings'][0]['symbol']} ({portfolio['holdings'][0]['allocation_percentage']:.1f}%) and {portfolio['holdings'][1]['symbol']} ({portfolio['holdings'][1]['allocation_percentage']:.1f}%), which have generated a {portfolio['performance']['total_return_percentage']:.2f}% overall return.

With the VIX at {market_data['market_indicators']['vix']} and Fear/Greed index at {market_data['market_indicators']['fear_greed_index']}/100, current market conditions suggest your diversified approach is appropriate. Your risk score of {self.fi_client.analyze_portfolio_risk()['risk_score']:.1f}/10 aligns well with the current market environment.""",
            
            "investment_market_behavioral": f"""I understand you're looking to invest and are concerned about your behavioral patterns. This kind of self-awareness is actually a great strength in investing. Given current market conditions, it's wise to be thoughtful about timing and emotional decision-making.

Your recognition of past behavioral patterns shows maturity as an investor. Many successful investors struggle with the same challenges - the key is developing systems and strategies that work with your psychology, not against it."""
        }
        
        return fallback_responses.get(compound_type, f"I'd be happy to help you with your question about {compound_type.replace('_', ' ')}. Let me analyze your portfolio and current market conditions to provide you with the most relevant guidance.")
    
    def get_coping_strategies(self, emotion_type: str) -> List[str]:
        """Get personalized coping strategies"""
        strategies = {
            "panic": [
                "🫁 **Breathing Exercise**: Take 5 deep breaths - in for 4, hold for 4, out for 6",
                "⏰ **24-Hour Rule**: Commit to waiting 24 hours before making any trades",
                "📱 **Digital Detox**: Close all trading apps and step away from financial news",
                "📞 **Call Support**: Reach out to a trusted friend, family member, or advisor",
                "📊 **Reality Check**: Remember your portfolio is built for long-term success"
            ],
            "anxious": [
                "📈 **Zoom Out**: Focus on your long-term investment goals and time horizon",
                "📚 **Study History**: Research how markets have recovered from past downturns",
                "🤖 **Automate Decisions**: Set up systematic investments to reduce emotional trading",
                "📝 **Write It Down**: Journal your concerns - they're often less scary on paper",
                "💰 **Remember Your Why**: Connect with your original reasons for investing"
            ],
            "fomo": [
                "🎯 **Strategy Check**: Ask 'Does this fit my existing investment plan?'",
                "⏰ **Wait 48 Hours**: Great opportunities don't disappear overnight",
                "📊 **Current Performance**: Review how your existing investments are doing",
                "🧘 **FOMO Meditation**: Acknowledge the feeling without acting on it",
                "💡 **Opportunity Cost**: Consider what you'd have to sell to buy something new"
            ],
            "overconfident": [
                "🪞 **Humility Practice**: Review past mistakes and lessons learned",
                "🎲 **Acknowledge Luck**: Some gains might be market timing, not pure skill",
                "📈 **Risk Assessment**: Calculate what you could lose, not just what you could gain",
                "📊 **Track Everything**: Document your reasoning for each investment decision",
                "❓ **Seek Contrarian Views**: Actively look for opposing perspectives"
            ]
        }
        
        return strategies.get(emotion_type, [
            "🎯 Focus on your long-term investment strategy",
            "📊 Review your portfolio's overall performance",
            "🤔 Take time to reflect before making decisions",
            "📞 Consider seeking a second opinion"
        ])
    
    # Additional utility methods you may need
    
    def _validate_classification(self, classification: Dict) -> bool:
        """Validate classification results"""
        required_fields = ['type', 'confidence', 'requires_market_data', 'emotional_content']
        return all(field in classification for field in required_fields)
    
    def get_response_metadata(self, classification: Dict, behavioral_analysis: Dict) -> Dict:
        """Get metadata about the response for frontend display"""
        return {
            "question_type": classification['type'],
            "confidence": classification['confidence'],
            "emotional_intensity": behavioral_analysis.get('stress_level', 5),
            "requires_followup": behavioral_analysis.get('intervention_needed', False),
            "market_data_used": classification.get('requires_market_data', False),
            "recommendations_provided": classification.get('requires_recommendations', False)
        }
    
    def log_interaction(self, user_message: str, classification: Dict, response: str):
        """Log interaction for learning and improvement"""
        # This could be expanded to log to a database for analysis
        print(f"Interaction logged: {classification['type']} (confidence: {classification['confidence']})")
    
    # Method to handle edge cases and errors gracefully
    def handle_error_gracefully(self, error: Exception, user_message: str) -> str:
        """Handle errors gracefully with helpful fallback responses"""
        error_responses = {
            "connection_error": "I'm having some connectivity issues right now, but I'm still here to help you think through your investment concerns.",
            "data_error": "I'm having trouble accessing some data, but we can still work through your investment questions together.",
            "analysis_error": "I encountered an issue with my analysis, but let's focus on what's most important to you right now about your investments."
        }
        
        # Log the error for debugging
        print(f"Error handled: {type(error).__name__}: {str(error)}")
        
        # Return a contextual error response
        if "connection" in str(error).lower():
            return error_responses["connection_error"]
        elif "data" in str(error).lower():
            return error_responses["data_error"]
        else:
            return error_responses["analysis_error"]