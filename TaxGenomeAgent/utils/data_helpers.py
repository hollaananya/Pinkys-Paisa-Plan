"""
Data processing helpers for Tax Genome Agent
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from .config import USER_TAX_DATA_FILE, USER_FINANCIAL_DATA_FILE

def load_json_file(file_path: str) -> Optional[Dict[Any, Any]]:
    """
    Load JSON data from file with error handling
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            print(f"⚠️ File not found: {file_path}")
            return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None

def save_json_file(data: Dict[Any, Any], file_path: str) -> bool:
    """
    Save data to JSON file with error handling
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(f"💾 Saved data to {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving to {file_path}: {e}")
        return False

def validate_tax_data_structure(data: Dict[Any, Any]) -> bool:
    """
    Validate if tax data has required structure
    """
    required_keys = ['income', 'investments', 'loans', 'insurance', 'family']
    
    if not isinstance(data, dict):
        return False
    
    for key in required_keys:
        if key not in data:
            print(f"⚠️ Missing required key: {key}")
            return False
    
    # Check income structure
    if 'income' in data:
        income_keys = ['monthly_salary', 'annual_salary', 'total_gross_income']
        for key in income_keys:
            if key not in data['income']:
                print(f"⚠️ Missing income key: {key}")
                return False
    
    return True

def generate_sample_tax_data() -> Dict[Any, Any]:
    """
    Generate sample tax data structure
    """
    return {
        "user_id": "user_12345",
        "tax_year": "2024-25",
        "last_updated": "2025-01-25T10:30:00Z",
        
        "income": {
            "annual_salary": 1200000,
            "monthly_salary": 100000,
            "bonus": 180000,
            "other_income": {
                "dividend_income": 15000,
                "interest_income": 25000,
                "capital_gains": 45000,
                "rental_income": 0
            },
            "total_gross_income": 1465000
        },
        
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
            }
        },
        
        "loans": {
            "home_loan": {
                "outstanding_principal": 2500000,
                "annual_interest_paid": 180000,
                "principal_repayment": 150000
            }
        },
        
        "insurance": {
            "health_insurance": {
                "self_family_premium": 18000,
                "parents_premium": 35000,
                "is_parents_senior_citizen": True
            }
        },
        
        "family": {
            "spouse": {
                "name": "Spouse",
                "annual_income": 0,
                "is_working": False,
                "age": 32
            },
            "children": [],
            "parents": []
        }
    }

def ensure_data_files_exist():
    """
    Ensure all required data files exist with proper structure
    """
    # Check tax data file
    if not os.path.exists(USER_TAX_DATA_FILE):
        print("📁 Creating sample tax data file...")
        sample_data = generate_sample_tax_data()
        save_json_file(sample_data, str(USER_TAX_DATA_FILE))
    
    # Check financial data file
    if not os.path.exists(USER_FINANCIAL_DATA_FILE):
        print("📁 Creating sample financial data file...")
        financial_data = {
            "user_id": "user_12345",
            "accounts": [],
            "transactions": [],
            "budgets": {}
        }
        save_json_file(financial_data, str(USER_FINANCIAL_DATA_FILE))