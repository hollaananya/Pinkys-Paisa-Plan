import google.generativeai as genai
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.time_machine_fi_client import TimeMachineFiClient
import math

load_dotenv()

class TimeMachineAgent:
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
                print("✅ Time Machine Agent - Gemini API connected successfully!")
                
            except Exception as e:
                print(f"⚠️ Time Machine Agent - Gemini API error: {e}")
                self.gemini_available = False
        else:
            print("⚠️ Time Machine Agent - No Gemini API key found")
            self.gemini_available = False
        
        self.fi_client = TimeMachineFiClient()
        
        # Time Machine scenario patterns
        self.scenario_patterns = {
            'salary_hike': {
                'keywords': ['salary hike', 'salary increase', 'promotion', 'raise', 'pay increase', 'income boost'],
                'type': 'income_change',
                'confidence_boost': 0.9
            },
            'house_purchase': {
                'keywords': ['buy house', 'buying house', 'home loan', 'property', 'real estate', 'house in'],
                'type': 'major_purchase',
                'confidence_boost': 0.9
            },
            'family_planning': {
                'keywords': ['baby', 'child', 'expecting', 'pregnancy', 'new family member', 'having a child'],
                'type': 'life_event',
                'confidence_boost': 0.85
            },
            'job_switch': {
                'keywords': ['job switch', 'changing job', 'new job', 'startup', 'no epf', 'no pf'],
                'type': 'career_change',
                'confidence_boost': 0.8
            },
            'education_goal': {
                'keywords': ['mba', 'education', 'higher studies', 'masters', 'abroad study', 'university'],
                'type': 'education_investment',
                'confidence_boost': 0.85
            },
            'loan_prepayment': {
                'keywords': ['pay off loan', 'prepay', 'close loan', 'early repayment', 'loan closure'],
                'type': 'debt_optimization',
                'confidence_boost': 0.8
            },
            'retirement_planning': {
                'keywords': ['retirement', 'retire early', 'pension', 'post-retirement', 'financial independence'],
                'type': 'long_term_goal',
                'confidence_boost': 0.9
            },
            'emergency_fund': {
                'keywords': ['emergency fund', 'contingency', 'job loss', 'medical emergency', 'unexpected expense'],
                'type': 'risk_management',
                'confidence_boost': 0.8
            }
        }
        
        # Financial calculation constants
        self.INFLATION_RATE = 0.06  # 6% default inflation
        self.SIP_RETURN_RATE = 0.12  # 12% expected SIP returns
        self.EMERGENCY_FUND_MONTHS = 6
        self.HOME_LOAN_RATE = 0.085  # 8.5% home loan rate
        self.EDUCATION_INFLATION = 0.08  # 8% education inflation
        
        # Indian financial context
        self.EPF_RATE = 0.085  # 8.5% EPF returns
        self.PPF_RATE = 0.075  # 7.5% PPF returns
        self.NPS_RETURN_RATE = 0.10  # 10% NPS expected returns
        
    def extract_financial_parameters(self, user_message: str) -> Dict[str, Any]:
        """Extract financial parameters from user message"""
        message_lower = user_message.lower()
        
        # Extract amounts (Indian currency patterns)
        amount_patterns = [
            r'₹(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|l)',  # ₹50 lakh
            r'₹(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:crore|cr)',  # ₹2 crore
            r'₹(\d+(?:,\d+)*(?:\.\d+)?)',  # ₹50000
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:lakh|l)',  # 50 lakh
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:crore|cr)',  # 2 crore
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*rupees?',  # 50000 rupees
        ]
        
        extracted_amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                try:
                    amount_str = match.replace(',', '')
                    amount = float(amount_str)
                    
                    # Convert lakh/crore to absolute values
                    if 'lakh' in pattern or 'l' in pattern:
                        amount *= 100000  # 1 lakh = 1,00,000
                    elif 'crore' in pattern or 'cr' in pattern:
                        amount *= 10000000  # 1 crore = 1,00,00,000
                    
                    extracted_amounts.append(amount)
                except ValueError:
                    continue
        
        # Extract time periods
        time_patterns = [
            r'(\d+)\s*(?:year|yr)s?',
            r'(\d+)\s*(?:month|mon)s?',
            r'in\s*(\d+)\s*(?:year|yr)s?',
            r'next\s*(\d+)\s*(?:year|yr)s?',
        ]
        
        extracted_times = []
        for pattern in time_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                try:
                    time_value = int(match)
                    if 'month' in pattern:
                        time_value = time_value / 12  # Convert to years
                    extracted_times.append(time_value)
                except ValueError:
                    continue
        
        # Extract salary/income information
        salary_patterns = [
            r'(\d+)%\s*(?:salary\s*hike|raise|increase)',
            r'₹(\d+(?:,\d+)*)\s*(?:salary|income)',
            r'(\d+(?:,\d+)*)\s*(?:salary|income)',
        ]
        
        salary_info = {}
        for pattern in salary_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                try:
                    value = matches[0].replace(',', '')
                    if '%' in pattern:
                        salary_info['hike_percentage'] = float(value)
                    else:
                        salary_info['amount'] = float(value)
                except ValueError:
                    continue
        
        return {
            'amounts': extracted_amounts,
            'time_periods': extracted_times,
            'salary_info': salary_info,
            'has_amounts': len(extracted_amounts) > 0,
            'has_timeline': len(extracted_times) > 0
        }
    
    def classify_scenario(self, user_message: str) -> Dict[str, Any]:
        """Classify the time machine scenario"""
        message_lower = user_message.lower()
        financial_params = self.extract_financial_parameters(user_message)
        
        # Check for scenario patterns
        detected_scenarios = []
        for scenario_name, config in self.scenario_patterns.items():
            for keyword in config['keywords']:
                if keyword in message_lower:
                    detected_scenarios.append({
                        'scenario': scenario_name,
                        'type': config['type'],
                        'confidence': config['confidence_boost'],
                        'keyword_matched': keyword
                    })
                    break
        
        # Determine primary scenario
        if detected_scenarios:
            # Sort by confidence and take the highest
            primary_scenario = max(detected_scenarios, key=lambda x: x['confidence'])
            
            return {
                'primary_scenario': primary_scenario['scenario'],
                'scenario_type': primary_scenario['type'],
                'confidence': primary_scenario['confidence'],
                'detected_scenarios': detected_scenarios,
                'financial_params': financial_params,
                'requires_calculation': True,
                'complexity': self._determine_complexity(financial_params, detected_scenarios)
            }
        else:
            # General financial planning query
            return {
                'primary_scenario': 'general_planning',
                'scenario_type': 'general',
                'confidence': 0.6,
                'detected_scenarios': [],
                'financial_params': financial_params,
                'requires_calculation': financial_params['has_amounts'] or financial_params['has_timeline'],
                'complexity': 'simple'
            }
    
    def _determine_complexity(self, financial_params: Dict, scenarios: List) -> str:
        """Determine scenario complexity"""
        complexity_score = 0
        
        if len(scenarios) > 1:
            complexity_score += 2
        if financial_params['has_amounts'] and financial_params['has_timeline']:
            complexity_score += 2
        if len(financial_params['amounts']) > 1:
            complexity_score += 1
        if financial_params.get('salary_info'):
            complexity_score += 1
        
        if complexity_score >= 4:
            return 'complex'
        elif complexity_score >= 2:
            return 'moderate'
        else:
            return 'simple'
    
    def calculate_future_value_sip(self, monthly_amount: float, years: float, 
                                  annual_return: float = 0.12) -> Tuple[float, float]:
        """Calculate future value of SIP"""
        monthly_return = annual_return / 12
        months = years * 12
        
        if monthly_return == 0:
            future_value = monthly_amount * months
            total_invested = monthly_amount * months
        else:
            future_value = monthly_amount * (((1 + monthly_return) ** months - 1) / monthly_return)
            total_invested = monthly_amount * months
        
        return future_value, total_invested
    
    def calculate_loan_emi(self, principal: float, annual_rate: float, years: float) -> float:
        """Calculate EMI for a loan"""
        monthly_rate = annual_rate / 12
        months = years * 12
        
        if monthly_rate == 0:
            return principal / months if months > 0 else 0
        
        denominator = (((1 + monthly_rate) ** months) - 1)
        if denominator == 0:
            return float('inf') 
            
        emi = principal * monthly_rate * ((1 + monthly_rate) ** months) / denominator
        return emi
    
    def project_inflation_adjusted_cost(self, current_cost: float, years: float, 
                                      inflation_rate: float = None) -> float:
        """Project future cost considering inflation"""
        if inflation_rate is None:
            inflation_rate = self.INFLATION_RATE
        
        future_cost = current_cost * ((1 + inflation_rate) ** years)
        return future_cost
    
    def analyze_salary_hike_scenario(self, user_message: str, financial_params: Dict) -> Dict[str, Any]:
        """Analyze salary hike impact scenario"""
        current_snapshot = self.fi_client.get_current_financial_snapshot()

        estimated_monthly_income = current_snapshot['income']['total_monthly_income']
        current_monthly_savings = current_snapshot['savings']['current_monthly_savings']

        hike_percentage = financial_params.get('salary_info', {}).get('hike_percentage', 25)

        new_monthly_income = estimated_monthly_income * (1 + hike_percentage / 100)
        additional_income = new_monthly_income - estimated_monthly_income
        
        scenario_results = {
            'current_monthly_income': estimated_monthly_income,
            'new_monthly_income': new_monthly_income,
            'additional_monthly_income': additional_income,
            'hike_percentage': hike_percentage,
            'recommendations': {
                'additional_sip': additional_income * 0.60,  # 60% of additional income to SIP
                'emergency_fund_boost': additional_income * 0.20,  # 20% to emergency fund
                'goal_acceleration': additional_income * 0.20,  # 20% to specific goals
            }
        }
        
        if additional_income > 0:
            home_goal_timeline = self._calculate_home_goal_acceleration(
                additional_income * 0.60, current_monthly_savings
            )
            scenario_results['goal_acceleration_impact'] = home_goal_timeline
        
        return scenario_results
    
    def analyze_house_purchase_scenario(self, user_message: str, financial_params: Dict) -> Dict[str, Any]:
        """Analyze house purchase feasibility"""
        amounts = financial_params.get('amounts', [])
        time_periods = financial_params.get('time_periods', [])
        
        if not amounts or not time_periods:
            return {'error': 'Missing house price or timeline information'}
        
        house_price = amounts[0]
        timeline_years = time_periods[0]
        
        current_snapshot = self.fi_client.get_current_financial_snapshot()
        
        current_total_portfolio_value = current_snapshot['assets']['total_portfolio_value']
        available_cash_for_downpayment = current_snapshot['assets']['emergency_fund'] * 0.5 
        
        monthly_savings = financial_params['amounts'][1] if len(financial_params['amounts']) > 1 else current_snapshot['savings']['current_monthly_savings']
        monthly_savings = max(0, monthly_savings) 
        
        current_savings_corpus_for_house = current_total_portfolio_value + available_cash_for_downpayment 

        future_savings_from_monthly_sip, _ = self.calculate_future_value_sip(
            monthly_savings, timeline_years, self.SIP_RETURN_RATE
        )
        
        total_available = current_savings_corpus_for_house * ((1 + self.SIP_RETURN_RATE) ** timeline_years) + future_savings_from_monthly_sip
        
        inflated_house_price = self.project_inflation_adjusted_cost(
            house_price, timeline_years, inflation_rate=0.05  
        )
        
        down_payment_required = inflated_house_price * 0.20
        loan_amount = inflated_house_price * 0.80
        
        shortfall_or_surplus = total_available - down_payment_required 
        
        loan_emi = self.calculate_loan_emi(loan_amount, self.HOME_LOAN_RATE, 20)  
        
        current_monthly_income = current_snapshot['income']['total_monthly_income']
        emi_to_income_ratio = (loan_emi / current_monthly_income) * 100 if current_monthly_income > 0 else float('inf')

        return {
            'house_price_today': house_price,
            'house_price_future': inflated_house_price,
            'timeline_years': timeline_years,
            'monthly_savings': monthly_savings,
            'total_savings_accumulated': total_available,
            'down_payment_required': down_payment_required,
            'loan_amount': loan_amount,
            'loan_emi': loan_emi,
            'shortfall_or_surplus': shortfall_or_surplus,
            'is_affordable': shortfall_or_surplus >= 0,
            'recommendation': self._generate_house_recommendation(shortfall_or_surplus, monthly_savings, timeline_years) 
        }
    
    def analyze_family_planning_scenario(self, user_message: str, financial_params: Dict) -> Dict[str, Any]:
        """Analyze financial impact of new family member"""
        current_snapshot = self.fi_client.get_current_financial_snapshot()
        
        current_emergency_fund = current_snapshot['assets']['emergency_fund']
        current_monthly_expenses = current_snapshot['expenses']['monthly_expenses']
        
        immediate_costs = {
            'hospital_delivery': 150000,  
            'initial_baby_items': 50000,  
            'insurance_premium_increase': 25000,  
        }
        
        monthly_ongoing_costs = {
            'baby_care_products': 8000,  
            'medical_checkups': 3000,  
            'childcare_savings': 5000,  
        }
        
        new_monthly_expenses = current_monthly_expenses + sum(monthly_ongoing_costs.values())
        new_emergency_fund_target = new_monthly_expenses * self.EMERGENCY_FUND_MONTHS
        
        emergency_fund_gap = max(0, new_emergency_fund_target - current_emergency_fund)
        
        return {
            'immediate_costs': immediate_costs,
            'total_immediate_cost': sum(immediate_costs.values()),
            'monthly_ongoing_costs': monthly_ongoing_costs,
            'total_monthly_increase': sum(monthly_ongoing_costs.values()),
            'current_emergency_fund': current_emergency_fund,
            'new_emergency_fund_target': new_emergency_fund_target,
            'emergency_fund_gap': emergency_fund_gap,
            'preparation_timeline': '9-12 months', 
            'recommendations': {
                'immediate_savings_target': sum(immediate_costs.values()) + emergency_fund_gap,
                'monthly_savings_adjustment': sum(monthly_ongoing_costs.values()),
                'insurance_review': 'Increase health and term insurance coverage'
            }
        }
    
    def analyze_job_switch_scenario(self, user_message: str, financial_params: Dict) -> Dict[str, Any]:
        """Analyze job switch with different benefits"""
        salary_info = financial_params.get('salary_info', {})
        hike_percentage = salary_info.get('hike_percentage', 30)
        
        current_snapshot = self.fi_client.get_current_financial_snapshot()
        
        estimated_monthly_income = current_snapshot['income']['total_monthly_income']
        current_epf_employee_contribution = current_snapshot['income']['epf_contribution'] 
        
        new_monthly_income = estimated_monthly_income * (1 + hike_percentage / 100)
        
        total_current_epf_contribution_monthly = current_epf_employee_contribution * 2
        
        lost_epf_monthly = total_current_epf_contribution_monthly
        
        years_to_retirement = current_snapshot['goals'].get('retirement', {}).get('timeline_years', 30) 

        current_epf_path_future_value, _ = self.calculate_future_value_sip(
            total_current_epf_contribution_monthly,
            years_to_retirement,
            self.EPF_RATE
        )

        required_private_investment_monthly = lost_epf_monthly 

        private_investment_future_value, _ = self.calculate_future_value_sip(
            required_private_investment_monthly,
            years_to_retirement,
            self.SIP_RETURN_RATE  
        )
        
        retirement_corpus_change = private_investment_future_value - current_epf_path_future_value

        additional_monthly_income = new_monthly_income - estimated_monthly_income
        net_monthly_benefit = additional_monthly_income - required_private_investment_monthly
        
        return {
            'current_monthly_income': estimated_monthly_income,
            'new_monthly_income': new_monthly_income,
            'salary_hike_percentage': hike_percentage,
            'lost_epf_monthly': lost_epf_monthly,
            'required_private_investment_monthly': required_private_investment_monthly,
            'net_monthly_benefit': net_monthly_benefit,
            'retirement_projections': {
                'years_to_retirement': years_to_retirement,
                'with_epf': current_epf_path_future_value,
                'with_private_investment': private_investment_future_value,
                'difference': retirement_corpus_change
            },
            'recommendations': {
                'ppf_investment_annual': min(150000, required_private_investment_monthly * 12),  
                'nps_option_annual': required_private_investment_monthly * 0.5 * 12, 
                'mutual_fund_sip_annual': required_private_investment_monthly * 0.5 * 12 
            },
            'is_beneficial': net_monthly_benefit > 0
        }
    
    def analyze_education_goal_scenario(self, user_message: str, financial_params: Dict) -> Dict[str, Any]:
        """Analyze higher education funding scenario"""
        amounts = financial_params.get('amounts', [])
        time_periods = financial_params.get('time_periods', [])
        
        if not amounts or not time_periods:
            return {'error': 'Missing education cost or timeline information'}
        
        education_cost_today = amounts[0]
        timeline_years = time_periods[0]
        
        current_snapshot = self.fi_client.get_current_financial_snapshot()
        current_education_corpus = current_snapshot['goals'].get('child_education', {}).get('current_progress', 0)
        
        education_inflation = self.EDUCATION_INFLATION
        future_education_cost = self.project_inflation_adjusted_cost(
            education_cost_today, timeline_years, education_inflation
        )
        
        is_abroad = any(keyword in user_message.lower() for keyword in ['abroad', 'us', 'usa', 'uk', 'canada'])
        if is_abroad:
            usd_rate = 83  
            currency_appreciation_rate = 0.03  
            currency_factor = (1 + currency_appreciation_rate) ** timeline_years
            future_education_cost *= currency_factor
        
        future_value_current_corpus = current_education_corpus * ((1 + self.SIP_RETURN_RATE) ** timeline_years)
        
        monthly_sip_required_total = self._calculate_sip_for_target(
            future_education_cost, timeline_years, self.SIP_RETURN_RATE
        )
        
        remaining_requirement = max(0, future_education_cost - future_value_current_corpus)
        adjusted_monthly_sip = self._calculate_sip_for_target(
            remaining_requirement, timeline_years, self.SIP_RETURN_RATE
        )
        
        if timeline_years > 5:
            equity_allocation = 0.80
            debt_allocation = 0.20
        elif timeline_years > 3:
            equity_allocation = 0.70
            debt_allocation = 0.30
        else:
            equity_allocation = 0.50
            debt_allocation = 0.50
        
        return {
            'education_cost_today': education_cost_today,
            'education_cost_future': future_education_cost,
            'timeline_years': timeline_years,
            'is_abroad_education': is_abroad,
            'monthly_sip_required': monthly_sip_required_total, 
            'current_portfolio_contribution': future_value_current_corpus, 
            'adjusted_monthly_sip': adjusted_monthly_sip, 
            'total_investment_needed': adjusted_monthly_sip * 12 * timeline_years, 
            'recommendations': {
                'equity_allocation': equity_allocation,  
                'debt_allocation': debt_allocation,
                'suggested_funds': self._suggest_education_funds(timeline_years)
            }
        }
    
    def analyze_loan_prepayment_scenario(self, user_message: str, financial_params: Dict) -> Dict[str, Any]:
        """Analyze loan prepayment vs investment scenario"""
        amounts = financial_params.get('amounts', [])
        
        if not amounts:
            return {'error': 'Missing loan amount information'}
        
        outstanding_loan = amounts[0]
        
        loan_rate = 0.10  
        remaining_years = financial_params['time_periods'][0] if financial_params['has_timeline'] and financial_params['time_periods'] else 5
        
        current_emi = self.calculate_loan_emi(outstanding_loan, loan_rate, remaining_years)
        
        investment_rate = self.SIP_RETURN_RATE
        
        total_interest_paid_if_continue = max(0, (current_emi * 12 * remaining_years) - outstanding_loan)
        
        prepayment_amount_lump_sum_option = outstanding_loan 
        
        investment_returns_on_prepayment_amount = prepayment_amount_lump_sum_option * ((1 + investment_rate) ** remaining_years)
        
        net_wealth_continue_emi_path = investment_returns_on_prepayment_amount - total_interest_paid_if_continue
        
        future_wealth_from_emi_investment, _ = self.calculate_future_value_sip(
            current_emi, remaining_years, investment_rate
        )
        
        total_benefit_prepayment_path = future_wealth_from_emi_investment

        net_benefit = total_benefit_prepayment_path - net_wealth_continue_emi_path
        
        recommendation_str = 'prepay' if net_benefit > 0 else 'continue_emi'
        rationale_str = self._generate_loan_prepayment_rationale(loan_rate, investment_rate, net_benefit)

        return {
            'outstanding_loan': outstanding_loan,
            'current_emi': current_emi,
            'loan_interest_rate': loan_rate * 100,
            'remaining_years': remaining_years,
            'total_interest_remaining': total_interest_paid_if_continue,
            'scenarios': {
                'prepayment': {
                    'immediate_outflow': prepayment_amount_lump_sum_option, 
                    'monthly_savings_if_prepaid': current_emi, 
                    'future_wealth_from_emi_investment': future_wealth_from_emi_investment, 
                    'total_benefit_prepayment_path': total_benefit_prepayment_path
                },
                'continue_emi': {
                    'total_interest_cost': total_interest_paid_if_continue,
                    'investment_returns_on_lumpsum': investment_returns_on_prepayment_amount, 
                    'net_wealth_continue_emi_path': net_wealth_continue_emi_path
                }
            },
            'recommendation': recommendation_str,
            'net_benefit': abs(net_benefit), 
            'rationale': rationale_str
        }
    
    def generate_comprehensive_scenario_analysis(self, user_message: str) -> Dict[str, Any]:
        """Main method to analyze any time machine scenario"""
        classification = self.classify_scenario(user_message)
        
        scenario_response = {
            "classification": classification,
            "scenario_analysis": {},
            "financial_projections": {},
            "recommendations": [],
            "action_plan": [],
            "requires_adjustment": False
        }
        
        primary_scenario = classification['primary_scenario']
        financial_params = classification['financial_params']
        
        try:
            if primary_scenario == 'salary_hike':
                scenario_response["scenario_analysis"] = self.analyze_salary_hike_scenario(user_message, financial_params)
                scenario_response["main_response"] = self._generate_salary_hike_response(user_message, scenario_response["scenario_analysis"])
            
            elif primary_scenario == 'house_purchase':
                scenario_response["scenario_analysis"] = self.analyze_house_purchase_scenario(user_message, financial_params)
                scenario_response["main_response"] = self._generate_house_purchase_response(user_message, scenario_response["scenario_analysis"])
            
            elif primary_scenario == 'family_planning':
                scenario_response["scenario_analysis"] = self.analyze_family_planning_scenario(user_message, financial_params)
                scenario_response["main_response"] = self._generate_family_planning_response(user_message, scenario_response["scenario_analysis"])
            
            elif primary_scenario == 'job_switch':
                scenario_response["scenario_analysis"] = self.analyze_job_switch_scenario(user_message, financial_params)
                scenario_response["main_response"] = self._generate_job_switch_response(user_message, scenario_response["scenario_analysis"])
            
            elif primary_scenario == 'education_goal':
                scenario_response["scenario_analysis"] = self.analyze_education_goal_scenario(user_message, financial_params)
                scenario_response["main_response"] = self._generate_education_goal_response(user_message, scenario_response["scenario_analysis"])
            
            elif primary_scenario == 'loan_prepayment':
                scenario_response["scenario_analysis"] = self.analyze_loan_prepayment_scenario(user_message, financial_params)
                scenario_response["main_response"] = self._generate_loan_prepayment_response(user_message, scenario_response["scenario_analysis"])
            
            else:
                scenario_response["main_response"] = self.generate_general_time_machine_response(user_message, classification)
        
        except Exception as e:
            print(f"Error in scenario analysis: {e}")
            scenario_response["main_response"] = self._generate_fallback_general_response(user_message, classification)
        
        return scenario_response
    
    # Helper methods for response generation 
    def _generate_salary_hike_response(self, user_message: str, analysis: Dict) -> str:
        """Generate response for salary hike scenario"""
        if not self.gemini_available:
            return self._generate_fallback_salary_response(analysis)
        
        prompt = f"""
User asked: "{user_message}"

SALARY HIKE ANALYSIS:
- Current Monthly Income: ₹{analysis['current_monthly_income']:,.0f}
- New Monthly Income: ₹{analysis['new_monthly_income']:,.0f}
- Additional Income: ₹{analysis['additional_monthly_income']:,.0f}
- Hike Percentage: {analysis['hike_percentage']}%

RECOMMENDED ALLOCATION:
- Additional SIP: ₹{analysis['recommendations']['additional_sip']:,.0f}/month
- Emergency Fund Boost: ₹{analysis['recommendations']['emergency_fund_boost']:,.0f}/month
- Goal Acceleration: ₹{analysis['recommendations']['goal_acceleration']:,.0f}/month

Provide a comprehensive response that:
1. Celebrates their salary increase
2. Shows how the additional income can accelerate their financial goals
3. Provides specific action steps for the additional ₹{analysis['additional_monthly_income']:,.0f}
4. Mentions goal timeline improvements (if any)

Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}.

Use encouraging tone with practical Indian financial advice. 3-4 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in salary hike response: {e}")
            return self._generate_fallback_salary_response(analysis)
    
    def _generate_house_purchase_response(self, user_message: str, analysis: Dict) -> str:
        """Generate response for house purchase scenario"""
        if not self.gemini_available:
            return self._generate_fallback_house_response(analysis)
        
        prompt = f"""
