"""
Tax calculation utilities for Indian tax system
"""
from typing import Dict, Any, Tuple
from .config import (
    TAX_SLABS_OLD_REGIME, 
    TAX_SLABS_NEW_REGIME,
    SECTION_80C_LIMIT,
    SECTION_80D_LIMIT,
    SECTION_80D_SENIOR_LIMIT,
    SECTION_80CCD_1B_LIMIT,
    SECTION_24B_LIMIT
)

def calculate_tax_old_regime(gross_income: float, deductions: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate tax under old regime with deductions
    """
    # Standard deduction
    standard_deduction = min(50000, gross_income)
    
    # Section 80C deductions
    section_80c = min(deductions.get('section_80c', 0), SECTION_80C_LIMIT)
    
    # Section 80D deductions
    section_80d = min(deductions.get('section_80d', 0), SECTION_80D_LIMIT)
    section_80d_parents = min(deductions.get('section_80d_parents', 0), SECTION_80D_SENIOR_LIMIT)
    
    # Section 80CCD(1B) - NPS
    section_80ccd_1b = min(deductions.get('section_80ccd_1b', 0), SECTION_80CCD_1B_LIMIT)
    
    # Section 24(b) - Home loan interest
    section_24b = min(deductions.get('section_24b', 0), SECTION_24B_LIMIT)
    
    # Total deductions
    total_deductions = (
        standard_deduction + 
        section_80c + 
        section_80d + 
        section_80d_parents + 
        section_80ccd_1b + 
        section_24b
    )
    
    # Taxable income
    taxable_income = max(0, gross_income - total_deductions)
    
    # Calculate tax
    tax = calculate_tax_from_slabs(taxable_income, TAX_SLABS_OLD_REGIME)
    
    # Add cess (4% on income tax)
    cess = tax * 0.04
    total_tax = tax + cess
    
    return {
        'regime': 'old',
        'gross_income': gross_income,
        'standard_deduction': standard_deduction,
        'total_deductions': total_deductions,
        'taxable_income': taxable_income,
        'income_tax': tax,
        'cess': cess,
        'total_tax': total_tax,
        'deduction_breakdown': {
            'section_80c': section_80c,
            'section_80d': section_80d,
            'section_80d_parents': section_80d_parents,
            'section_80ccd_1b': section_80ccd_1b,
            'section_24b': section_24b,
            'standard_deduction': standard_deduction
        }
    }

def calculate_tax_new_regime(gross_income: float) -> Dict[str, Any]:
    """
    Calculate tax under new regime (no deductions except standard)
    """
    # Standard deduction
    standard_deduction = min(75000, gross_income)  # Increased in new regime
    
    # Taxable income
    taxable_income = max(0, gross_income - standard_deduction)
    
    # Calculate tax
    tax = calculate_tax_from_slabs(taxable_income, TAX_SLABS_NEW_REGIME)
    
    # Add cess (4% on income tax)
    cess = tax * 0.04
    total_tax = tax + cess
    
    return {
        'regime': 'new',
        'gross_income': gross_income,
        'standard_deduction': standard_deduction,
        'total_deductions': standard_deduction,
        'taxable_income': taxable_income,
        'income_tax': tax,
        'cess': cess,
        'total_tax': total_tax
    }

def calculate_tax_from_slabs(taxable_income: float, tax_slabs: list) -> float:
    """
    Calculate tax based on tax slabs
    """
    tax = 0
    previous_limit = 0
    
    for limit, rate in tax_slabs:
        if taxable_income <= previous_limit:
            break
            
        taxable_in_slab = min(taxable_income, limit) - previous_limit
        tax += taxable_in_slab * rate
        
        if taxable_income <= limit:
            break
            
        previous_limit = limit
    
    return tax

def compare_tax_regimes(gross_income: float, deductions: Dict[str, float]) -> Dict[str, Any]:
    """
    Compare old vs new tax regime
    """
    old_regime = calculate_tax_old_regime(gross_income, deductions)
    new_regime = calculate_tax_new_regime(gross_income)
    
    savings = old_regime['total_tax'] - new_regime['total_tax']
    recommended = 'new' if savings < 0 else 'old'
    
    return {
        'old_regime': old_regime,
        'new_regime': new_regime,
        'savings_with_old': savings,
        'recommended_regime': recommended,
        'comparison': {
            'tax_difference': abs(savings),
            'percentage_savings': (abs(savings) / max(old_regime['total_tax'], new_regime['total_tax'])) * 100
        }
    }

def calculate_advance_tax_due(annual_tax: float, tds_paid: float, advance_tax_paid: float) -> Dict[str, Any]:
    """
    Calculate advance tax due for remaining quarters
    """
    remaining_liability = annual_tax - tds_paid - advance_tax_paid
    
    # Advance tax payment schedule (cumulative percentages)
    schedule = {
        'Q1': 0.15,  # 15% by June 15
        'Q2': 0.45,  # 45% by Sept 15  
        'Q3': 0.75,  # 75% by Dec 15
        'Q4': 1.00   # 100% by March 15
    }
    
    return {
        'total_annual_tax': annual_tax,
        'tds_paid': tds_paid,
        'advance_tax_paid': advance_tax_paid,
        'remaining_liability': remaining_liability,
        'payment_schedule': schedule,
        'next_due_amount': max(0, remaining_liability)
    }