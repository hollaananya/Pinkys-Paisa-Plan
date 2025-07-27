"""
Configuration settings for Tax Genome Agent
"""
import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "fi_data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Data files
USER_TAX_DATA_FILE = DATA_DIR / "user_tax_data.json"
USER_FINANCIAL_DATA_FILE = DATA_DIR / "user_financial_data.json"

# Tax calculation constants
TAX_SLABS_OLD_REGIME = [
    (250000, 0.0),
    (500000, 0.05),
    (1000000, 0.20),
    (float('inf'), 0.30)
]

TAX_SLABS_NEW_REGIME = [
    (300000, 0.0),
    (600000, 0.05),
    (900000, 0.10),
    (1200000, 0.15),
    (1500000, 0.20),
    (float('inf'), 0.30)
]

# Section limits
SECTION_80C_LIMIT = 150000
SECTION_80D_LIMIT = 25000
SECTION_80D_SENIOR_LIMIT = 50000
SECTION_80CCD_1B_LIMIT = 50000
SECTION_24B_LIMIT = 200000

# API settings
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)