User asked: "{user_message}"

HOUSE PURCHASE ANALYSIS:
- House Price Today: ₹{analysis['house_price_today']:,.0f}
- House Price Future ({analysis['timeline_years']} years): ₹{analysis['house_price_future']:,.0f}
- Monthly Savings: ₹{analysis['monthly_savings']:,.0f}
- Total Savings Available for Down Payment: ₹{analysis['total_savings_accumulated']:,.0f}
- Down Payment Required: ₹{analysis['down_payment_required']:,.0f}
- Loan Amount: ₹{analysis['loan_amount']:,.0f}
- Estimated Monthly EMI: ₹{analysis['loan_emi']:,.0f}
- Shortfall/Surplus for Down Payment: ₹{analysis['shortfall_or_surplus']:,.0f}
- Is Affordable (Down Payment & EMI): {analysis['is_affordable']}

Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}.

Provide detailed analysis that:
1. Clearly states if the goal is achievable with current plan.
2. Explains the impact of real estate inflation over the timeline.
3. Shows loan EMI affordability relative to income.
4. Provides specific recommendations based on shortfall/surplus and EMI affordability.
5. Suggests adjustments if needed (e.g., increase savings, adjust timeline, lower price).

Use realistic Indian real estate context. 3-4 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in house purchase response: {e}")
            return self._generate_fallback_house_response(analysis)
    
    def _generate_family_planning_response(self, user_message: str, analysis: Dict) -> str:
        """Generate response for family planning scenario"""
        if not self.gemini_available:
            return self._generate_fallback_family_response(analysis)
        
        prompt = f"""
User asked: "{user_message}"

FAMILY PLANNING FINANCIAL ANALYSIS:
- Total Immediate Costs (Delivery, Essentials, Insurance): ₹{analysis['total_immediate_cost']:,.0f}
- Monthly Ongoing Cost Increase (Baby Care, Medical, Education Savings): ₹{analysis['total_monthly_increase']:,.0f}
- Current Emergency Fund: ₹{analysis['current_emergency_fund']:,.0f}
- New Emergency Fund Target (6 months expenses): ₹{analysis['new_emergency_fund_target']:,.0f}
- Emergency Fund Gap: ₹{analysis['emergency_fund_gap']:,.0f}

IMMEDIATE COSTS BREAKDOWN:
- Hospital/Delivery: ₹{analysis['immediate_costs']['hospital_delivery']:,.0f}
- Baby Items: ₹{analysis['immediate_costs']['initial_baby_items']:,.0f}
- Insurance Increase: ₹{analysis['immediate_costs']['insurance_premium_increase']:,.0f}

RECOMMENDATIONS:
- Immediate Savings Target (for initial costs + emergency fund gap): ₹{analysis['recommendations']['immediate_savings_target']:,.0f}
- Monthly Savings Adjustment (for ongoing costs): ₹{analysis['recommendations']['monthly_savings_adjustment']:,.0f}

Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}.

Provide comprehensive family financial planning advice that:
1. Acknowledges the joy of expecting a baby.
2. Breaks down realistic immediate and ongoing costs in an Indian context.
3. Emphasizes the importance of an adequate emergency fund and insurance.
4. Provides a practical timeline for financial preparation.
5. Includes emotional reassurance about affordability with proper planning.

Use a warm, supportive tone with practical advice. 3-4 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in family planning response: {e}")
            return self._generate_fallback_family_response(analysis)
    
    def _generate_job_switch_response(self, user_message: str, analysis: Dict) -> str:
        """Generate response for job switch scenario"""
        if not self.gemini_available:
            return self._generate_fallback_job_response(analysis)
        
        prompt = f"""
