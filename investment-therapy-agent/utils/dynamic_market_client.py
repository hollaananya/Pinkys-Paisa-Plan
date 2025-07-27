import yfinance as yf
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import google.generativeai as genai
import os

class DynamicMarketClient:
    def __init__(self):
        """Initialize dynamic market data client with real APIs"""
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
                print("✅ Dynamic Market Client with Gemini initialized!")
            except Exception as e:
                print(f"⚠️ Gemini API error in market client: {e}")
        
        # Popular ETFs and stocks universe for dynamic recommendations
        self.investment_universe = {
            'etfs': {
                'SPY': {'name': 'SPDR S&P 500 ETF', 'category': 'large_cap', 'risk': 'low'},
                'QQQ': {'name': 'Invesco QQQ Trust', 'category': 'tech_growth', 'risk': 'medium'},
                'VTI': {'name': 'Vanguard Total Stock Market', 'category': 'total_market', 'risk': 'low'},
                'VUG': {'name': 'Vanguard Growth ETF', 'category': 'growth', 'risk': 'medium'},
                'VTV': {'name': 'Vanguard Value ETF', 'category': 'value', 'risk': 'low'},
                'VBR': {'name': 'Vanguard Small-Cap Value', 'category': 'small_cap', 'risk': 'high'},
                'VXUS': {'name': 'Vanguard Total International', 'category': 'international', 'risk': 'medium'},
                'BND': {'name': 'Vanguard Total Bond Market', 'category': 'bonds', 'risk': 'very_low'},
                'VNQ': {'name': 'Vanguard Real Estate ETF', 'category': 'real_estate', 'risk': 'medium'},
                'GLD': {'name': 'SPDR Gold Shares', 'category': 'commodities', 'risk': 'medium'}
            },
            'stocks': {
                'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'risk': 'medium'},
                'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'risk': 'medium'},
                'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology', 'risk': 'medium'},
                'AMZN': {'name': 'Amazon.com Inc.', 'sector': 'Consumer Discretionary', 'risk': 'medium'},
                'TSLA': {'name': 'Tesla Inc.', 'sector': 'Automotive', 'risk': 'high'},
                'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'risk': 'high'},
                'JPM': {'name': 'JPMorgan Chase & Co.', 'sector': 'Financial', 'risk': 'medium'},
                'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Healthcare', 'risk': 'low'},
                'V': {'name': 'Visa Inc.', 'sector': 'Financial', 'risk': 'medium'},
                'PG': {'name': 'Procter & Gamble', 'sector': 'Consumer Staples', 'risk': 'low'}
            }
        }
    
    def get_real_time_market_data(self) -> Dict[str, Any]:
        """Fetch real-time market indicators"""
        try:
            # Get VIX (Volatility Index)
            vix = yf.Ticker("^VIX")
            vix_data = vix.history(period="1d")
            current_vix = float(vix_data['Close'].iloc[-1]) if not vix_data.empty else 20.0
            
            # Get S&P 500 for trend analysis
            spy = yf.Ticker("SPY")
            spy_data = spy.history(period="5d")
            
            if not spy_data.empty:
                current_price = float(spy_data['Close'].iloc[-1])
                previous_price = float(spy_data['Close'].iloc[-2])
                change_percent = ((current_price - previous_price) / previous_price) * 100
                
                # Determine market trend
                if change_percent > 1:
                    trend = "bullish"
                elif change_percent < -1:
                    trend = "bearish"
                else:
                    trend = "neutral"
            else:
                trend = "neutral"
                change_percent = 0
            
            # Calculate Fear & Greed Index approximation
            # (Simplified calculation based on VIX)
            if current_vix < 15:
                fear_greed = 75  # Greed
            elif current_vix < 25:
                fear_greed = 50  # Neutral
            else:
                fear_greed = 25  # Fear
            
            return {
                "vix": round(current_vix, 1),
                "fear_greed_index": fear_greed,
                "market_trend": trend,
                "spy_change_percent": round(change_percent, 2),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error fetching real market data: {e}")
            # Fallback to reasonable defaults
            return {
                "vix": 20.0,
                "fear_greed_index": 50,
                "market_trend": "neutral",
                "spy_change_percent": 0.0,
                "last_updated": datetime.now().isoformat()
            }
    
    def get_stock_performance_data(self, symbols: List[str], period: str = "1mo") -> Dict[str, Dict]:
        """Get real-time stock performance for multiple symbols"""
        performance_data = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                info = ticker.info
                
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    first_price = float(hist['Close'].iloc[0])
                    return_pct = ((current_price - first_price) / first_price) * 100
                    
                    # Get volatility (standard deviation of returns)
                    returns = hist['Close'].pct_change().dropna()
                    volatility = float(returns.std() * (252 ** 0.5) * 100)  # Annualized
                    
                    performance_data[symbol] = {
                        "current_price": round(current_price, 2),
                        "return_1m": round(return_pct, 2),
                        "volatility": round(volatility, 1),
                        "volume": int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0,
                        "market_cap": info.get('marketCap', 0),
                        "pe_ratio": info.get('trailingPE', 0),
                        "sector": info.get('sector', 'Unknown')
                    }
                    
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                performance_data[symbol] = {
                    "current_price": 0,
                    "return_1m": 0,
                    "volatility": 20,
                    "volume": 0,
                    "market_cap": 0,
                    "pe_ratio": 0,
                    "sector": "Unknown"
                }
        
        return performance_data
    
    def generate_dynamic_recommendations(self, investment_amount: float, user_profile: Dict, 
                                       current_portfolio: Dict, market_data: Dict) -> List[Dict]:
        """Generate dynamic investment recommendations using Gemini and real market data"""
        
        if not self.gemini_available:
            return self._fallback_recommendations(investment_amount, user_profile)
        
        # Get real-time performance for our investment universe
        all_symbols = list(self.investment_universe['etfs'].keys()) + list(self.investment_universe['stocks'].keys())
        performance_data = self.get_stock_performance_data(all_symbols)
        
        # Create market analysis prompt
        analysis_prompt = f"""
You are a professional investment advisor with access to real-time market data. Generate 3-5 personalized investment recommendations.

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
- VIX (Volatility): {market_data['vix']}
- Fear/Greed Index: {market_data['fear_greed_index']}/100
- Market Trend: {market_data['market_trend']}
- S&P 500 Recent Change: {market_data['spy_change_percent']}%

REAL-TIME PERFORMANCE DATA (1-month):
{self._format_performance_data_for_prompt(performance_data)}

Based on this real-time analysis, recommend 3-5 investments from the available options. Consider:
1. Current market conditions and volatility
2. User's risk profile and existing holdings
3. Recent performance trends
4. Diversification needs
5. Market sentiment

Return ONLY a JSON array with this structure:
[
  {{
    "symbol": "SYMBOL",
    "allocation_percentage": 30-70,
    "investment_amount": dollar_amount,
    "rationale": "Why this investment fits now",
    "risk_assessment": "Current risk level and why",
    "market_timing": "Why this is good timing given current market",
    "suitability_score": 1-10
  }}
]

Focus on current market opportunities and risks. Be specific about timing and market conditions.
"""
        
        try:
            response = self.model.generate_content(analysis_prompt)
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
            
            # Clean and parse JSON
            response_text = response_text.strip()
            if not response_text.startswith('['):
                start = response_text.find('[')
                end = response_text.rfind(']') + 1
                if start != -1 and end != 0:
                    response_text = response_text[start:end]
            
            recommendations = json.loads(response_text)
            
            # Enhance with real-time data
            enhanced_recommendations = []
            for rec in recommendations:
                symbol = rec['symbol']
                if symbol in performance_data:
                    perf = performance_data[symbol]
                    rec['current_price'] = perf['current_price']
                    rec['recent_return'] = perf['return_1m']
                    rec['volatility'] = perf['volatility']
                    rec['fund_info'] = self._get_fund_info(symbol)
                
                enhanced_recommendations.append(rec)
            
            return enhanced_recommendations
            
        except Exception as e:
            print(f"Error generating dynamic recommendations: {e}")
            return self._fallback_recommendations(investment_amount, user_profile)
    
    def analyze_current_holdings(self, holdings: List[Dict]) -> Dict[str, Any]:
        """Analyze current portfolio holdings with real-time data"""
        if not holdings:
            return {"analysis": "No holdings to analyze"}
        
        symbols = [h['symbol'] for h in holdings]
        performance_data = self.get_stock_performance_data(symbols)
        
        analysis = {
            "total_holdings": len(holdings),
            "performance_summary": {},
            "risk_analysis": {},
            "recommendations": []
        }
        
        if self.gemini_available:
            analysis_prompt = f"""
Analyze this investment portfolio with real-time data:

CURRENT HOLDINGS:
{json.dumps(holdings, indent=2)}

REAL-TIME PERFORMANCE (1-month):
{json.dumps(performance_data, indent=2)}

MARKET CONDITIONS:
{json.dumps(self.get_real_time_market_data(), indent=2)}

Provide analysis on:
1. Portfolio performance vs market
2. Risk concentration issues
3. Sector diversification
4. Current market positioning
5. Specific recommendations for improvement

Return detailed analysis in plain text format.
"""
            
            try:
                response = self.model.generate_content(analysis_prompt)
                analysis["ai_analysis"] = response.text.strip()
            except:
                analysis["ai_analysis"] = "Portfolio analysis temporarily unavailable"
        
        return analysis
    
    def _format_performance_data_for_prompt(self, performance_data: Dict) -> str:
        """Format performance data for Gemini prompt"""
        formatted = []
        for symbol, data in performance_data.items():
            fund_info = self._get_fund_info(symbol)
            formatted.append(
                f"{symbol} ({fund_info['name']}): "
                f"Price: ₹{data['current_price']}, "
                f"1M Return: {data['return_1m']}%, "
                f"Volatility: {data['volatility']}%, "
                f"Category: {fund_info['category']}"
            )
        return "\n".join(formatted)
    
    def _get_fund_info(self, symbol: str) -> Dict[str, str]:
        """Get fund information from our universe"""
        if symbol in self.investment_universe['etfs']:
            info = self.investment_universe['etfs'][symbol].copy()
            info['type'] = 'ETF'
            return info
        elif symbol in self.investment_universe['stocks']:
            info = self.investment_universe['stocks'][symbol].copy()
            info['type'] = 'Stock'
            info['category'] = info.get('sector', 'Unknown')
            return info
        else:
            return {'name': symbol, 'category': 'Unknown', 'risk': 'medium', 'type': 'Unknown'}
    
    def _fallback_recommendations(self, investment_amount: float, user_profile: Dict) -> List[Dict]:
        """Fallback recommendations when Gemini is not available"""
        risk_tolerance = user_profile.get('risk_tolerance', 'moderate')
        
        if 'conservative' in risk_tolerance:
            symbols = ['BND', 'VTV', 'SPY']
        elif 'aggressive' in risk_tolerance:
            symbols = ['QQQ', 'VUG', 'VBR']
        else:
            symbols = ['SPY', 'VTI', 'BND']
        
        recommendations = []
        allocation_per_fund = investment_amount / len(symbols)
        
        for i, symbol in enumerate(symbols):
            fund_info = self._get_fund_info(symbol)
            recommendations.append({
                "symbol": symbol,
                "allocation_percentage": 100 / len(symbols),
                "investment_amount": allocation_per_fund,
                "rationale": f"Fits {risk_tolerance} risk profile",
                "risk_assessment": fund_info['risk'],
                "market_timing": "Suitable for current market conditions",
                "suitability_score": 7 + i,
                "fund_info": fund_info
            })
        
        return recommendations