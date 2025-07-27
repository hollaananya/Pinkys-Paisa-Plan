from .data_helpers import load_json_file, save_json_file, ensure_data_files_exist
from .config import USER_TAX_DATA_FILE
import json
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta


class FiMCPClient:
    def __init__(self, fi_data_file: str = "fi_data/user_financial_data.json", 
                 tax_data_file: str = "fi_data/user_tax_data.json"):
        """Initialize Fi MCP client to read from JSON files"""
        self.fi_data_file = fi_data_file
        self.tax_data_file = tax_data_file
        self.fi_data = None
        self.tax_data = None
        self.is_loaded = False
        self._load_fi_data()
        self._load_or_create_tax_data()
    
    def _load_fi_data(self):
        """Load Fi data from JSON file"""
        try:
            if os.path.exists(self.fi_data_file):
                with open(self.fi_data_file, 'r') as f:
                    self.fi_data = json.load(f)
                self.is_loaded = True
                print(f"✅ Loaded Fi data successfully!")
                print(f"📊 Portfolio Value: ${self.fi_data['portfolio']['total_market_value']:,.2f}")
            else:
                print(f"⚠️ Fi data file not found: {self.fi_data_file}")
                self.is_loaded = False
        except Exception as e:
            print(f"❌ Error loading Fi data: {e}")
            self.is_loaded = False
    
    def _load_or_create_tax_data(self):
        """Load or create tax-specific data"""
        try:
            if os.path.exists(self.tax_data_file):
                with open(self.tax_data_file, 'r') as f:
                    self.tax_data = json.load(f)
                print(f"✅ Loaded tax data successfully!")
            else:
                # Create tax data from Fi data
                self.tax_data = self._generate_tax_data_from_fi()
                self._save_tax_data()
                print(f"✅ Generated and saved tax data!")
        except Exception as e:
            print(f"❌ Error loading/creating tax data: {e}")
            self.tax_data = self._get_demo_tax_data()
    
    def _generate_tax_data_from_fi(self) -> Dict[str, Any]:
        """Generate comprehensive tax data from Fi MCP data"""
        if not self.fi_data:
            return self._get_demo_tax_data()
        
        # Extract portfolio and user profile data
        portfolio = self.fi_data.get('portfolio', {})
        user_profile = self.fi_data.get('user_profile', {})
        account = self.fi_data.get('account', {})
        
        # Calculate annual income (simplified - assuming salary from portfolio value)
        estimated_annual_salary = portfolio.get('total_market_value', 0) * 0.6  # Rough estimate
        
        return {
            "user_id": self.fi_data.get('user_id', 'user_12345'),
            "tax_year": "2024-25",
            "last_updated": datetime.now().isoformat(),
            
            # Income Information
            "income": {
                "annual_salary": estimated_annual_salary,
                "monthly_salary": estimated_annual_salary / 12,
                "bonus": estimated_annual_salary * 0.15,
                "other_income": {
                    "dividend_income": portfolio.get('total_return', 0) * 0.3,
                    "interest_income": 25000,
                    "capital_gains": portfolio.get('total_return', 0) * 0.4
                },
                "total_gross_income": estimated_annual_salary + (portfolio.get('total_return', 0) * 0.7)
            },
            
            # Current Investments (Tax-saving)
            "investments": {
                "ppf": {
                    "current_year_contribution": 120000,
                    "total_balance": 450000,
                    "remaining_80c_limit": 30000
                },
                "elss": {
                    "current_investments": 0,
                    "market_value": 0,
                    "remaining_80c_limit": 150000
                },
                "nps": {
                    "employer_contribution": estimated_annual_salary * 0.10,
                    "employee_contribution": 50000,
                    "additional_80ccd_1b": 0,
                    "remaining_80ccd_1b_limit": 50000
                },
                "life_insurance": {
                    "annual_premium": 35000,
                    "sum_assured": 1000000
                },
                "ulip": {
                    "annual_premium": 0,
                    "current_value": 0
                }
            },
            
            # Loans and Interest
            "loans": {
                "home_loan": {
                    "outstanding_principal": 2500000,
                    "annual_interest_paid": 180000,
                    "principal_repayment": 150000,
                    "remaining_24b_limit": 20000
                },
                "education_loan": {
                    "outstanding_amount": 500000,
                    "annual_interest_paid": 45000
                },
                "personal_loan": {
                    "outstanding_amount": 0,
                    "annual_interest_paid": 0
                }
            },
            
            # Insurance Details
            "insurance": {
                "health_insurance": {
                    "self_family_premium": 18000,
                    "parents_premium": 35000,
                    "is_parents_senior_citizen": True,
                    "remaining_80d_limit": 22000
                },
                "life_insurance": {
                    "term_plan_premium": 12000,
                    "endowment_premium": 23000
                }
            },
            
            # Family Information
            "family": {
                "spouse": {
                    "name": "Partner",
                    "annual_income": 0,
                    "is_working": False,
                    "age": 32
                },
                "children": [
                    {
                        "name": "Mother",
                        "age": 62,
                        "is_senior_citizen": True,
                        "health_expenses": 30000,
                        "is_dependent": True
                    }
                ]
            },
            
            # Employment Details
            "employment": {
                "employer_name": "Tech Corp India",
                "employee_id": "EMP001",
                "salary_structure": {
                    "basic_salary": estimated_annual_salary * 0.40,
                    "hra": estimated_annual_salary * 0.25,
                    "special_allowance": estimated_annual_salary * 0.25,
                    "lta": 15000,
                    "medical_allowance": 15000,
                    "food_coupons": 26400,
                    "mobile_allowance": 12000
                },
                "pf_contribution": {
                    "employee": estimated_annual_salary * 0.12,
                    "employer": estimated_annual_salary * 0.12
                },
                "gratuity_eligible": True
            },
            
            # Previous Year Tax Details
            "previous_year_tax": {
                "gross_income": estimated_annual_salary * 0.95,
                "total_tax_paid": estimated_annual_salary * 0.15,
                "tds_deducted": estimated_annual_salary * 0.12,
                "advance_tax_paid": estimated_annual_salary * 0.03,
                "refund_received": 5000,
                "regime_used": "old"
            },
            
            # Current Year Projections
            "current_year_projections": {
                "estimated_gross_income": estimated_annual_salary,
                "estimated_tax_old_regime": estimated_annual_salary * 0.16,
                "estimated_tax_new_regime": estimated_annual_salary * 0.18,
                "tds_till_date": estimated_annual_salary * 0.08,
                "advance_tax_paid": 0,
                "remaining_tax_liability": estimated_annual_salary * 0.08
            },
            
            # Tax Saving Opportunities
            "optimization_opportunities": {
                "section_80c": {
                    "current_utilization": 120000,
                    "limit": 150000,
                    "remaining": 30000,
                    "recommended_investments": ["PPF", "ELSS", "Life Insurance"]
                },
                "section_80ccd_1b": {
                    "current_utilization": 0,
                    "limit": 50000,
                    "remaining": 50000,
                    "recommended": "Additional NPS contribution"
                },
                "section_80d": {
                    "current_utilization": 53000,
                    "limit": 75000,
                    "remaining": 22000,
                    "breakdown": {
                        "self_family": 18000,
                        "parents": 35000
                    }
                },
                "section_24b": {
                    "current_utilization": 180000,
                    "limit": 200000,
                    "remaining": 20000
                },
                "section_80e": {
                    "current_utilization": 45000,
                    "limit": "unlimited",
                    "description": "Education loan interest"
                }
            },
            
            # Banking and Savings
            "banking": {
                "savings_accounts": [
                    {
                        "bank_name": "HDFC Bank",
                        "account_type": "Savings",
                        "interest_earned": 8000
                    },
                    {
                        "bank_name": "SBI",
                        "account_type": "Savings", 
                        "interest_earned": 3500
                    }
                ],
                "fixed_deposits": [
                    {
                        "bank_name": "ICICI Bank",
                        "amount": 500000,
                        "interest_rate": 6.5,
                        "maturity_date": "2025-06-15",
                        "interest_earned": 32500
                    }
                ],
                "total_interest_income": 44000
            },
            
            # Investment Analysis
            "investment_analysis": {
                "total_tax_saving_investments": 215000,
                "potential_additional_investments": 122000,
                "estimated_tax_savings": 36600,
                "recommended_asset_allocation": {
                    "equity": 60,
                    "debt": 30,
                    "tax_saving": 10
                }
            },
            
            # Compliance Status
            "compliance": {
                "itr_filed_last_year": True,
                "itr_filing_date": "2024-07-15",
                "advance_tax_compliance": "partial",
                "tds_certificates_received": True,
                "form_16_received": True,
                "pending_actions": [
                    "Complete remaining 80C investments",
                    "Plan advance tax for Q4",
                    "Review salary structure optimization"
                ]
            }
        }
    
    def _save_tax_data(self):
        """Save tax data to JSON file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.tax_data_file) if os.path.dirname(self.tax_data_file) else ".", exist_ok=True)
            
            with open(self.tax_data_file, 'w') as f:
                json.dump(self.tax_data, f, indent=2)
            print(f"💾 Tax data saved to {self.tax_data_file}")
        except Exception as e:
            print(f"❌ Error saving tax data: {e}")
    
    def get_tax_profile_data(self) -> Dict[str, Any]:
        """Get comprehensive tax profile data"""
        if not self.tax_data:
            return self._get_demo_tax_data()
        
        return {
            "annual_income": self.tax_data["income"]["total_gross_income"],
            "monthly_salary": self.tax_data["income"]["monthly_salary"],
            "current_deductions": {
                "80C": self.tax_data["optimization_opportunities"]["section_80c"]["current_utilization"],
                "80CCD_1B": self.tax_data["optimization_opportunities"]["section_80ccd_1b"]["current_utilization"],
                "80D": self.tax_data["optimization_opportunities"]["section_80d"]["current_utilization"],
                "24B": self.tax_data["optimization_opportunities"]["section_24b"]["current_utilization"],
                "80E": self.tax_data["optimization_opportunities"]["section_80e"]["current_utilization"]
            },
            "investments": self.tax_data["investments"],
            "loans": self.tax_data["loans"],
            "insurance": self.tax_data["insurance"],
            "family": self.tax_data["family"],
            "employment": self.tax_data["employment"],
            "optimization_opportunities": self.tax_data["optimization_opportunities"],
            "compliance": self.tax_data["compliance"]
        }
    
    def get_deduction_analysis(self) -> Dict[str, Any]:
        """Get detailed deduction analysis"""
        if not self.tax_data:
            return {}
        
        opportunities = self.tax_data["optimization_opportunities"]
        
        return {
            "section_80c": {
                "utilized": opportunities["section_80c"]["current_utilization"],
                "limit": opportunities["section_80c"]["limit"],
                "remaining": opportunities["section_80c"]["remaining"],
                "utilization_percentage": (opportunities["section_80c"]["current_utilization"] / opportunities["section_80c"]["limit"]) * 100
            },
            "section_80ccd_1b": {
                "utilized": opportunities["section_80ccd_1b"]["current_utilization"],
                "limit": opportunities["section_80ccd_1b"]["limit"],
                "remaining": opportunities["section_80ccd_1b"]["remaining"],
                "utilization_percentage": (opportunities["section_80ccd_1b"]["current_utilization"] / opportunities["section_80ccd_1b"]["limit"]) * 100
            },
            "section_80d": {
                "utilized": opportunities["section_80d"]["current_utilization"],
                "limit": opportunities["section_80d"]["limit"],
                "remaining": opportunities["section_80d"]["remaining"],
                "utilization_percentage": (opportunities["section_80d"]["current_utilization"] / opportunities["section_80d"]["limit"]) * 100
            },
            "total_deductions_used": sum([
                opportunities["section_80c"]["current_utilization"],
                opportunities["section_80ccd_1b"]["current_utilization"],
                opportunities["section_80d"]["current_utilization"]
            ]),
            "total_potential_deductions": sum([
                opportunities["section_80c"]["limit"],
                opportunities["section_80ccd_1b"]["limit"],
                opportunities["section_80d"]["limit"]
            ])
        }
    
    def get_family_tax_profile(self) -> Dict[str, Any]:
        """Get family tax planning data"""
        if not self.tax_data:
            return {}
        
        family_data = self.tax_data.get("family", {})
        
        return {
            "total_family_income": (
                self.tax_data["income"]["total_gross_income"] + 
                family_data.get("spouse", {}).get("annual_income", 0)
            ),
            "dependents": {
                "spouse": family_data.get("spouse", {}),
                "children": family_data.get("children", []),
                "parents": family_data.get("parents", [])
            },
            "education_expenses": sum([child.get("school_fees_annual", 0) for child in family_data.get("children", [])]),
            "healthcare_expenses": sum([parent.get("health_expenses", 0) for parent in family_data.get("parents", [])]),
            "optimization_potential": {
                "spouse_investments": 150000 if family_data.get("spouse", {}).get("annual_income", 0) == 0 else 0,
                "children_education_deduction": len(family_data.get("children", [])) * 30000,
                "parents_health_deduction": 50000 if any(p.get("is_senior_citizen") for p in family_data.get("parents", [])) else 25000
            }
        }
    
    def get_salary_structure_data(self) -> Dict[str, Any]:
        """Get salary structure for optimization"""
        if not self.tax_data:
            return {}
        
        employment = self.tax_data.get("employment", {})
        salary_structure = employment.get("salary_structure", {})
        
        return {
            "current_structure": salary_structure,
            "gross_salary": sum(salary_structure.values()),
            "taxable_components": {
                "basic_salary": salary_structure.get("basic_salary", 0),
                "special_allowance": salary_structure.get("special_allowance", 0)
            },
            "exempt_components": {
                "hra": salary_structure.get("hra", 0),
                "lta": salary_structure.get("lta", 0),
                "medical_allowance": salary_structure.get("medical_allowance", 0),
                "food_coupons": salary_structure.get("food_coupons", 0),
                "mobile_allowance": salary_structure.get("mobile_allowance", 0)
            },
            "pf_contribution": employment.get("pf_contribution", {}),
            "optimization_suggestions": [
                "Maximize HRA exemption",
                "Utilize LTA limit",
                "Optimize food coupons to ₹26,400",
                "Increase mobile/internet reimbursement"
            ]
        }
    
    def update_tax_investment(self, section: str, amount: float, investment_type: str):
        """Update tax-saving investment"""
        try:
            if section == "80C":
                if investment_type == "PPF":
                    self.tax_data["investments"]["ppf"]["current_year_contribution"] += amount
                elif investment_type == "ELSS":
                    self.tax_data["investments"]["elss"]["current_investments"] += amount
                
                # Update utilization
                current_80c = (self.tax_data["investments"]["ppf"]["current_year_contribution"] + 
                             self.tax_data["investments"]["elss"]["current_investments"])
                self.tax_data["optimization_opportunities"]["section_80c"]["current_utilization"] = min(current_80c, 150000)
                self.tax_data["optimization_opportunities"]["section_80c"]["remaining"] = max(0, 150000 - current_80c)
            
            elif section == "80CCD_1B":
                self.tax_data["investments"]["nps"]["additional_80ccd_1b"] += amount
                self.tax_data["optimization_opportunities"]["section_80ccd_1b"]["current_utilization"] = min(
                    self.tax_data["investments"]["nps"]["additional_80ccd_1b"], 50000)
            
            # Save updated data
            self._save_tax_data()
            print(f"✅ Updated {section} investment: ₹{amount:,.0f} in {investment_type}")
            
        except Exception as e:
            print(f"❌ Error updating tax investment: {e}")
    
    def _get_demo_tax_data(self) -> Dict[str, Any]:
        """Demo tax data for fallback"""
        return {
            "user_id": "demo_user",
            "tax_year": "2024-25",
            "income": {
                "annual_salary": 1200000,
                "total_gross_income": 1200000
            },
            "optimization_opportunities": {
                "section_80c": {"current_utilization": 100000, "limit": 150000, "remaining": 50000},
                "section_80ccd_1b": {"current_utilization": 0, "limit": 50000, "remaining": 50000},
                "section_80d": {"current_utilization": 25000, "limit": 75000, "remaining": 50000}
            },
            "investments": {"ppf": 100000, "elss": 0, "nps": 50000},
            "family": {"spouse": {"annual_income": 0}, "children": [], "parents": []}
        }
    
    # Keep original methods for backward compatibility
    def get_portfolio_data(self) -> Dict[str, Any]:
        """Get portfolio data from Fi JSON file"""
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
                    "sector": holding.get('sector', 'Unknown')
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
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary from Fi JSON file"""
        if not self.is_loaded:
            return self._get_demo_account()
        
        account_section = self.fi_data.get('account', {})
        profile_section = self.fi_data.get('user_profile', {})
        
        return {
            "account_id": account_section.get('account_id', ''),
            "user_id": self.fi_data.get('user_id', ''),
            "net_worth": float(account_section.get('net_worth', 0)),
            "investment_experience": profile_section.get('investment_experience', 'intermediate'),
            "risk_tolerance": profile_section.get('risk_tolerance', 'moderate'),
            "investment_goals": profile_section.get('investment_goals', ['long_term_growth']),
            "time_horizon": profile_section.get('time_horizon', '10+ years'),
            "age_range": profile_section.get('age_range', '30-40')
        }
    
    def _get_demo_data(self):
        """Fallback demo data"""
        return {
            "user_id": "demo_user",
            "total_value": 100000.00,
            "cash_balance": 5000.00,
            "holdings": [
                {
                    "symbol": "DEMO",
                    "company_name": "Demo Stock",
                    "quantity": 100.0,
                    "current_price": 950.00,
                    "market_value": 95000.00,
                    "cost_basis": 90000.00,
                    "unrealized_gain_loss": 5000.00,
                    "allocation_percentage": 95.0,
                    "sector": "Demo"
                }
            ],
            "performance": {
                "total_return": 5000.00,
                "total_return_percentage": 5.26,
                "day_change": -500.00,
                "day_change_percentage": -0.50,
                "ytd_change": 5000.00
            }
        }
    
    def _get_demo_account(self):
        """Fallback demo account"""
        return {
            "account_id": "demo_acc",
            "user_id": "demo_user",
            "net_worth": 120000.0,
            "investment_experience": "beginner",
            "risk_tolerance": "moderate",
            "investment_goals": ["long_term_growth"],
            "time_horizon": "10+ years",
            "age_range": "25-35"
        }