User asked: "{user_message}"

JOB SWITCH ANALYSIS:
- Current Monthly Income: ₹{analysis['current_monthly_income']:,.0f}
- New Monthly Income: ₹{analysis['new_monthly_income']:,.0f}
- Salary Increase: {analysis['salary_hike_percentage']}%
- Lost EPF Monthly Contribution (Employer+Employee): ₹{analysis['lost_epf_monthly']:,.0f}
- Required Private Investment (to compensate for lost EPF): ₹{analysis['required_private_investment_monthly']:,.0f}/month
- Net Monthly Benefit (New Salary Increase - Required Private Investment): ₹{analysis['net_monthly_benefit']:,.0f}

RETIREMENT IMPACT (Projected over {analysis['retirement_projections']['years_to_retirement']} years):
- Estimated Corpus with EPF (if current job continued): ₹{analysis['retirement_projections']['with_epf']:,.0f}
- Estimated Corpus with Private Investment (new job path): ₹{analysis['retirement_projections']['with_private_investment']:,.0f}
- Difference in Retirement Corpus: ₹{analysis['retirement_projections']['difference']:,.0f} ({'Gain' if analysis['retirement_projections']['difference'] > 0 else 'Loss'})

RECOMMENDED ANNUAL PRIVATE INVESTMENTS (if no EPF):
- PPF (Public Provident Fund): ₹{analysis['recommendations']['ppf_investment_annual']:,.0f}
- NPS (National Pension System): ₹{analysis['recommendations']['nps_option_annual']:,.0f}
- Mutual Fund SIP: ₹{analysis['recommendations']['mutual_fund_sip_annual']:,.0f}

