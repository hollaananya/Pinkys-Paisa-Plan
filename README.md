# Pinky's Paisa Plan – Agentic AI based Financial Planner

**An Emotion-Aware, Multi-Agent Financial Assistant Ecosystem**  
Personalized | Predictive | Family-Focused

---

## Overview

This project is a part of the *Agentic AI Hackathon*, aiming to revolutionize personal and family finance management using **emotionally intelligent, multi-agent systems**. It allows users to simulate financial futures, manage emotional spending, and coordinate family goals — all through intelligent agents working in sync.

---

## Core AI Agents

| Agent Name                | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| `TaxGenomeAgent`         | Uncovers tax-saving opportunities and auto-adjusts investment allocations   |
| `TimeMachineAgent`       | Simulates future financial states based on "what-if" life events            |
| `InvestmentTherapyAgent` | Detects stress-spending, provides emotional coaching and plan adjustments   |
| `FamilyOrchestrator`     | (Planned) Coordinates shared goals across family members                    |

---

## Technologies Used

- **Frontend:**  
  - `Streamlit` – Chat interface and visualization  
  - `streamlit-chat`, `streamlit-option-menu`, `matplotlib`, `plotly`, `pandas`

- **Backend & AI Agents:**  
  - Python classes for each agent  
  - `google-cloud-aiplatform` (Gemini) for reasoning  
  - Fi MCP sample data


---


---

## Getting Started

### Prerequisites
- Python 3.8+
- Google Cloud credentials (for Gemini)
- Fi MCP access (or mocked JSON)

### Setup Instructions

```bash
# Clone the repo
git clone https://github.com/hollaananya/family-financial-planner.git
cd family-financial-planner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requiremnts.txt

# Set up environment variables
cp .env.example .env
# Fill in your keys in the .env file

# Run the app
streamlit run main_app.py

