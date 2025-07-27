import json
import os
import math
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

class TimeMachineFiClient:
    def __init__(self, fi_data_file: str = "fi_data/time_machine_user_data.json"):
        """Initialize Time Machine Fi Client with scenario planning capabilities"""
        self.fi_data_file = fi_data_file
        self.fi_data = None
        self.is_loaded = False
        self._load_fi_data()
        
        # Scenario planning templates
        self.scenario_templates = {
            'salary_hike': {
                'impact_areas': ['monthly_income', 'savings_rate', 'goal_timelines'],
                'calculation_fields': ['current_salary', 'hike_percentage', 'effective_date']
            },
            'house_purchase': {
                'impact_areas': ['major_expenses', 'loan_requirements', 'down_payment'],
                'calculation_fields': ['house_price', 'timeline_years', 'location', 'loan_tenure']
            },
            'family_planning': {
                'impact_areas': ['monthly_expenses', 'emergency_fund', 'insurance_needs'],
                'calculation_fields': ['expected_date', 'preparation_timeline', 'cost_estimates']
            },
            'job_switch': {
                'impact_areas': ['income_change', 'benefits_change', 'retirement_planning'],
                'calculation_fields': ['new_salary', 'epf_status', 'other_benefits']
            },
            'education_goal': {
                'impact_areas': ['major_expenses', 'investment_strategy', 'timeline_planning'],
                'calculation_fields': ['course_cost', 'timeline_years', 'location', 'currency']
            },
            'loan_prepayment': {
                'impact_areas': ['debt_reduction', 'investment_reallocation', 'cash_flow'],
                'calculation_fields': ['loan_amount', 'current_emi', 'interest_rate', 'tenure_remaining']
            }
        }
        
        # Goal categories with Indian context
        self.goal_categories = {
            'short_term': {  # 1-3 years
                'emergency_fund': {'priority': 'high', 'typical_amount_months': 6},
                'vacation': {'priority': 'medium', 'typical_amount': 200000},
                'gadgets': {'priority': 'low', 'typical_amount': 100000}
            },
            'medium_term': {  # 3-7 years
                'house_down_payment': {'priority': 'high', 'typical_percentage': 20},
                'car_purchase': {'priority': 'medium', 'typical_amount': 800000},
                'wedding': {'priority': 'high', 'typical_amount': 1500000}
            },
            'long_term': {  # 7+ years
                'child_education': {'priority': 'high', 'inflation_rate': 0.08},
                'retirement': {'priority': 'high', 'replacement_ratio': 0.75},
                'dream_home': {'priority': 'medium', 'typical_amount': 8000000}
            }
        }
        
        # Market assumptions for projections
        self.market_assumptions = {
            'equity_returns': 0.12,  # 12% long-term equity returns
            'debt_returns': 0.07,   # 7% debt returns
            'inflation_general': 0.06,  # 6% general inflation
            'inflation_education': 0.08,  # 8% education inflation
            'inflation_healthcare': 0.09,  # 9% healthcare inflation
            'inflation_real_estate': 0.05,  # 5% real estate inflation
            'epf_returns': 0.085,   # 8.5% EPF returns
            'ppf_returns': 0.075,   # 7.5% PPF returns
            'home_loan_rate': 0.085,  # 8.5% home loan rate
            'personal_loan_rate': 0.12,  # 12% personal loan rate
            'salary_growth_rate': 0.08   # 8% annual salary growth
        }
    
    def _load_fi_data(self):
        """Load Fi data from JSON file"""
        try:
            if os.path.exists(self.fi_data_file):
                with open(self.fi_data_file, 'r') as f:
                    self.fi_data = json.load(f)
                self.is_loaded = True
                print(f"✅ Time Machine Fi data loaded successfully!")
            else:
                print(f"⚠️ Time Machine Fi data file not found: {self.fi_data_file}")
                # Create a default empty structure if file doesn't exist
                self.fi_data = {} 
                self.is_loaded = False
        except Exception as e:
            print(f"❌ Error loading Time Machine Fi data: {e}")
            self.is_loaded = False
    
    def get_current_financial_snapshot(self) -> Dict[str, Any]:
        """Get comprehensive current financial snapshot"""
        if not self.is_loaded:
            return self._get_demo_snapshot()
        
        portfolio_section = self.fi_data.get('portfolio', {})
        income_section = self.fi_data.get('income', {})
        expenses_section = self.fi_data.get('expenses', {})
        goals_section = self.fi_data.get('goals', {})
        user_profile_section = self.fi_data.get('user_profile', {}) # Added for risk_tolerance

        return {
            "assets": {
                "total_portfolio_value": float(portfolio_section.get('total_market_value', 0)),
                "emergency_fund": float(portfolio_section.get('emergency_fund', 0)),
                "real_estate": float(portfolio_section.get('real_estate_value', 0)),
                "other_assets": float(portfolio_section.get('other_assets', 0))
            },
            "income": {
                "monthly_salary": float(income_section.get('monthly_salary', 0)),
                "annual_bonus": float(income_section.get('annual_bonus', 0)),
                "other_income": float(income_section.get('other_income', 0)),
                "epf_contribution": float(income_section.get('epf_contribution', 0)),
                "total_monthly_income": float(income_section.get('total_monthly_income', 0))
            },
            "expenses": {
                "monthly_expenses": float(expenses_section.get('monthly_expenses', 0)),
                "rent_emi": float(expenses_section.get('rent_emi', 0)),
                "insurance_premiums": float(expenses_section.get('insurance_premiums', 0)),
                "discretionary_expenses": float(expenses_section.get('discretionary_expenses', 0))
            },
            "savings": {
                "monthly_sip": float(portfolio_section.get('monthly_sip', 0)),
                "savings_rate": float(income_section.get('savings_rate', 0.20)),
                "current_monthly_savings": float(income_section.get('monthly_savings', 0))
            },
            "goals": self._format_goals_data(goals_section),
            "debts": {
                "home_loan": float(self.fi_data.get('debts', {}).get('home_loan', 0)),
                "personal_loans": float(self.fi_data.get('debts', {}).get('personal_loans', 0)),
                "credit_card_debt": float(self.fi_data.get('debts', {}).get('credit_card_debt', 0))
            },
            "user_profile": { # Include user profile data
                "risk_tolerance": user_profile_section.get('risk_tolerance', 'moderate'),
                "investment_goals": user_profile_section.get('investment_goals', [])
            }
        }
    
    # --- ADDED FOR TimeMachineAgent COMPATIBILITY ---
    def get_portfolio_data(self) -> Dict[str, Any]:
        """Wrapper to provide portfolio data in the format TimeMachineAgent expects."""
        snapshot = self.get_current_financial_snapshot()
        return {
            'total_value': snapshot['assets']['total_portfolio_value'],
            'investments': [] # Your current snapshot doesn't detail individual investments, so this will be empty or generalized
        }

    def get_account_summary(self) -> Dict[str, Any]:
        """Wrapper to provide account summary data in the format TimeMachineAgent expects."""
        snapshot = self.get_current_financial_snapshot()
        return {
            'available_cash': snapshot['assets']['emergency_fund'],
            'risk_tolerance': snapshot['user_profile']['risk_tolerance'],
            'investment_goals': snapshot['user_profile']['investment_goals'], # Use the new user_profile section
            'monthly_income': snapshot['income']['total_monthly_income'],
            'monthly_expenses': snapshot['expenses']['monthly_expenses']
        }
    # --- END ADDED METHODS ---

    def _format_goals_data(self, goals_section: Dict) -> Dict[str, Any]:
        """Format goals data for time machine analysis"""
        formatted_goals = {}
        
        for goal_name, goal_data in goals_section.items():
            formatted_goals[goal_name] = {
                "target_amount": float(goal_data.get('target_amount', 0)),
                "current_progress": float(goal_data.get('current_progress', 0)),
                "timeline_years": float(goal_data.get('timeline_years', 0)),
                "priority": goal_data.get('priority', 'medium'),
                "category": goal_data.get('category', 'general'),
                "monthly_allocation": float(goal_data.get('monthly_allocation', 0))
            }
        
        return formatted_goals
    
    def get_scenario_impact_analysis(self, scenario_type: str, parameters: Dict) -> Dict[str, Any]:
        """Analyze impact of a specific scenario on financial situation"""
        current_snapshot = self.get_current_financial_snapshot()
        
        if scenario_type == 'salary_hike':
            return self._analyze_salary_hike_impact(current_snapshot, parameters)
        elif scenario_type == 'house_purchase':
            return self._analyze_house_purchase_impact(current_snapshot, parameters)
        elif scenario_type == 'family_planning':
            return self._analyze_family_planning_impact(current_snapshot, parameters)
        elif scenario_type == 'job_switch':
            return self._analyze_job_switch_impact(current_snapshot, parameters)
        elif scenario_type == 'education_goal':
            return self._analyze_education_goal_impact(current_snapshot, parameters)
        elif scenario_type == 'loan_prepayment':
            return self._analyze_loan_prepayment_impact(current_snapshot, parameters)
        else:
            return {"error": f"Unknown scenario type: {scenario_type}"}
    
    def _analyze_salary_hike_impact(self, snapshot: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze salary hike impact on financial goals"""
        current_income = snapshot['income']['monthly_salary']
        hike_percentage = params.get('hike_percentage', 25)
        new_income = current_income * (1 + hike_percentage / 100)
        additional_income = new_income - current_income
        
        # Impact on savings
        current_savings = snapshot['savings']['current_monthly_savings']
        additional_savings_potential = additional_income * 0.70  # 70% of additional income to savings
        new_total_savings = current_savings + additional_savings_potential
        
        # Impact on goals
        goal_acceleration = {}
        for goal_name, goal_data in snapshot['goals'].items():
            current_monthly = goal_data['monthly_allocation']
            boosted_monthly = current_monthly + (additional_savings_potential * 0.3)  # 30% boost to each goal
            
            # Calculate new timeline
            target = goal_data['target_amount']
            current_progress = goal_data['current_progress']
            remaining_amount = target - current_progress
            
            if boosted_monthly > 0:
                new_timeline = self._calculate_timeline_for_target(
                    remaining_amount, boosted_monthly, self.market_assumptions['equity_returns']
                )
                original_timeline = goal_data['timeline_years']
                acceleration_months = max(0, (original_timeline - new_timeline) * 12)
            else:
                acceleration_months = 0
            
            goal_acceleration[goal_name] = {
                'original_monthly': current_monthly,
                'boosted_monthly': boosted_monthly,
                'acceleration_months': acceleration_months
            }
        
        return {
            'income_change': {
                'current_monthly': current_income,
                'new_monthly': new_income,
                'additional_monthly': additional_income,
                'percentage_increase': hike_percentage
            },
            'savings_impact': {
                'current_monthly_savings': current_savings,
                'additional_savings_potential': additional_savings_potential,
                'new_total_savings': new_total_savings,
                'savings_rate_improvement': (additional_savings_potential / new_income) * 100
            },
            'goal_acceleration': goal_acceleration,
            'recommendations': {
                'lifestyle_inflation_limit': additional_income * 0.30,
                'investment_increase': additional_income * 0.50,
                'emergency_fund_boost': additional_income * 0.20
            }
        }
    
    def _analyze_house_purchase_impact(self, snapshot: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze house purchase feasibility and impact"""
        house_price = params.get('house_price', 5000000)
        timeline_years = params.get('timeline_years', 3)
        location_factor = params.get('location_factor', 1.0)  # City price multiplier
        
        # Adjust house price for location and inflation
        adjusted_price = house_price * location_factor
        future_price = adjusted_price * ((1 + self.market_assumptions['inflation_real_estate']) ** timeline_years)
        
        # Down payment calculation (20%)
        down_payment_required = future_price * 0.20
        loan_amount = future_price * 0.80
        
        # Current savings available for house
        current_savings = snapshot['assets']['total_portfolio_value'] + snapshot['assets']['emergency_fund'] * 0.5
        monthly_house_savings = snapshot['savings']['current_monthly_savings'] * 0.60  # 60% allocated to house
        
        # Future value calculation
        future_savings = self._calculate_future_value_sip(
            monthly_house_savings, timeline_years, self.market_assumptions['equity_returns']
        )
        total_available = current_savings + future_savings
        
        # EMI calculation
        monthly_emi = self._calculate_emi(
            loan_amount, self.market_assumptions['home_loan_rate'], 20  # 20-year loan
        )
        
        # Affordability analysis
        current_income = snapshot['income']['total_monthly_income']
        emi_to_income_ratio = (monthly_emi / current_income) * 100 if current_income > 0 else float('inf')
        
        return {
            'house_details': {
                'current_price': house_price,
                'location_adjusted_price': adjusted_price,
                'future_price': future_price,
                'down_payment_required': down_payment_required,
                'loan_amount': loan_amount
            },
            'savings_analysis': {
                'current_available': current_savings,
                'monthly_allocation': monthly_house_savings,
                'future_savings': future_savings,
                'total_available': total_available,
                'shortfall_surplus': total_available - down_payment_required
            },
            'loan_analysis': {
                'monthly_emi': monthly_emi,
                'emi_to_income_ratio': emi_to_income_ratio,
                'affordability_status': 'affordable' if emi_to_income_ratio < 40 else 'stretched' if emi_to_income_ratio < 50 else 'unaffordable'
            },
            'recommendations': self._generate_house_recommendations(total_available, down_payment_required, emi_to_income_ratio)
        }
    
    def _analyze_family_planning_impact(self, snapshot: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze financial impact of family planning"""
        expected_date = params.get('expected_date', '2025-01-01')
        preparation_months = params.get('preparation_months', 9)
        
        # Cost estimates (Indian context)
        immediate_costs = {
            'hospital_delivery': 150000,
            'baby_essentials': 75000,
            'insurance_upgrades': 50000,
            'contingency': 50000
        }
        
        monthly_cost_increases = {
            'baby_care': 8000,
            'medical_expenses': 3000,
            'child_education_sip': 5000,
            'increased_insurance': 2000
        }
        
        # Emergency fund impact
        current_monthly_expenses = snapshot['expenses']['monthly_expenses']
        new_monthly_expenses = current_monthly_expenses + sum(monthly_cost_increases.values())
        new_emergency_fund_target = new_monthly_expenses * 6
        current_emergency_fund = snapshot['assets']['emergency_fund']
        emergency_fund_gap = max(0, new_emergency_fund_target - current_emergency_fund)
        
        # Total immediate preparation needed
        total_immediate_need = sum(immediate_costs.values()) + emergency_fund_gap
        monthly_preparation_target = total_immediate_need / preparation_months
        
        # Impact on current savings allocation
        current_savings = snapshot['savings']['current_monthly_savings']
        remaining_for_other_goals = current_savings - monthly_preparation_target - sum(monthly_cost_increases.values())
        
        return {
            'cost_analysis': {
                'immediate_costs': immediate_costs,
                'total_immediate': sum(immediate_costs.values()),
                'monthly_increases': monthly_cost_increases,
                'total_monthly_increase': sum(monthly_cost_increases.values())
            },
            'emergency_fund_impact': {
                'current_fund': current_emergency_fund,
                'new_target': new_emergency_fund_target,
                'gap': emergency_fund_gap
            },
            'preparation_plan': {
                'total_preparation_needed': total_immediate_need,
                'monthly_target': monthly_preparation_target,
                'preparation_timeline_months': preparation_months
            },
            'budget_impact': {
                'current_monthly_savings': current_savings,
                'preparation_allocation': monthly_preparation_target,
                'ongoing_cost_increase': sum(monthly_cost_increases.values()),
                'remaining_for_other_goals': remaining_for_other_goals
            },
            'recommendations': {
                'start_preparation_immediately': True,
                'increase_health_insurance': True,
                'setup_child_education_fund': True,
                'review_term_insurance': True
            }
        }
    
    def _analyze_job_switch_impact(self, snapshot: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze job switch financial impact"""
        new_salary = params.get('new_salary', snapshot['income']['monthly_salary'] * 1.3)
        epf_available = params.get('epf_available', False)
        other_benefits = params.get('other_benefits', {})
        
        current_salary = snapshot['income']['monthly_salary']
        salary_change = new_salary - current_salary
        
        # EPF impact analysis
        current_epf_employee_contrib = snapshot['income']['epf_contribution']
        current_epf_total_contrib = current_epf_employee_contrib * 2 # Employee + Employer
        
        if epf_available:
            new_epf_employee_contrib = new_salary * 0.12  # 12% employee contribution
            new_epf_total_contrib = new_epf_employee_contrib * 2
            epf_change_monthly = new_epf_total_contrib - current_epf_total_contrib
            required_private_retirement = 0
        else:
            new_epf_total_contrib = 0
            epf_change_monthly = -current_epf_total_contrib
            required_private_retirement = current_epf_total_contrib
        
        # Retirement corpus impact (30-year projection)
        years_to_retirement = 30 # Assuming a fixed projection period for comparison

        # Current job's EPF path (if continued)
        current_epf_path_future_value = self._calculate_future_value_sip(
            current_epf_total_contrib, years_to_retirement, self.market_assumptions['epf_returns']
        )

        # New job's path
        if epf_available:
            new_job_path_future_value = self._calculate_future_value_sip(
                new_epf_total_contrib, years_to_retirement, self.market_assumptions['epf_returns']
            )
        else:
            # Private investment path for the lost EPF amount
            new_job_path_future_value = self._calculate_future_value_sip(
                required_private_retirement, years_to_retirement, self.market_assumptions['equity_returns'] # Assuming higher returns for private MF
            )
        
        retirement_corpus_change = new_job_path_future_value - current_epf_path_future_value

        # Net monthly benefit calculation (considering salary change and required private investment)
        net_monthly_benefit = salary_change - required_private_retirement
        
        return {
            'salary_impact': {
                'current_salary': current_salary,
                'new_salary': new_salary,
                'salary_change': salary_change,
                'percentage_change': (salary_change / current_salary) * 100 if current_salary > 0 else 0
            },
            'epf_impact': {
                'epf_available_new_job': epf_available,
                'current_epf_total_contribution': current_epf_total_contrib,
                'new_epf_total_contribution': new_epf_total_contrib,
                'epf_change_monthly': epf_change_monthly,
                'required_private_investment_monthly': required_private_retirement
            },
            'retirement_impact': {
                'years_to_retirement': years_to_retirement,
                'projected_corpus_change': retirement_corpus_change,
                'better_for_retirement': retirement_corpus_change > 0
            },
            'net_benefit': {
                'monthly_net_benefit': net_monthly_benefit,
                'annual_net_benefit': net_monthly_benefit * 12,
                'recommendation': 'beneficial' if net_monthly_benefit > 0 else 'requires_consideration'
            },
            'alternative_investments': {
                # Convert monthly required_private_retirement to annual for PPF, NPS
                'ppf_option_annual': min(150000, required_private_retirement * 12) if not epf_available else 0,
                'nps_option_annual': required_private_retirement * 0.5 * 12 if not epf_available else 0, # Example split
                'mutual_fund_sip_annual': required_private_retirement * 0.5 * 12 if not epf_available else 0 # Example split
            }
        }
    
    def _analyze_education_goal_impact(self, snapshot: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze education goal funding requirements"""
        course_cost_today = params.get('course_cost', 8000000)  # ₹80 lakhs default
        timeline_years = params.get('timeline_years', 4)
        is_abroad = params.get('is_abroad', True)
        currency = params.get('currency', 'USD')
        
        # Inflation adjustment
        education_inflation = self.market_assumptions['inflation_education']
        future_cost_inr = course_cost_today * ((1 + education_inflation) ** timeline_years)
        
        # Currency risk for abroad education
        if is_abroad:
            currency_appreciation_rate = 0.03  # 3% annual INR depreciation vs USD
            currency_factor = (1 + currency_appreciation_rate) ** timeline_years
            future_cost_inr *= currency_factor
        
        # Current allocation to education goal from snapshot
        # Assuming there's a 'child_education' goal with current_progress and monthly_allocation
        education_goal_data = snapshot['goals'].get('child_education', {})
        current_education_corpus = education_goal_data.get('current_progress', 0)
        current_education_monthly_allocation = education_goal_data.get('monthly_allocation', 0)

        # Future value of current corpus
        future_value_current_corpus = current_education_corpus * ((1 + self.market_assumptions['equity_returns']) ** timeline_years)
        
        # Required monthly SIP calculation for the *entire* future cost
        required_monthly_sip_total = self._calculate_sip_for_target(
            future_cost_inr, timeline_years, self.market_assumptions['equity_returns']
        )
        
        # Adjusted requirement considering the future value of the existing corpus
        net_requirement = max(0, future_cost_inr - future_value_current_corpus)
        adjusted_monthly_sip = self._calculate_sip_for_target(
            net_requirement, timeline_years, self.market_assumptions['equity_returns']
        )
        
        # Investment strategy based on timeline
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
            'cost_analysis': {
                'current_cost': course_cost_today,
                'future_cost_base': course_cost_today * ((1 + education_inflation) ** timeline_years),
                'currency_impact': currency_factor if is_abroad else 1.0,
                'total_future_cost': future_cost_inr,
                'timeline_years': timeline_years
            },
            'funding_analysis': {
                'current_corpus': current_education_corpus,
                'future_value_current_corpus': future_value_current_corpus,
                'net_requirement': net_requirement,
                'required_monthly_sip_total': required_monthly_sip_total, # SIP if starting from zero with no existing corpus
                'adjusted_monthly_sip': adjusted_monthly_sip, # SIP needed *in addition* to current corpus
                'current_monthly_allocation': current_education_monthly_allocation,
                'shortfall_monthly': max(0, adjusted_monthly_sip - current_education_monthly_allocation)
            },
            'investment_strategy': {
                'equity_allocation': equity_allocation,
                'debt_allocation': debt_allocation,
                'recommended_funds': self._get_education_fund_recommendations(timeline_years),
                'review_frequency': 'annually' if timeline_years > 3 else 'semi-annually'
            },
            'risk_factors': {
                'currency_risk': is_abroad,
                'inflation_risk': True,
                'market_risk': equity_allocation > 0.5,
                'mitigation_strategies': self._get_education_risk_mitigation(timeline_years, is_abroad)
            }
        }
    
    def _analyze_loan_prepayment_impact(self, snapshot: Dict, params: Dict) -> Dict[str, Any]:
        """Analyze loan prepayment vs investment decision"""
        # Prioritize loan amount from params, else use home_loan from snapshot
        loan_amount = params.get('loan_amount', snapshot['debts'].get('home_loan', 0))
        # Prioritize current_emi from params, else try to calculate from snapshot's monthly_expenses if it includes EMI
        current_emi = params.get('current_emi', 0)
        
        interest_rate = params.get('interest_rate', self.market_assumptions['home_loan_rate'])
        remaining_tenure = params.get('remaining_tenure', 15)  # years
        
        # If current_emi is not provided in params, and not explicitly known, calculate it
        # This part assumes loan_amount is the OUTSTANDING principal for calculation
        if current_emi == 0 and loan_amount > 0:
            # Need to know original tenure to calculate original EMI, if not provided directly.
            # For simplicity, if not provided, assume a standard 20-year loan for EMI calculation.
            # This might not be precise if original tenure was different.
            current_emi = self._calculate_emi(loan_amount, interest_rate, remaining_tenure) # Using remaining tenure for EMI calculation
        
        # Scenario 1: Continue EMI and invest potential lump sum / future savings
        # Total interest paid if the loan runs its course
        total_interest_remaining = (current_emi * 12 * remaining_tenure) - loan_amount
        
        # Scenario 2: Prepay loan and invest EMI amount
        investment_return_rate = self.market_assumptions['equity_returns']
        
        # Future value if EMI amount is invested after prepayment
        emi_investment_future_value = self._calculate_future_value_sip(
            current_emi, remaining_tenure, investment_return_rate
        )
        
        # Opportunity cost analysis
        prepayment_amount = loan_amount # Assuming full outstanding loan for prepayment scenario
        
        # Compare:
        # 1. Wealth if loan is repaid + freed EMI invested
        wealth_after_prepayment = emi_investment_future_value # This represents the *future value* of the money that would have gone to EMI
        
        # 2. Wealth if loan is continued + equivalent lump sum (if available) invested
        # If the user has a lump sum to prepay, compare investing *that lump sum* vs. prepaying
        # Assuming the 'prepayment_amount' (which is the outstanding loan here) could instead be invested.
        wealth_if_invest_lump_sum = prepayment_amount * ((1 + investment_return_rate) ** remaining_tenure)
        
        # The decision logic here is often comparing the loan interest rate to the investment return rate.
        # If investment_return_rate > loan_interest_rate, investing is generally better.
        # If loan_interest_rate > investment_return_rate, prepaying is generally better.
        
        # Net gain from choosing investment over prepayment (if positive, investing is better)
        # Or net gain from choosing prepayment over investment (if positive, prepayment is better)
        
        # Let's frame it as Net Benefit of Prepayment: (Interest saved) - (Opportunity cost of investing that money)
        # Or: (Future value of investing EMI after prepayment) - (Future value of investing lump sum and paying loan)
        
        # Net Benefit for Prepayment vs. Not Prepaying (and investing an equivalent lump sum)
        # If you prepay, you save `total_interest_remaining` but lose `wealth_if_invest_lump_sum` potential.
        # Plus, you gain `emi_investment_future_value` from investing the freed EMIs.
        
        # Simplified comparison: Compare the effective cost/gain.
        # Option A: Prepay. Cost = immediate cash outflow (loan_amount). Benefit = no future interest payment + future value of investing freed EMI.
        # Option B: Don't prepay. Cost = total_interest_remaining. Benefit = keep cash for investment (wealth_if_invest_lump_sum).
        
        # Let's use the net benefit from the agent's calculation:
        # wealth_after_prepayment vs continue_emi_scenario_wealth
        # wealth_after_prepayment: Value you accumulate by being debt-free and investing freed EMI
        # continue_emi_scenario_wealth: Value you accumulate by investing a lump sum (equivalent to loan) minus interest paid
        
        # The agent provides `net_benefit = prepayment_scenario_wealth - continue_emi_scenario_wealth`
        # where `prepayment_scenario_wealth = emi_investment_returns`
        # and `continue_emi_scenario_wealth = investment_returns_on_prepayment_amount - total_interest_paid_if_continue`
        
        # This means the agent calculates net benefit as:
        # (FV of investing freed EMI) - [(FV of investing initial lump sum) - (Total Interest Paid)]
        
        # For simplicity in this _analyze method, let's just make a recommendation based on rates.
        
        # Decision matrix based on rates (simplistic, real world needs tax benefits, liquidity, risk appetite)
        if interest_rate < investment_return_rate:
            recommendation_text = 'continue_emi_and_invest'
            rationale_text = f"Your potential investment returns ({investment_return_rate*100:.1f}%) are likely higher than your loan interest rate ({interest_rate*100:.1f}%). Investing the amount you would prepay, or the freed-up EMI, would yield more wealth over time."
        else:
            recommendation_text = 'prepay_loan'
            rationale_text = f"Your loan interest rate ({interest_rate*100:.1f}%) is higher than or comparable to your potential investment returns ({investment_return_rate*100:.1f}%). Prepaying the loan would save you more in interest than you might gain from investing."
        
        # A more holistic net benefit could be considered by comparing total wealth in both scenarios.
        # For this client, we'll keep the output consistent with the agent's expectation.
        # The agent's `net_benefit` calculation (which is external) is the definitive one.
        # Here we only provide the `_analyze` method's output.
        
        return {
            'loan_details': {
                'outstanding_amount': loan_amount,
                'current_emi': current_emi,
                'interest_rate': interest_rate * 100,
                'remaining_tenure_years': remaining_tenure,
                'total_interest_remaining': total_interest_remaining
            },
            'scenarios_comparative_summary': { # More descriptive names
                'prepayment_path_future_wealth_from_emi_investment': emi_investment_future_value,
                'continue_emi_path_future_wealth_from_lumpsum_investment': wealth_if_invest_lump_sum,
                'net_interest_cost_if_continue_emi': total_interest_remaining
            },
            'recommendation': {
                'decision': recommendation_text,
                'rationale': rationale_text,
                'confidence_level': 'high' # Placeholder, can be more nuanced
            },
            'considerations': {
                'tax_benefits_on_loan_interest': min(200000, loan_amount * interest_rate) if loan_amount > 0 else 0,
                'liquidity_impact_of_prepayment': loan_amount,
                'risk_appetite_for_investing': snapshot['user_profile']['risk_tolerance'] # From snapshot
            }
        }
    
    # Helper calculation methods (these are correctly defined from your previous versions)
    def _calculate_future_value_sip(self, monthly_amount: float, years: float, annual_return: float) -> float:
        """Calculate future value of SIP"""
        monthly_return = annual_return / 12
        months = years * 12
        
        if monthly_return == 0:
            return monthly_amount * months
        
        future_value = monthly_amount * (((1 + monthly_return) ** months - 1) / monthly_return)
        return future_value
    
    def _calculate_emi(self, principal: float, annual_rate: float, years: float) -> float:
        """Calculate EMI for a loan"""
        monthly_rate = annual_rate / 12
        months = years * 12
        
        if monthly_rate == 0:
            return principal / months
        
        emi = principal * monthly_rate * ((1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
        return emi
    
    def _calculate_sip_for_target(self, target_amount: float, years: float, annual_return: float) -> float:
        """Calculate monthly SIP required for target amount"""
        monthly_return = annual_return / 12
        months = years * 12
        
        if monthly_return == 0:
            return target_amount / months
        
        # Avoid division by zero if (1+r)^n - 1 is zero (e.g., if months is too small for small monthly_return)
        denominator = (((1 + monthly_return) ** months) - 1)
        if denominator == 0:
            return float('inf') # Target unreachable with these parameters
            
        monthly_sip = target_amount * monthly_return / denominator
        return monthly_sip
    
    def _calculate_timeline_for_target(self, target: float, monthly_sip: float, annual_return: float) -> float:
        """Calculate years needed to reach target with given SIP"""
        if monthly_sip <= 0:
            return float('inf')
        
        monthly_return = annual_return / 12
        if monthly_return == 0:
            return target / monthly_sip / 12
        
        # Check argument for logarithm
        argument_for_log = (target * monthly_return / monthly_sip) + 1
        if argument_for_log <= 0: # Target is unreachable or already passed
            return float('inf')

        try:
            months = math.log(argument_for_log) / math.log(1 + monthly_return)
        except (ValueError, ZeroDivisionError): # Handles log of non-positive or division by zero
            return float('inf')
            
        return months / 12
    
    def _generate_house_recommendations(self, available: float, required: float, emi_ratio: float) -> List[str]:
        """Generate house purchase recommendations"""
        recommendations = []
        
        if available >= required:
            recommendations.append("✅ Down payment target achievable with current plan")
        else:
            shortfall = required - available
            recommendations.append(f"❌ Shortfall of ₹{shortfall:,.0f} for down payment")
            # This recommendation is for the client's internal analysis, not the agent's final output
            # A more precise recommendation would factor in the timeline.
            recommendations.append(f"💡 Consider increasing monthly savings or extending your timeline.")
        
        if emi_ratio < 30:
            recommendations.append("✅ EMI very affordable (healthy debt ratio)")
        elif emi_ratio < 40:
            recommendations.append("⚠️ EMI affordable but tight (monitor expenses)")
        else:
            recommendations.append("❌ EMI too high (>40% of income)")
            recommendations.append("💡 Consider lower price range or longer tenure")
        
        return recommendations
    
    def _get_education_fund_recommendations(self, timeline: float) -> List[str]:
        """Get education fund recommendations based on timeline"""
        if timeline > 5:
            return ["Large Cap Equity Funds", "Multi-Cap Funds", "International Funds (for abroad education)"]
        elif timeline > 3:
            return ["Hybrid Aggressive Funds", "Large Cap Funds", "Education-focused ULIP"]
        else:
            return ["Conservative Hybrid Funds", "Short Duration Debt Funds", "Liquid Funds"]
    
    def _get_education_risk_mitigation(self, timeline: float, is_abroad: bool) -> List[str]:
        """Get education risk mitigation strategies"""
        strategies = []
        
        if timeline > 3:
            strategies.append("Start with higher equity allocation, reduce as goal approaches")
        
        if is_abroad:
            strategies.append("Consider international equity funds for natural hedging")
            strategies.append("Monitor currency trends and consider forex hedging")
        
        strategies.append("Regular goal amount review for inflation adjustment")
        strategies.append("Maintain separate education corpus (don't mix with other goals)")
        
        return strategies
    
    def _get_demo_snapshot(self) -> Dict[str, Any]:
        """Fallback demo snapshot for when data file is not found or loaded"""
        return {
            "assets": {
                "total_portfolio_value": 1500000, # Increased for more realistic scenarios
                "emergency_fund": 600000,  # 6 months of 1L expenses
                "real_estate": 0,
                "other_assets": 100000
            },
            "income": {
                "monthly_salary": 100000,
                "annual_bonus": 200000,
                "other_income": 10000,
                "epf_contribution": 12000, # Employee's 12%
                "total_monthly_income": 110000 # Salary + other income
            },
            "expenses": {
                "monthly_expenses": 70000,
                "rent_emi": 25000,
                "insurance_premiums": 5000,
                "discretionary_expenses": 15000
            },
            "savings": {
                "monthly_sip": 20000, # Actual SIPs for investments
                "savings_rate": 0.25, # Derived from income/expenses
                "current_monthly_savings": 40000 # Total current savings (income - expenses)
            },
            "goals": {
                "house_down_payment": {
                    "target_amount": 1500000,
                    "current_progress": 200000,
                    "timeline_years": 4,
                    "priority": "high",
                    "category": "medium_term",
                    "monthly_allocation": 15000 # Monthly contribution to this goal
                },
                "child_education": {
                    "target_amount": 5000000,
                    "current_progress": 50000,
                    "timeline_years": 15,
                    "priority": "high",
                    "category": "long_term",
                    "monthly_allocation": 8000
                },
                "retirement": { # Added retirement goal to demo data for job switch scenario
                    "target_amount": 30000000, # Example retirement corpus
                    "current_progress": 1000000,
                    "timeline_years": 30,
                    "priority": "high",
                    "category": "long_term",
                    "monthly_allocation": 10000 # This would be separate from EPF
                }
            },
            "debts": {
                "home_loan": 0,
                "personal_loans": 0,
                "credit_card_debt": 0
            },
            "user_profile": { # Added for get_account_summary compatibility
                "risk_tolerance": "moderate",
                "investment_goals": ["retirement", "house_down_payment", "child_education"] # Example explicit goals
            }
        }