Overall Decision Status: {"BENEFICIAL" if analysis['is_beneficial'] else "NEEDS CAREFUL CONSIDERATION"}

Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}.

Provide a comprehensive analysis that:
1. Evaluates the overall financial impact of the job switch.
2. Clearly explains the trade-offs between EPF benefits and private investment.
3. Shows the projected impact on long-term retirement planning.
4. Suggests specific alternative investment avenues (like PPF, NPS, Mutual Funds) if EPF is lost.
5. Gives a clear recommendation on the job switch decision.

Use a professional, analytical tone with practical Indian retirement planning context. 3-4 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in job switch response: {e}")
            return self._generate_fallback_job_response(analysis)
    
    def _generate_education_goal_response(self, user_message: str, analysis: Dict) -> str:
        """Generate response for education goal scenario"""
        if not self.gemini_available:
            return self._generate_fallback_education_response(analysis)
        
        prompt = f"""
User asked: "{user_message}"

EDUCATION GOAL ANALYSIS:
- Education Cost Today: ₹{analysis['education_cost_today']:,.0f}
- Future Cost ({analysis['timeline_years']} years, Inflation Adjusted{' & Currency Impact' if analysis['is_abroad_education'] else ''}): ₹{analysis['education_cost_future']:,.0f}
- Total Monthly SIP Required (if starting from scratch): ₹{analysis['monthly_sip_required']:,.0f}
- Your Current Portfolio Contribution (future value of existing corpus): ₹{analysis['current_portfolio_contribution']:,.0f}
- Adjusted Monthly SIP Needed (to meet remaining goal): ₹{analysis['adjusted_monthly_sip']:,.0f}
- Total Investment Needed (Adjusted SIP * years): ₹{analysis['total_investment_needed']:,.0f}
- Is Abroad Education: {analysis['is_abroad_education']}

RECOMMENDED INVESTMENT STRATEGY:
- Equity Allocation: {analysis['recommendations']['equity_allocation']*100}%
- Debt Allocation: {analysis['recommendations']['debt_allocation']*100}%
- Suggested Fund Categories: {', '.join(analysis['recommendations']['suggested_funds'])}

Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}.

Provide comprehensive education funding advice that:
1. Explains the significant impact of education inflation (typically 8% annually) and currency risk (for abroad studies).
2. Clearly outlines the realistic monthly investment requirements.
3. Suggests an appropriate asset allocation strategy based on the investment timeline.
4. Provides specific fund recommendations tailored to the goal's horizon.
5. Emphasizes the advantages of starting early and consistent investing to achieve this dream.

Use an educational, motivational tone focusing on achieving dreams. 3-4 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in education goal response: {e}")
            return self._generate_fallback_education_response(analysis)
    
    def _generate_loan_prepayment_response(self, user_message: str, analysis: Dict) -> str:
        """Generate response for loan prepayment scenario"""
        if not self.gemini_available:
            return self._generate_fallback_loan_response(analysis)
        
        prompt = f"""
