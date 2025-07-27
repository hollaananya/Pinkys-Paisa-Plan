import google.generativeai as genai
import json
import re
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
from utils.fi_mcp_client import FiMCPClient
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

load_dotenv()

class TaxRegime(Enum):
    OLD = "old"
    NEW = "new"

@dataclass
class TaxCalculation:
    gross_income: float
    taxable_income: float
    tax_liability: float
    cess: float
    total_tax: float
    deductions_used: Dict[str, float]
    regime: TaxRegime
    effective_tax_rate: float

class TaxGenomeAgent:
    def __init__(self):
        # Try Gemini API first
        self.gemini_available = False
        self.model = None
        
        # Configure Gemini API
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Test the connection
                test_response = self.model.generate_content("Hello")
                self.gemini_available = True
                print("✅ Tax Genome Agent - Gemini API connected successfully!")
                
            except Exception as e:
                print(f"⚠️ Gemini API error: {e}")
                print("🔄 Using advanced fallback responses")
        else:
            print("⚠️ No Gemini API key found")
            print("🔄 Using advanced fallback responses")
        
        self.fi_client = FiMCPClient()
        self.tax_year = "2024-25"
        self.standard_deduction = 50000
        
        # Tax slabs for FY 2024-25
        self.old_regime_slabs = [
            {"min": 0, "max": 250000, "rate": 0.0},
            {"min": 250000, "max": 500000, "rate": 0.05},
            {"min": 500000, "max": 1000000, "rate": 0.20},
            {"min": 1000000, "max": float('inf'), "rate": 0.30}
        ]
        
        self.new_regime_slabs = [
            {"min": 0, "max": 300000, "rate": 0.0},
            {"min": 300000, "max": 600000, "rate": 0.05},
            {"min": 600000, "max": 900000, "rate": 0.10},
            {"min": 900000, "max": 1200000, "rate": 0.15},
            {"min": 1200000, "max": 1500000, "rate": 0.20},
            {"min": 1500000, "max": float('inf'), "rate": 0.30}
        ]
        
        # Deduction limits
        self.deduction_limits = {
            "80C": 150000,
            "80CCD_1B": 50000,
            "80D": 75000,
            "24B": 200000,
            "80E": float('inf'),
            "80TTA": 10000,
            "80TTB": 50000
        }
    
    def analyze_tax_situation(self, user_message: str) -> Dict[str, Any]:
        """Analyze user's tax situation from their query"""
        try:
            # Get financial data
            financial_data = self.fi_client.get_tax_profile_data()
            
            if not financial_data:
                return {"error": "Unable to fetch financial data"}
            
            # Calculate current tax liability
            gross_income = financial_data.get("annual_income", 0)
            current_deductions = financial_data.get("current_deductions", {})
            
            # Tax calculations for both regimes
            old_regime_tax = self._calculate_tax_liability(gross_income, TaxRegime.OLD, current_deductions)
            new_regime_tax = self._calculate_tax_liability(gross_income, TaxRegime.NEW, {})
            
            # Generate optimization recommendations
            optimization = self._optimize_deductions(gross_income, financial_data)
            
            analysis = {
                "gross_income": gross_income,
                "current_tax_old_regime": old_regime_tax,
                "current_tax_new_regime": new_regime_tax,
                "recommended_regime": "OLD" if old_regime_tax.total_tax < new_regime_tax.total_tax else "NEW",
                "potential_savings": optimization.get("total_potential_savings", 0),
                "optimization_recommendations": optimization,
                "urgent_actions": self._get_urgent_tax_actions(financial_data),
                "financial_data": financial_data
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing tax situation: {str(e)}")
            return {"error": str(e)}
    
    def generate_tax_response(self, user_message: str, tax_analysis: Dict[str, Any]) -> str:
        """Generate comprehensive tax advice using Gemini API"""
        if not self.gemini_available:
            return self._generate_fallback_tax_response(user_message, tax_analysis)
        
        # Extract key data
        gross_income = tax_analysis.get("gross_income", 0)
        old_tax = tax_analysis.get("current_tax_old_regime")
        new_tax = tax_analysis.get("current_tax_new_regime")
        potential_savings = tax_analysis.get("potential_savings", 0)
        financial_data = tax_analysis.get("financial_data", {})
        
        tax_prompt = f"""
You are the Tax Genome Agent - an AI-powered tax optimization expert specializing in Indian taxation.

USER QUERY: "{user_message}"

CURRENT TAX SITUATION:
- Annual Income: ₹{gross_income:,.0f}
- Old Regime Tax: ₹{old_tax.total_tax if old_tax else 0:,.0f}
- New Regime Tax: ₹{new_tax.total_tax if new_tax else 0:,.0f}
- Recommended Regime: {tax_analysis.get("recommended_regime", "OLD")}
- Potential Annual Savings: ₹{potential_savings:,.0f}

CURRENT INVESTMENTS & DEDUCTIONS:
- PPF: ₹{financial_data.get("investments", {}).get("ppf", 0):,.0f}
- ELSS: ₹{financial_data.get("investments", {}).get("elss", 0):,.0f}
- NPS: ₹{financial_data.get("investments", {}).get("nps", 0):,.0f}
- Home Loan Interest: ₹{financial_data.get("loans", {}).get("home_loan_interest", 0):,.0f}
- Health Insurance: ₹{financial_data.get("insurance", {}).get("health_premium", 0):,.0f}

FAMILY CONTEXT:
- Spouse Income: ₹{financial_data.get("family", {}).get("spouse_income", 0):,.0f}
- Children: {len(financial_data.get("family", {}).get("children", []))}
- Senior Citizen Parents: {len([p for p in financial_data.get("family", {}).get("parents", []) if p.get("is_senior_citizen")])}

Provide comprehensive tax advice that includes:

1. **Tax Regime Analysis**: Compare old vs new regime with specific numbers
2. **Immediate Optimization**: Top 3 actions to save taxes this fiscal year
3. **Investment Recommendations**: Specific suggestions for remaining 80C, 80CCD(1B), 80D limits
4. **Family Tax Planning**: How to optimize across family members
5. **Salary Structure**: If employee, suggest optimizations
6. **Timeline**: Critical dates and deadlines
7. **Potential Savings**: Quantify the financial impact

Be specific with amounts, sections, and actionable recommendations. Use a professional yet approachable tone.
Keep response comprehensive but well-structured (4-5 paragraphs with clear sections).
"""
        
        try:
            response = self.model.generate_content(tax_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error in Gemini tax response: {e}")
            return self._generate_fallback_tax_response(user_message, tax_analysis)
    
    def generate_comprehensive_tax_response(self, user_message: str) -> str:
        """Main method to handle tax-related queries"""
        
        # Analyze the tax situation
        tax_analysis = self.analyze_tax_situation(user_message)
        
        if "error" in tax_analysis:
            return f"I'm sorry, I encountered an issue accessing your financial data: {tax_analysis['error']}. Please ensure your financial profile is updated and try again."
        
        # Generate comprehensive response
        return self.generate_tax_response(user_message, tax_analysis)
    
    def _calculate_tax_liability(self, gross_income: float, regime: TaxRegime, deductions: Dict[str, float] = None) -> TaxCalculation:
        """Calculate tax liability for given regime"""
        if deductions is None:
            deductions = {}
        
        # Select tax slabs
        slabs = self.old_regime_slabs if regime == TaxRegime.OLD else self.new_regime_slabs
        
        # Calculate taxable income
        total_deductions = sum(deductions.values()) if regime == TaxRegime.OLD else 0
        if regime == TaxRegime.OLD:
            total_deductions += self.standard_deduction
        
        taxable_income = max(0, gross_income - total_deductions)
        
        # Calculate tax
        tax_liability = 0
        remaining_income = taxable_income
        
        for slab in slabs:
            if remaining_income <= 0:
                break
            
            slab_income = min(remaining_income, slab["max"] - slab["min"])
            if slab_income > 0:
                tax_liability += slab_income * slab["rate"]
                remaining_income -= slab_income
        
        # Add 4% cess
        cess = tax_liability * 0.04
        total_tax = tax_liability + cess
        
        return TaxCalculation(
            gross_income=gross_income,
            taxable_income=taxable_income,
            tax_liability=tax_liability,
            cess=cess,
            total_tax=total_tax,
            deductions_used=deductions,
            regime=regime,
            effective_tax_rate=(total_tax / gross_income) * 100 if gross_income > 0 else 0
        )
    
    def _optimize_deductions(self, gross_income: float, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization recommendations"""
        recommendations = {
            "section_80c": [],
            "section_80ccd_1b": [],
            "section_80d": [],
            "section_24b": [],
            "family_optimizations": [],
            "total_potential_savings": 0
        }
        
        # Current investments
        current_investments = financial_data.get("investments", {})
        ppf_amount = current_investments.get("ppf", {}).get("current_year_contribution", 0)
        elss_amount = current_investments.get("elss", {}).get("current_investments", 0)
        current_80c = ppf_amount + elss_amount
        
        # Section 80C optimization
        if current_80c < 150000:
            remaining_80c = 150000 - current_80c
            tax_rate = 0.30 if gross_income > 1000000 else 0.20
            recommendations["section_80c"].append({
                "message": f"Invest additional ₹{remaining_80c:,.0f} under Section 80C",
                "tax_savings": remaining_80c * tax_rate,
                "suggestions": [
                    f"PPF: ₹{min(remaining_80c, 150000):,.0f}",
                    f"ELSS: ₹{min(remaining_80c, 100000):,.0f}",
                    "Life Insurance Premium"
                ]
            })
        
        # Section 80CCD(1B) - NPS
        current_nps = current_investments.get("nps_additional", 0)
        if current_nps < 50000:
            remaining_nps = 50000 - current_nps
            tax_rate = 0.30 if gross_income > 1000000 else 0.20
            recommendations["section_80ccd_1b"].append({
                "message": f"Additional NPS investment of ₹{remaining_nps:,.0f}",
                "tax_savings": remaining_nps * tax_rate
            })
        
        # Section 80D - Health Insurance
        current_health = financial_data.get("insurance", {}).get("health_premium", 0)
        max_80d = 75000  # 25K self + 50K parents
        if current_health < max_80d:
            remaining_80d = max_80d - current_health
            tax_rate = 0.30 if gross_income > 1000000 else 0.20
            recommendations["section_80d"].append({
                "message": f"Increase health insurance by ₹{remaining_80d:,.0f}",
                "tax_savings": remaining_80d * tax_rate
            })
        
        # Calculate total potential savings
        total_savings = sum([
            sum([r.get("tax_savings", 0) for r in recommendations["section_80c"]]),
            sum([r.get("tax_savings", 0) for r in recommendations["section_80ccd_1b"]]),
            sum([r.get("tax_savings", 0) for r in recommendations["section_80d"]])
        ])
        
        recommendations["total_potential_savings"] = total_savings
        
        return recommendations
    
    def _get_urgent_tax_actions(self, financial_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Get urgent actions based on current date"""
        current_date = datetime.now()
        month = current_date.month
        
        urgent_actions = []
        
        # Time-sensitive actions based on month
        if month >= 1 and month <= 3:  # Jan-Mar: Last chance for tax savings
            urgent_actions.append({
                "action": "Complete 80C investments before March 31st",
                "deadline": "March 31, 2025",
                "priority": "HIGH"
            })
        
        if month >= 4 and month <= 7:  # Apr-Jul: New FY planning + ITR filing
            urgent_actions.append({
                "action": "File ITR for previous year",
                "deadline": "July 31, 2025",
                "priority": "HIGH"
            })
        
        if month in [6, 9, 12, 3]:  # Advance tax months
            urgent_actions.append({
                "action": "Pay advance tax installment",
                "deadline": f"{['June 15', 'September 15', 'December 15', 'March 15'][month//3 - (1 if month < 4 else 2)]}",
                "priority": "MEDIUM"
            })
        
        return urgent_actions
    
    def _generate_fallback_tax_response(self, user_message: str, tax_analysis: Dict[str, Any]) -> str:
        """Fallback response when Gemini is not available"""
        if "error" in tax_analysis:
            return "I'm currently unable to access your complete tax profile. However, I can provide general tax optimization guidance. What specific tax concern would you like help with?"
        
        gross_income = tax_analysis.get("gross_income", 0)
        old_tax = tax_analysis.get("current_tax_old_regime")
        new_tax = tax_analysis.get("current_tax_new_regime")
        potential_savings = tax_analysis.get("potential_savings", 0)
        
        return f"""
## 🧬 Tax Genome Analysis

**Your Current Tax Situation:**
- Annual Income: ₹{gross_income:,.0f}
- Old Regime Tax: ₹{old_tax.total_tax if old_tax else 0:,.0f} ({old_tax.effective_tax_rate if old_tax else 0:.1f}%)
- New Regime Tax: ₹{new_tax.total_tax if new_tax else 0:,.0f} ({new_tax.effective_tax_rate if new_tax else 0:.1f}%)
- **Recommended:** {tax_analysis.get("recommended_regime", "OLD")} Regime

**💰 Immediate Optimization Opportunities:**
You can potentially save ₹{potential_savings:,.0f} annually through strategic tax planning:

1. **Section 80C**: Maximize your ₹1,50,000 limit through PPF, ELSS, or life insurance
2. **Section 80CCD(1B)**: Additional ₹50,000 NPS investment
3. **Section 80D**: Optimize health insurance coverage (₹25K + ₹50K for parents)

**🎯 Next Steps:**
- Review your current deductions and identify gaps
- Consider family tax planning strategies
- Plan systematic investments for remaining fiscal year
- Optimize salary structure if you're employed

Would you like me to dive deeper into any specific area of tax optimization?
"""

    def classify_tax_question(self, user_message: str) -> Dict[str, Any]:
        """Classify the type of tax question"""
        message_lower = user_message.lower()
        
        classification = {
            'type': 'general_tax',
            'specific_area': None,
            'urgency': 'medium',
            'requires_calculation': False
        }
        
        # Tax regime comparison
        if any(word in message_lower for word in ['old regime', 'new regime', 'which regime', 'regime comparison']):
            classification['type'] = 'regime_comparison'
            classification['requires_calculation'] = True
        
        # Deduction optimization
        elif any(word in message_lower for word in ['80c', '80d', 'deduction', 'tax saving', 'investment']):
            classification['type'] = 'deduction_optimization'
            classification['specific_area'] = 'deductions'
        
        # Family tax planning
        elif any(word in message_lower for word in ['family', 'spouse', 'children', 'parents']):
            classification['type'] = 'family_planning'
        
        # Salary optimization
        elif any(word in message_lower for word in ['salary', 'hra', 'allowance', 'employer']):
            classification['type'] = 'salary_optimization'
        
        # Urgent/deadline related
        elif any(word in message_lower for word in ['deadline', 'urgent', 'last date', 'march 31']):
            classification['urgency'] = 'high'
        
        return classification