import google.generativeai as genai
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class GeminiMarketClient:
    def __init__(self):
        """Initialize Gemini-powered market data client"""
        self.gemini_available = False
        self.model = None
        
        # Initialize Gemini
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                test_response = self.model.generate_content("Hello")
                self.gemini_available = True
                print("✅ Gemini Market Client initialized successfully!")
            except Exception as e:
                print(f"⚠️ Gemini API error in market client: {e}")
        else:
            print("⚠️ No Gemini API key found for market client")
    
    def get_real_time_market_data(self) -> Dict[str, Any]:
        """Get real-time market data using Gemini's knowledge"""
        if not self.gemini_available:
            return self._get_fallback_market_data()
        
        market_prompt = f"""
You are a financial market analyst with access to current market data. Provide real-time market analysis for today ({datetime.now().strftime('%Y-%m-%d')}).

Please provide current market information in the following JSON format:
{{
    "vix": current_vix_level,
    "fear_greed_index": current_fear_greed_0_to_100,
    "market_trend": "bullish/bearish/neutral",
    "spy_change_percent": todays_sp500_change_percent,
    "market_summary": "brief_market_summary",
    "key_movers": ["list", "of", "notable", "stock", "movements"],
    "sector_performance": {{
        "technology": percent_change,
        "healthcare": percent_change,
        "financials": percent_change,
        "energy": percent_change
    }},
    "market_sentiment": "risk_on/risk_off/mixed",
    "last_updated": "{datetime.now().isoformat()}"
}}

Focus on:
1. Current VIX volatility index
2. Market sentiment (Fear & Greed)
3. S&P 500 performance today
4. Major sector movements
5. Overall market direction

Return ONLY the JSON object with current market data.
"""
        
        try:
            response = self.model.generate_content(market_prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
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
            
            market_data = json.loads(response_text)
            
            # Validate and clean data with safe type conversion
            def safe_float(value, default=0.0):
                """Safely convert value to float"""
                if value is None:
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default

            def safe_int(value, default=0):
                """Safely convert value to int"""
                if value is None:
                    return default
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            validated_data = {
                "vix": safe_float(market_data.get("vix"), 20.0),
                "fear_greed_index": safe_int(market_data.get("fear_greed_index"), 50),
                "market_trend": market_data.get("market_trend", "neutral"),
                "spy_change_percent": safe_float(market_data.get("spy_change_percent"), 0.0),
                "market_summary": market_data.get("market_summary", "Market conditions are stable"),
                "key_movers": market_data.get("key_movers", []),
                "sector_performance": market_data.get("sector_performance", {}),
                "market_sentiment": market_data.get("market_sentiment", "mixed"),
                "last_updated": datetime.now().isoformat()
            }
            
            return validated_data
            
        except Exception as e:
            print(f"Error getting Gemini market data: {e}")
            return self._get_fallback_market_data()
    
    def get_stock_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get current stock analysis using Gemini"""
        if not self.gemini_available:
            return {"error": "Gemini not available"}
        
        stock_prompt = f"""
Analyze the current status of {symbol} stock as of today ({datetime.now().strftime('%Y-%m-%d')}).

Provide analysis in this JSON format:
{{
    "symbol": "{symbol}",
    "current_price": estimated_current_price,
    "price_change_percent": todays_change_percent,
    "volume_trend": "high/normal/low",
    "analyst_sentiment": "bullish/bearish/neutral",
    "key_news": ["recent", "news", "items"],
    "technical_analysis": "brief_technical_outlook",
    "fundamental_strength": "strong/moderate/weak",
    "risk_level": "high/medium/low",
    "short_term_outlook": "positive/negative/neutral",
    "volatility": "high/medium/low"
}}

Focus on:
1. Recent price movements
2. Any significant news or events
3. Technical indicators
4. Market sentiment around this stock
5. Risk assessment

Return ONLY the JSON object.
"""
        
        try:
            response = self.model.generate_content(stock_prompt)
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
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return {"symbol": symbol, "error": "Analysis unavailable"}
    
    def generate_dynamic_investment_recommendations(self, investment_amount: float, 
                                                  user_profile: Dict, current_portfolio: Dict) -> List[Dict]:
        """Generate investment recommendations based on current market conditions"""
        if not self.gemini_available:
            return []
        
        # Get current market data first
        market_data = self.get_real_time_market_data()
        
        recommendation_prompt = f"""
You are a professional investment advisor. Based on current market conditions and user profile, recommend 3-5 investment options.

INVESTMENT AMOUNT: ₹{investment_amount:,.2f}

USER PROFILE:
- Risk Tolerance: {user_profile.get('risk_tolerance', 'moderate')}
- Experience: {user_profile.get('investment_experience', 'intermediate')}
- Time Horizon: {user_profile.get('time_horizon', '10+ years')}
- Goals: {user_profile.get('investment_goals', [])}

CURRENT PORTFOLIO:
- Total Value: ₹{current_portfolio.get('total_value', 0):,.2f}
- Holdings: {len(current_portfolio.get('holdings', []))} positions
- Top Holdings: {[h['symbol'] for h in current_portfolio.get('holdings', [])[:3]]}

CURRENT MARKET CONDITIONS:
- VIX: {market_data['vix']}
- Fear/Greed Index: {market_data['fear_greed_index']}/100
- Market Trend: {market_data['market_trend']}
- S&P 500 Change: {market_data['spy_change_percent']}%
- Market Summary: {market_data['market_summary']}

Based on TODAY'S market conditions, recommend investment options in this JSON format:
[
  {{
    "symbol": "ETF_or_STOCK_SYMBOL",
    "name": "Full Name",
    "allocation_percentage": 20-40,
    "investment_amount": dollar_amount,
    "rationale": "Why this investment fits now given current market conditions",
    "risk_level": "low/medium/high",
    "market_timing": "Why this is good timing given today's market",
    "suitability_score": 1-10,
    "category": "large_cap/bonds/international/etc",
    "current_outlook": "positive/negative/neutral"
  }}
]

Consider:
1. Current market volatility (VIX: {market_data['vix']})
2. Market sentiment (Fear/Greed: {market_data['fear_greed_index']})
3. Sector performance today
4. User's risk tolerance and goals
5. Portfolio diversification needs

Recommend actual ETFs/stocks that make sense given today's market conditions.
Return ONLY the JSON array.
"""
        
        try:
            response = self.model.generate_content(recommendation_prompt)
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
            if not response_text.startswith('['):
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                if start != -1 and end != 0:
                    response_text = response_text[start:end]
            
            recommendations = json.loads(response_text)
            
            # Validate recommendations
            validated_recommendations = []
            for rec in recommendations:
                if isinstance(rec, dict) and 'symbol' in rec:
                    validated_rec = {
                        "symbol": rec.get("symbol", ""),
                        "name": rec.get("name", ""),
                        "allocation_percentage": float(rec.get("allocation_percentage", 25)),
                        "investment_amount": float(rec.get("investment_amount", investment_amount * 0.25)),
                        "rationale": rec.get("rationale", ""),
                        "risk_level": rec.get("risk_level", "medium"),
                        "market_timing": rec.get("market_timing", ""),
                        "suitability_score": float(rec.get("suitability_score", 7)),
                        "category": rec.get("category", "diversified"),
                        "current_outlook": rec.get("current_outlook", "neutral")
                    }
                    validated_recommendations.append(validated_rec)
            
            return validated_recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []
    
    def analyze_market_sentiment_for_investment(self, user_message: str, amount: float) -> str:
        """Analyze if current market conditions are good for the user's investment"""
        if not self.gemini_available:
            return "Market analysis unavailable"
        
        market_data = self.get_real_time_market_data()
        
        sentiment_prompt = f"""
A user wants to invest ₹{amount:,.2f} and said: "{user_message}"

Current market conditions:
- VIX: {market_data['vix']}
- Fear/Greed: {market_data['fear_greed_index']}/100
- Market Trend: {market_data['market_trend']}
- Market Summary: {market_data['market_summary']}

Provide a brief analysis (2-3 sentences) about whether NOW is a good time for this investment given current market conditions. Focus on:
1. Market timing
2. Volatility concerns
3. Emotional factors (fear/greed)
4. Overall market environment

Be practical and supportive.
"""
        
        try:
            response = self.model.generate_content(sentiment_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in market sentiment analysis: {e}")
            return "Current market conditions suggest a balanced approach to investing."
    
    def _get_fallback_market_data(self) -> Dict[str, Any]:
        """Fallback market data when Gemini is unavailable"""
        return {
            "vix": 20.0,
            "fear_greed_index": 50,
            "market_trend": "neutral",
            "spy_change_percent": 0.0,
            "market_summary": "Market conditions are stable",
            "key_movers": [],
            "sector_performance": {
                "technology": 0.0,
                "healthcare": 0.0,
                "financials": 0.0,
                "energy": 0.0
            },
            "market_sentiment": "mixed",
            "last_updated": datetime.now().isoformat()
        }