User asked: "{user_message}"

LOAN PREPAYMENT ANALYSIS:
- Outstanding Loan Amount: ₹{analysis['outstanding_loan']:,.0f}
- Current Monthly EMI: ₹{analysis['current_emi']:,.0f}
- Assumed Loan Interest Rate: {analysis['loan_interest_rate']}%
- Remaining Loan Tenure: {analysis['remaining_years']} years
- Total Interest Remaining (if loan runs full term): ₹{analysis['total_interest_remaining']:,.0f}

SCENARIO COMPARISON:
1. **Prepayment Path**:
   - Immediate Outflow (if you prepay the full loan): ₹{analysis['scenarios']['prepayment']['immediate_outflow']:,.0f}
   - Monthly Savings (freed up EMI): ₹{analysis['scenarios']['prepayment']['monthly_savings_if_prepaid']:,.0f}
   - Future Wealth (from investing freed EMI over {analysis['remaining_years']} years at {self.SIP_RETURN_RATE*100:.1f}%): ₹{analysis['scenarios']['prepayment']['future_wealth_from_emi_investment']:,.0f}
   - Total Wealth Benefit in Prepayment Path: ₹{analysis['scenarios']['prepayment']['total_benefit_prepayment_path']:,.0f}

2. **Continue EMI Path (and Invest the Lump Sum Equivalent)**:
   - Total Interest Cost (if loan runs full term): ₹{analysis['scenarios']['continue_emi']['total_interest_cost']:,.0f}
   - Future Wealth (from investing the equivalent lump sum over {analysis['remaining_years']} years at {self.SIP_RETURN_RATE*100:.1f}%): ₹{analysis['scenarios']['continue_emi']['investment_returns_on_lumpsum']:,.0f}
   - Net Wealth in Continue EMI Path: ₹{analysis['scenarios']['continue_emi']['net_wealth_continue_emi_path']:,.0f}

