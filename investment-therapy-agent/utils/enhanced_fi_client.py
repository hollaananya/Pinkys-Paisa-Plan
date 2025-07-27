import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class EnhancedFiMCPClient:
    def __init__(self, fi_data_file: str = "fi_data/enhanced_user_data.json"):
        """Initialize Enhanced Fi MCP client with amount-aware recommendations"""
        self.fi_data_file = fi_data_file
        self.fi_data = None
        self.is_loaded = False
        self._load_fi_data()
        
        # Initialize Gemini market client
        try:
            from utils.gemini_market_client import GeminiMarketClient
            self.market_client = GeminiMarketClient()
            print("🚀 Enhanced Fi MCP Client with Gemini Market Data initialized!")
        except ImportError as e:
            print(f"⚠️ Could not import GeminiMarketClient: {e}")
            self.market_client = None
        
        # Amount-based investment strategies
        self.amount_strategies = {
            "micro": {  # ₹100 - ₹500
                "min_amount": 100,
                "max_amount": 500,
                "strategy": "single_etf_focus",
                "max_positions": 1,
                "focus": "Low-cost broad market exposure"
            },
            "small": {  # ₹500 - ₹2000
                "min_amount": 500,
                "max_amount": 2000,
                "strategy": "core_satellite",
                "max_positions": 2,
                "focus": "Core diversification with growth component"
            },
            "medium": {  # ₹2000 - ₹10000
                "min_amount": 2000,
                "max_amount": 10000,
                "strategy": "diversified_portfolio",
                "max_positions": 4,
                "focus": "Balanced diversification across asset classes"
            },
            "large": {  # ₹10000 - ₹50000
                "min_amount": 10000,
                "max_amount": 50000,
                "strategy": "sophisticated_allocation",
                "max_positions": 6,
                "focus": "Comprehensive diversification with individual stocks"
            },
            "portfolio": {  # ₹50000+
                "min_amount": 50000,
                "max_amount": float('inf'),
                "strategy": "institutional_approach",
                "max_positions": 10,
                "focus": "Full institutional-style portfolio construction"
            }
        }
        
        # Investment universe with amount considerations
        self.investment_options = {
            'conservative': {
                'micro': [{'symbol': 'BND', 'allocation': 100}],
                'small': [{'symbol': 'BND', 'allocation': 60}, {'symbol': 'SPY', 'allocation': 40}],
                'medium': [{'symbol': 'SPY', 'allocation': 40}, {'symbol': 'BND', 'allocation': 35}, {'symbol': 'VTV', 'allocation': 25}],
                'large': [{'symbol': 'SPY', 'allocation': 35}, {'symbol': 'BND', 'allocation': 30}, {'symbol': 'VTV', 'allocation': 20}, {'symbol': 'VXUS', 'allocation': 15}],
                'portfolio': [{'symbol': 'SPY', 'allocation': 30}, {'symbol': 'BND', 'allocation': 25}, {'symbol': 'VTV', 'allocation': 20}, {'symbol': 'VXUS', 'allocation': 15}, {'symbol': 'VNQ', 'allocation': 10}]
            },
            'moderate': {
                'micro': [{'symbol': 'SPY', 'allocation': 100}],
                'small': [{'symbol': 'SPY', 'allocation': 70}, {'symbol': 'BND', 'allocation': 30}],
                'medium': [{'symbol': 'SPY', 'allocation': 50}, {'symbol': 'QQQ', 'allocation': 25}, {'symbol': 'BND', 'allocation': 25}],
                'large': [{'symbol': 'SPY', 'allocation': 40}, {'symbol': 'QQQ', 'allocation': 25}, {'symbol': 'BND', 'allocation': 20}, {'symbol': 'VXUS', 'allocation': 15}],
                'portfolio': [{'symbol': 'SPY', 'allocation': 35}, {'symbol': 'QQQ', 'allocation': 20}, {'symbol': 'BND', 'allocation': 20}, {'symbol': 'VXUS', 'allocation': 15}, {'symbol': 'VNQ', 'allocation': 10}]
            },
            'aggressive': {
                'micro': [{'symbol': 'QQQ', 'allocation': 100}],
                'small': [{'symbol': 'QQQ', 'allocation': 60}, {'symbol': 'VUG', 'allocation': 40}],
                'medium': [{'symbol': 'QQQ', 'allocation': 40}, {'symbol': 'VUG', 'allocation': 30}, {'symbol': 'SPY', 'allocation': 30}],
                'large': [{'symbol': 'QQQ', 'allocation': 35}, {'symbol': 'VUG', 'allocation': 25}, {'symbol': 'SPY', 'allocation': 20}, {'symbol': 'VBR', 'allocation': 20}],
                'portfolio': [{'symbol': 'QQQ', 'allocation': 30}, {'symbol': 'VUG', 'allocation': 25}, {'symbol': 'SPY', 'allocation': 20}, {'symbol': 'VBR', 'allocation': 15}, {'symbol': 'VXUS', 'allocation': 10}]
            }
        }
        
        # Fund details database
        self.fund_details = {
            'SPY': {'name': 'SPDR S&P 500 ETF', 'category': 'large_cap', 'risk_level': 'low', 'expense_ratio': 0.09},
            'QQQ': {'name': 'Invesco QQQ Trust', 'category': 'tech_growth', 'risk_level': 'medium', 'expense_ratio': 0.20},
            'VTI': {'name': 'Vanguard Total Stock Market', 'category': 'total_market', 'risk_level': 'low', 'expense_ratio': 0.03},
            'VUG': {'name': 'Vanguard Growth ETF', 'category': 'growth', 'risk_level': 'medium', 'expense_ratio': 0.04},
            'VTV': {'name': 'Vanguard Value ETF', 'category': 'value', 'risk_level': 'low', 'expense_ratio': 0.04},
            'BND': {'name': 'Vanguard Total Bond Market', 'category': 'bonds', 'risk_level': 'very_low', 'expense_ratio': 0.03},
            'VXUS': {'name': 'Vanguard Total International', 'category': 'international', 'risk_level': 'medium', 'expense_ratio': 0.08},
            'VNQ': {'name': 'Vanguard Real Estate ETF', 'category': 'real_estate', 'risk_level': 'medium', 'expense_ratio': 0.12},
            'VBR': {'name': 'Vanguard Small-Cap Value', 'category': 'small_cap', 'risk_level': 'high', 'expense_ratio': 0.07},
            'GLD': {'name': 'SPDR Gold Shares', 'category': 'commodities', 'risk_level': 'medium', 'expense_ratio': 0.40}
        }
    
    def _load_fi_data(self):
        """Load Fi data from JSON file"""
        try:
            if os.path.exists(self.fi_data_file):
                with open(self.fi_data_file, 'r') as f:
                    self.fi_data = json.load(f)
                self.is_loaded = True
                print(f"✅ Enhanced Fi data loaded successfully!")
                print(f"📊 Portfolio Value: ₹{self.fi_data['portfolio']['total_market_value']:,.2f}")
            else:
                print(f"⚠️ Fi data file not found: {self.fi_data_file}")
                self.is_loaded = False
        except Exception as e:
            print(f"❌ Error loading Fi data: {e}")
            self.is_loaded = False
    
    def determine_amount_category(self, amount: float) -> str:
        """Determine investment amount category"""
        for category, config in self.amount_strategies.items():
            if config["min_amount"] <= amount <= config["max_amount"]:
                return category
        return "portfolio"
    
    def get_portfolio_data(self) -> Dict[str, Any]:
        """Get comprehensive portfolio data"""
        if not self.is_loaded:
            return self._get_demo_data()
        
        portfolio_section = self.fi_data.get('portfolio', {})
        
        return {
            "user_id": self.fi_data.get('user_id', 'unknown'),
            "total_value": float(portfolio_section.get('total_market_value', 0)),
            "cash_balance": float(portfolio_section.get('cash_balance', 0)),
            "holdings": [
                {
                    "symbol": holding.get('symbol', ''),
                    "company_name": holding.get('company_name', ''),
                    "quantity": float(holding.get('quantity', 0)),
                    "current_price": float(holding.get('current_price', 0)),
                    "market_value": float(holding.get('market_value', 0)),
                    "cost_basis": float(holding.get('cost_basis', 0)),
                    "unrealized_gain_loss": float(holding.get('unrealized_pnl', 0)),
                    "allocation_percentage": float(holding.get('allocation_percent', 0)),
                    "sector": holding.get('sector', 'Unknown'),
                    "risk_level": holding.get('risk_level', 'medium'),
                    "emotional_impact": holding.get('emotional_impact', 'medium')
                }
                for holding in portfolio_section.get('holdings', [])
            ],
            "performance": {
                "total_return": float(portfolio_section.get('total_return', 0)),
                "total_return_percentage": float(portfolio_section.get('total_return_percent', 0)),
                "day_change": float(portfolio_section.get('day_change', 0)),
                "day_change_percentage": float(portfolio_section.get('day_change_percent', 0)),
                "ytd_change": float(portfolio_section.get('ytd_change', 0))
            }
        }
    
    def get_behavioral_history(self) -> Dict[str, Any]:
        """Get user's behavioral patterns and history"""
        if not self.is_loaded:
            return self._get_demo_behavioral()
        
        return self.fi_data.get('behavioral_history', {})
    
    def get_psychological_profile(self) -> Dict[str, Any]:
        """Get user's psychological profile"""
        if not self.is_loaded:
            return {}
        
        return self.fi_data.get('psychological_profile', {})
    
    def get_transaction_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get enhanced transaction history with emotional context"""
        if not self.is_loaded:
            return []
        
        transactions_section = self.fi_data.get('transactions', [])
        
        return [
            {
                "transaction_id": txn.get('transaction_id', ''),
                "date": txn.get('date', ''),
                "type": txn.get('transaction_type', '').upper(),
                "symbol": txn.get('symbol', ''),
                "quantity": float(txn.get('quantity', 0)) if txn.get('quantity') else None,
                "price": float(txn.get('price', 0)) if txn.get('price') else None,
                "total_amount": float(txn.get('total_amount', 0)),
                "emotional_tag": txn.get('emotional_tag', 'neutral'),
                "confidence_level": txn.get('confidence_level', 5),
                "description": txn.get('description', '')
            }
            for txn in transactions_section
        ]
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get enhanced account summary"""
        if not self.is_loaded:
            return self._get_demo_account()
        
        account_section = self.fi_data.get('account', {})
        profile_section = self.fi_data.get('user_profile', {})
        
        return {
            "account_id": account_section.get('account_id', ''),
            "user_id": self.fi_data.get('user_id', ''),
            "net_worth": float(account_section.get('net_worth', 0)),
            "available_cash": float(account_section.get('available_cash', 0)),
            "buying_power": float(account_section.get('buying_power', 0)),
            "investment_experience": profile_section.get('investment_experience', 'intermediate'),
            "risk_tolerance": profile_section.get('risk_tolerance', 'moderate'),
            "investment_goals": profile_section.get('investment_goals', ['long_term_growth']),
            "time_horizon": profile_section.get('time_horizon', '10+ years'),
            "age_range": profile_section.get('age_range', '30-40'),
            "income_stability": profile_section.get('income_stability', 'stable'),
            "financial_knowledge": profile_section.get('financial_knowledge', 'good')
        }
    
    def get_market_data(self) -> Dict[str, Any]:
        """Get REAL-TIME market data from Gemini"""
        # Try to get live market data from Gemini first
        if self.market_client:
            try:
                real_time_data = self.market_client.get_real_time_market_data()
                return {
                    "market_indicators": real_time_data
                }
            except Exception as e:
                print(f"Error getting Gemini market data: {e}")
        
        # Fallback to static data
        if self.is_loaded:
            market_section = self.fi_data.get('market_data', {})
            return {
                "market_indicators": {
                    "vix": float(market_section.get('vix', 20.0)),
                    "fear_greed_index": int(market_section.get('fear_greed_index', 50)),
                    "market_trend": market_section.get('market_trend', 'neutral'),
                    "sector_performance": market_section.get('sector_performance', {})
                }
            }
        
        return self._get_demo_market()
    
    def get_personalized_recommendations(self, investment_amount: float) -> List[Dict[str, Any]]:
        """Get AMOUNT-AWARE personalized investment recommendations"""
        print(f"🎯 Generating recommendations for ₹{investment_amount:,.2f}")
        
        # Get user profile and market data
        account = self.get_account_summary()
        portfolio = self.get_portfolio_data()
        market_data = self.get_market_data()
        
        # Determine amount category and risk profile
        amount_category = self.determine_amount_category(investment_amount)
        risk_tolerance = account.get('risk_tolerance', 'moderate')
        
        print(f"📊 Amount category: {amount_category}, Risk tolerance: {risk_tolerance}")
        
        # Try Gemini-powered recommendations first
        if self.market_client:
            try:
                gemini_recommendations = self._get_gemini_amount_aware_recommendations(
                    investment_amount, account, portfolio, market_data, amount_category
                )
                if gemini_recommendations:
                    print(f"✅ Generated {len(gemini_recommendations)} Gemini recommendations")
                    return gemini_recommendations
            except Exception as e:
                print(f"⚠️ Gemini recommendations failed: {e}")
        
        # Fallback to amount-aware static recommendations
        return self._get_amount_aware_static_recommendations(
            investment_amount, risk_tolerance, amount_category
        )
    
    def _get_gemini_amount_aware_recommendations(self, investment_amount: float, account: Dict, 
                                               portfolio: Dict, market_data: Dict, amount_category: str) -> List[Dict]:
        """Get Gemini-powered amount-aware recommendations"""
        strategy_config = self.amount_strategies[amount_category]
        market_indicators = market_data.get('market_indicators', {})
        
        # Create amount-specific prompt for Gemini
        prompt = f"""
Generate {strategy_config['max_positions']} investment recommendations for ₹{investment_amount:,.2f}.

AMOUNT STRATEGY: {amount_category.upper()} - {strategy_config['focus']}
MAX POSITIONS: {strategy_config['max_positions']}

USER PROFILE:
- Risk Tolerance: {account.get('risk_tolerance', 'moderate')}
- Experience: {account.get('investment_experience', 'intermediate')}
- Current Portfolio: ₹{portfolio['total_value']:,.2f}

MARKET CONDITIONS:
- VIX: {market_indicators.get('vix', 20)}
- Fear/Greed: {market_indicators.get('fear_greed_index', 50)}/100
- Trend: {market_indicators.get('market_trend', 'neutral')}

AMOUNT-SPECIFIC RULES:
{self._get_amount_specific_rules(investment_amount, amount_category)}

Available ETFs: SPY, QQQ, VTI, VUG, VTV, BND, VXUS, VNQ, VBR, GLD

Return recommendations in this JSON format:
[
  {{
    "symbol": "ETF_SYMBOL",
    "name": "Full Name",
    "allocation_percentage": percentage,
    "investment_amount": dollar_amount,
    "rationale": "Why this fits ₹{investment_amount:,.2f} investment",
    "risk_level": "low/medium/high",
    "category": "core/satellite/growth",
    "suitability_score": 1-10
  }}
]

Ensure investment_amount values sum to exactly ₹{investment_amount:,.2f}.
"""
        
        try:
            response = self.market_client.model.generate_content(prompt)
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
            
            # Format to expected structure
            formatted_recommendations = []
            for rec in recommendations:
                symbol = rec.get('symbol', '')
                fund_info = self.fund_details.get(symbol, {})
                
                formatted_rec = {
                    "fund": {
                        "symbol": symbol,
                        "name": rec.get('name', fund_info.get('name', symbol)),
                        "category": fund_info.get('category', 'unknown'),
                        "risk_level": rec.get('risk_level', fund_info.get('risk_level', 'medium')),
                        "min_investment": 1,
                        "expense_ratio": fund_info.get('expense_ratio', 0.05),
                        "historical_volatility": 15.0,
                        "emotional_suitability": self._determine_emotional_suitability(rec.get('risk_level', 'medium')),
                        "description": rec.get('rationale', ''),
                        "current_outlook": "neutral"
                    },
                    "suitability_score": float(rec.get('suitability_score', 7.0)),
                    "suggested_amount": float(rec.get('investment_amount', investment_amount * 0.33)),
                    "rationale": rec.get('rationale', ''),
                    "market_timing": f"Suitable for {amount_category} investment strategy",
                    "risk_assessment": rec.get('risk_level', 'medium')
                }
                formatted_recommendations.append(formatted_rec)
            
            return formatted_recommendations
            
        except Exception as e:
            print(f"Error in Gemini amount-aware recommendations: {e}")
            return []
    
    def _get_amount_specific_rules(self, amount: float, category: str) -> str:
        """Get amount-specific investment rules"""
        rules = {
            "micro": f"For ₹{amount:,.2f}: Recommend only 1 ETF. Focus on lowest fees. No individual stocks.",
            "small": f"For ₹{amount:,.2f}: Max 2 positions. 70/30 or 80/20 split. Core + satellite approach.",
            "medium": f"For ₹{amount:,.2f}: Max 4 positions. Include bonds for diversification. Can add growth component.",
            "large": f"For ₹{amount:,.2f}: Max 6 positions. Full asset class diversification. Can include individual stocks.",
            "portfolio": f"For ₹{amount:,.2f}: Max 10 positions. Institutional approach with alternatives."
        }
        return rules.get(category, f"Standard diversification for ₹{amount:,.2f}")
    
    def _get_amount_aware_static_recommendations(self, investment_amount: float, 
                                               risk_tolerance: str, amount_category: str) -> List[Dict]:
        """Fallback static recommendations based on amount"""
        
        # Normalize risk tolerance
        if 'conservative' in risk_tolerance.lower():
            risk_profile = 'conservative'
        elif 'aggressive' in risk_tolerance.lower():
            risk_profile = 'aggressive'
        else:
            risk_profile = 'moderate'
        
        # Get appropriate allocation based on amount and risk
        allocations = self.investment_options[risk_profile][amount_category]
        
        recommendations = []
        for allocation in allocations:
            symbol = allocation['symbol']
            percentage = allocation['allocation']
            dollar_amount = round((investment_amount * percentage / 100), 2)
            
            fund_info = self.fund_details.get(symbol, {})
            
            recommendation = {
                "fund": {
                    "symbol": symbol,
                    "name": fund_info.get('name', symbol),
                    "category": fund_info.get('category', 'unknown'),
                    "risk_level": fund_info.get('risk_level', 'medium'),
                    "min_investment": 1,
                    "expense_ratio": fund_info.get('expense_ratio', 0.05),
                    "historical_volatility": 15.0,
                    "emotional_suitability": self._determine_emotional_suitability(fund_info.get('risk_level', 'medium')),
                    "description": f"Optimal for {amount_category} {risk_profile} strategy",
                    "current_outlook": "neutral"
                },
                "suitability_score": 8.0,
                "suggested_amount": dollar_amount,
                "rationale": f"₹{investment_amount:,.2f} {amount_category} allocation: {percentage}% fits {risk_profile} profile",
                "market_timing": f"Appropriate for {amount_category} investment size",
                "risk_assessment": fund_info.get('risk_level', 'medium')
            }
            recommendations.append(recommendation)
        
        print(f"✅ Generated {len(recommendations)} amount-aware static recommendations")
        return recommendations
    
    def get_stock_analysis_from_gemini(self, symbol: str) -> Dict[str, Any]:
        """Get real-time stock analysis from Gemini"""
        if self.market_client:
            try:
                return self.market_client.get_stock_analysis(symbol)
            except Exception as e:
                print(f"Error getting Gemini stock analysis for {symbol}: {e}")
        
        return {"symbol": symbol, "error": "Analysis unavailable"}
    
    def get_market_sentiment_for_investment(self, user_message: str, amount: float) -> str:
        """Get market timing analysis from Gemini"""
        if self.market_client:
            try:
                return self.market_client.analyze_market_sentiment_for_investment(user_message, amount)
            except Exception as e:
                print(f"Error getting market sentiment: {e}")
        
        return "Market analysis suggests a balanced approach to investing given current conditions."
    
    def analyze_portfolio_risk(self) -> Dict[str, Any]:
        """Analyze portfolio risk characteristics"""
        portfolio = self.get_portfolio_data()
        
        total_value = portfolio['total_value']
        high_risk_exposure = 0
        medium_risk_exposure = 0
        low_risk_exposure = 0
        
        for holding in portfolio['holdings']:
            if holding['risk_level'] == 'high':
                high_risk_exposure += holding['market_value']
            elif holding['risk_level'] == 'medium':
                medium_risk_exposure += holding['market_value']
            else:
                low_risk_exposure += holding['market_value']
        
        return {
            "total_value": total_value,
            "high_risk_percent": (high_risk_exposure / total_value) * 100 if total_value > 0 else 0,
            "medium_risk_percent": (medium_risk_exposure / total_value) * 100 if total_value > 0 else 0,
            "low_risk_percent": (low_risk_exposure / total_value) * 100 if total_value > 0 else 0,
            "risk_score": self._calculate_risk_score(portfolio)
        }
    
    def _calculate_risk_score(self, portfolio: Dict) -> float:
        """Calculate overall portfolio risk score (1-10)"""
        risk_weights = {'high': 3, 'medium': 2, 'low': 1}
        total_weight = 0
        total_value = 0
        
        for holding in portfolio['holdings']:
            weight = risk_weights.get(holding['risk_level'], 2)
            total_weight += weight * holding['market_value']
            total_value += holding['market_value']
        
        if total_value == 0:
            return 5.0
        
        normalized_score = (total_weight / total_value) * 3.33  # Scale to 1-10
        return min(10.0, max(1.0, normalized_score))
    
    def _determine_emotional_suitability(self, risk_level: str) -> str:
        """Determine emotional suitability based on risk level"""
        if risk_level in ["very_low", "low"]:
            return "stress_averse"
        elif risk_level == "high":
            return "high_risk_comfort"
        else:
            return "growth_focused"
    
    def _get_demo_data(self):
        """Fallback demo data"""
        return {
            "user_id": "demo_user",
            "total_value": 100000.00,
            "cash_balance": 5000.00,
            "holdings": [],
            "performance": {
                "total_return": 5000.00,
                "total_return_percentage": 5.26,
                "day_change": -500.00,
                "day_change_percentage": -0.50,
                "ytd_change": 5000.00
            }
        }
    
    def _get_demo_behavioral(self):
        """Demo behavioral data"""
        return {
            "emotional_patterns": {
                "risk_comfort": "moderate",
                "volatility_tolerance": 5,
                "loss_aversion_score": 6,
                "fomo_tendency": 5,
                "patience_level": 6
            }
        }
    
    def _get_demo_account(self):
        """Fallback demo account"""
        return {
            "account_id": "demo_acc",
            "user_id": "demo_user",
            "net_worth": 120000.0,
            "available_cash": 5000.0,
            "buying_power": 10000.0,
            "investment_experience": "beginner",
            "risk_tolerance": "moderate",
            "investment_goals": ["long_term_growth"],
            "time_horizon": "10+ years",
            "age_range": "25-35"
        }
    
    def _get_demo_market(self):
        """Fallback demo market data"""
        return {
            "market_indicators": {
                "vix": 18.5,
                "fear_greed_index": 45,
                "market_trend": "neutral",
                "sector_performance": {}
            }
        }