**RECOMMENDATION**: {analysis['recommendation'].upper()}
**Net Financial Benefit of Recommended Path**: ₹{analysis['net_benefit']:,.0f}
**Rationale**: {analysis['rationale']}

Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}.

Provide a detailed analysis that:
1. Clearly compares the financial outcomes of both prepayment and continuing EMI scenarios.
2. Explains the concept of opportunity cost (comparing loan interest saved vs. investment returns gained).
3. Briefly touches upon other considerations like tax benefits (if applicable for specific loans like home loans) and liquidity needs.
4. Gives a clear and concise recommendation with robust reasoning.
5. Helps the user make a balanced decision considering both rational financial analysis and personal circumstances.

Use an analytical, balanced tone helping with financial decision-making. 3-4 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in loan prepayment response: {e}")
            return self._generate_fallback_loan_response(analysis)
    
    def generate_general_time_machine_response(self, user_message: str, classification: Dict) -> str:
        """Generate response for general time machine queries"""
        if not self.gemini_available:
            return self._generate_fallback_general_response(user_message, classification)
        
        current_snapshot = self.fi_client.get_current_financial_snapshot()
        
        portfolio_value = current_snapshot['assets']['total_portfolio_value']
        available_cash = current_snapshot['assets']['emergency_fund'] 
        
        risk_tolerance = current_snapshot['user_profile']['risk_tolerance']
        investment_goals_list = current_snapshot['user_profile']['investment_goals']
        
        investment_goals_str = ', '.join([goal.replace('_', ' ').title() for goal in investment_goals_list]) if investment_goals_list else "No specific goals defined"

        prompt = f"""
User asked: "{user_message}"

CURRENT FINANCIAL STATUS:
- Portfolio Value: ₹{portfolio_value:,.0f}
- Available Cash (Emergency Fund): ₹{available_cash:,.0f}
- Risk Tolerance: {risk_tolerance.title()}
- Investment Goals: {investment_goals_str}

CLASSIFICATION: {classification['scenario_type']} scenario
DETECTED PARAMETERS: {classification['financial_params']}

Current time is {datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p %Z')}.

This appears to be a general financial planning query. Provide:
1. Understanding of their financial scenario
2. Time-based projections where possible
3. Actionable recommendations
4. Next steps for detailed planning

Use encouraging, educational tone. Focus on time-value of money concepts. 3 paragraphs.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in general response: {e}")
            return self._generate_fallback_general_response(user_message, classification)
    
    # Fallback response methods (unchanged)
    def _generate_fallback_salary_response(self, analysis: Dict) -> str:
        """Fallback response for salary hike scenario"""
        return f"""Congratulations on your {analysis['hike_percentage']}% salary increase! This ₹{analysis['additional_monthly_income']:,.0f} additional monthly income is a great opportunity to accelerate your financial goals.

I recommend allocating ₹{analysis['recommendations']['additional_sip']:,.0f} (60%) to additional SIP investments, ₹{analysis['recommendations']['emergency_fund_boost']:,.0f} (20%) to boost your emergency fund, and ₹{analysis['recommendations']['goal_acceleration']:,.0f} (20%) toward specific goals like home buying or education.

This strategic allocation will help you maintain lifestyle inflation in check while significantly improving your long-term wealth creation. Consider automating these investments right after your first increased salary credit."""
    
    def _generate_fallback_house_response(self, analysis: Dict) -> str:
        """Fallback response for house purchase scenario"""
        affordability_text = "achievable" if analysis['is_affordable'] else "challenging but possible"
        shortfall_text = f"surplus of ₹{analysis['shortfall_or_surplus']:,.0f}" if analysis['is_affordable'] else f"shortfall of ₹{abs(analysis['shortfall_or_surplus']):,.0f}"
        
        return f"""Your goal of buying a ₹{analysis['house_price_today']:,.0f} house in {analysis['timeline_years']} years is {affordability_text}. With real estate inflation, the house will cost approximately ₹{analysis['house_price_future']:,.0f} by then.

Your ₹{analysis['monthly_savings']:,.0f} monthly savings will accumulate to ₹{analysis['total_savings_accumulated']:,.0f}, creating a {shortfall_text} for the ₹{analysis['down_payment_required']:,.0f} down payment. The resulting home loan EMI would be ₹{analysis['loan_emi']:,.0f}.

{"You're on track for your goal!" if analysis['is_affordable'] else f"Consider increasing monthly savings or extending timeline to bridge the gap."} Ensure your EMI doesn't exceed 40% of your monthly income for comfortable repayment."""
    
    def _generate_fallback_family_response(self, analysis: Dict) -> str:
        """Fallback response for family planning scenario"""
        return f"""Congratulations on your growing family! Financially preparing for a baby requires planning for both immediate costs of ₹{analysis['total_immediate_cost']:,.0f} and ongoing monthly expenses increasing by ₹{analysis['total_monthly_increase']:,.0f}.

Your emergency fund needs to grow from ₹{analysis['current_emergency_fund']:,.0f} to ₹{analysis['new_emergency_fund_target']:,.0f}, requiring an additional ₹{analysis['emergency_fund_gap']:,.0f}. This accounts for higher monthly expenses including baby care, medical checkups, and future education savings.

Start building this fund over the next 9-12 months, and review your health and term insurance coverage. The monthly cost increase is manageable when planned systematically, ensuring your baby's arrival brings only joy, not financial stress."""
    
    def _generate_fallback_job_response(self, analysis: Dict) -> str:
        """Fallback response for job switch scenario"""
        decision_text = "financially beneficial" if analysis['is_beneficial'] else "requires careful consideration"
        
        return f"""Your job switch with {analysis['salary_hike_percentage']}% salary hike appears {decision_text}. While you'll gain ₹{analysis['additional_monthly_income']:,.0f} monthly, losing EPF means you'll need to invest ₹{analysis['required_private_investment_monthly']:,.0f} privately for retirement planning.

The retirement impact analysis shows private investments could potentially generate ₹{analysis['retirement_projections']['difference']:,.0f} more than EPF, assuming 12% returns vs 8.5% EPF returns. However, this requires disciplined investing in PPF (₹{analysis['recommendations']['ppf_investment_annual']:,.0f}/year), NPS, and mutual funds.

{"The switch makes financial sense" if analysis['is_beneficial'] else "Consider the trade-offs carefully"}, especially the loss of job security and guaranteed EPF returns. Ensure you can maintain the required private investment discipline throughout your career."""
    
    def _generate_fallback_education_response(self, analysis: Dict) -> str:
        """Fallback response for education goal scenario"""
        abroad_text = " (including currency risk)" if analysis['is_abroad_education'] else ""
        
        return f"""Your ₹{analysis['education_cost_today']:,.0f} education goal will require ₹{analysis['education_cost_future']:,.0f} in {analysis['timeline_years']} years due to 8% education inflation{abroad_text}. You'll need to invest ₹{analysis['adjusted_monthly_sip']:,.0f} monthly through SIPs.

With your timeline of {analysis['timeline_years']} years, I recommend {analysis['recommendations']['equity_allocation']*100}% equity and {analysis['recommendations']['debt_allocation']*100}% debt allocation to balance growth and stability. Your current portfolio will contribute ₹{analysis['current_portfolio_contribution']:,.0f} toward this goal.

Starting early gives you the power of compounding. Consider diversified equity funds for the majority allocation, gradually shifting to debt funds as you approach the goal timeline to protect against market volatility."""
    
    def _generate_fallback_loan_response(self, analysis: Dict) -> str:
        """Fallback response for loan prepayment scenario"""
        return f"""Analyzing your ₹{analysis['outstanding_loan']:,.0f} loan prepayment decision: The choice depends on opportunity cost. Continuing EMIs will cost ₹{analysis['total_interest_remaining']:,.0f} in interest, while prepaying allows you to invest ₹{analysis['scenarios']['prepayment']['monthly_savings_if_prepaid']:,.0f} monthly.

Your loan interest rate of {analysis['loan_interest_rate']}% versus potential investment returns of {self.SIP_RETURN_RATE*100}% suggests {analysis['recommendation']} is better. The net benefit of ₹{analysis['net_benefit']:,.0f} favors {"prepayment" if analysis['recommendation'] == 'prepay' else "continuing EMIs and investing"}.

{analysis['rationale']} Consider your risk tolerance, tax benefits on the loan, and liquidity needs when making this decision. The mathematical analysis favors one approach, but your personal financial situation should guide the final choice."""
    
    def _generate_fallback_general_response(self, user_message: str, classification: Dict) -> str:
        """Fallback response for general queries"""
        return f"""I understand you're looking for financial guidance around your scenario. Based on your message, this appears to be a {classification['scenario_type']} situation that involves {"financial calculations" if classification['requires_calculation'] else "planning considerations"}.

To provide more specific time machine analysis, I'd need additional details like specific amounts, timelines, or current financial parameters. However, I can guide you through the key factors to consider for any financial goal: time horizon, required amount, current savings rate, and expected returns.

Would you like to share more specific details about amounts or timelines? This will help me provide precise projections and recommendations for your financial scenario."""
    
    # Helper calculation methods (modified for robustness)
    def _estimate_monthly_income(self, portfolio: Dict, snapshot_data: Dict) -> float:
        """
        Estimate monthly income based on snapshot data.
        'snapshot_data' is expected to be the full current_financial_snapshot.
        """
        if 'income' in snapshot_data and 'total_monthly_income' in snapshot_data['income'] and snapshot_data['income']['total_monthly_income'] > 0:
            return snapshot_data['income']['total_monthly_income']

        print("Warning: Estimating monthly income. 'total_monthly_income' missing or zero in client snapshot. Using fallback heuristic.")
        total_wealth = snapshot_data['assets']['total_portfolio_value'] + snapshot_data['assets']['emergency_fund']
        estimated_monthly_savings = total_wealth * 0.005 
        return max(50000, estimated_monthly_savings / 0.20) 
        
    def _estimate_monthly_expenses(self, portfolio: Dict, snapshot_data: Dict) -> float:
        """
        Estimate monthly expenses based on snapshot data.
        'snapshot_data' is expected to be the full current_financial_snapshot.
        """
        if 'expenses' in snapshot_data and 'monthly_expenses' in snapshot_data['expenses'] and snapshot_data['expenses']['monthly_expenses'] > 0:
            return snapshot_data['expenses']['monthly_expenses']

        print("Warning: Estimating monthly expenses. 'monthly_expenses' missing or zero in client snapshot. Using fallback heuristic.")
        estimated_income = self._estimate_monthly_income(portfolio, snapshot_data) 
        return estimated_income * 0.70 
    
    def _calculate_sip_for_target(self, target_amount: float, years: float, annual_return: float) -> float:
        """Calculate monthly SIP needed for target amount"""
        monthly_return = annual_return / 12
        months = years * 12
        
        if months <= 0: 
            return float('inf') 

        if monthly_return == 0:
            return target_amount / months
        
        denominator = (((1 + monthly_return) ** months) - 1)
        if denominator <= 0: 
            return float('inf') 
             
        monthly_sip = target_amount * monthly_return / denominator
        return monthly_sip
    
    def _calculate_home_goal_acceleration(self, additional_sip: float, current_monthly_savings_before_hike: float) -> Dict:
        """Calculate how additional SIP accelerates home buying goal"""
        house_price = 5000000 
        down_payment_target = house_price * 0.20 
        
        current_monthly_contribution_to_house = current_monthly_savings_before_hike * 0.60
        new_monthly_contribution_to_house = current_monthly_contribution_to_house + additional_sip
        
        original_timeline = self._years_to_reach_target(
            target=down_payment_target,
            monthly_sip=current_monthly_contribution_to_house,
            annual_return=self.SIP_RETURN_RATE
        )

        new_timeline = self._years_to_reach_target(
            target=down_payment_target,
            monthly_sip=new_monthly_contribution_to_house,
            annual_return=self.SIP_RETURN_RATE
        )
        
        acceleration_months = (original_timeline - new_timeline) * 12 if original_timeline != float('inf') and new_timeline != float('inf') else 0

        return {
            'house_price': house_price,
            'down_payment_target': down_payment_target,
            'original_timeline_years': original_timeline,
            'new_timeline_years': new_timeline,
            'acceleration_months': acceleration_months
        }
    
    def _years_to_reach_target(self, target: float, monthly_sip: float, annual_return: float) -> float:
        """
        Calculate years needed to reach target with given monthly SIP, assuming no initial lump sum.
        If target is not reachable (SIP too low or negative), returns float('inf').
        """
        if monthly_sip <= 0:
            return float('inf')
        
        monthly_return = annual_return / 12
        
        if monthly_return == 0:
            if target <= monthly_sip * 12 and monthly_sip * 12 > 0: 
                return target / (monthly_sip * 12)
            else:
                return float('inf') 
        
        argument_for_log = (target * monthly_return / monthly_sip) + 1
        
        if argument_for_log <= 0: 
            return float('inf') 
        
        try:
            months = math.log(argument_for_log) / math.log(1 + monthly_return)
        except (ValueError, ZeroDivisionError): 
            return float('inf')
            
        return months / 12
    
    def _suggest_education_funds(self, timeline_years: float) -> List[str]:
        """Suggest appropriate funds for education goal"""
        if timeline_years > 5:
            return ['Large Cap Equity Funds', 'Multi-Cap Funds', 'International Funds']
        elif timeline_years > 3:
            return ['Hybrid Funds', 'Large Cap Funds', 'Short-term Debt Funds']
        else:
            return ['Debt Funds', 'Liquid Funds', 'Conservative Hybrid Funds']
    
    def _generate_house_recommendation(self, shortfall_surplus: float, monthly_savings: float, timeline_years: float) -> str:
        """Generate house purchase recommendation"""
        if shortfall_surplus >= 0:
            return "Your current savings plan is sufficient for the down payment and the goal appears achievable."
        else:
            additional_needed = abs(shortfall_surplus)
            required_extra_monthly_sip = self._calculate_sip_for_target(additional_needed, timeline_years, self.SIP_RETURN_RATE)
            
            if required_extra_monthly_sip == float('inf'):
                return f"You have a significant shortfall of ₹{additional_needed:,.0f} for the down payment. It seems challenging to bridge this gap within the {timeline_years} year timeline with current parameters. Consider a longer timeline or a lower house price."
            else:
                return f"You have a shortfall of ₹{additional_needed:,.0f} for the down payment. To bridge this gap within the {timeline_years} year timeline, you would need to increase your monthly savings by approximately ₹{required_extra_monthly_sip:,.0f}."
    
    def _generate_loan_prepayment_rationale(self, loan_rate: float, investment_rate: float, net_benefit: float) -> str:
        """Generate rationale for loan prepayment decision"""
        if net_benefit > 0:
            return f"Investing the freed-up EMI and the initial lump sum (if applicable) at a potential return of {investment_rate*100:.1f}% is projected to generate more wealth than the interest saved on the loan at {loan_rate*100:.1f}%. Therefore, prepayment is financially more beneficial in this scenario."
        else:
            return f"Your loan interest rate of {loan_rate*100:.1f}% is currently lower than or very close to your expected investment returns of {investment_rate*100:.1f}%. In this case, it is financially more advantageous to continue paying your EMIs and strategically invest any surplus funds."