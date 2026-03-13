ContractIQ

AI-powered contract risk analyzer that detects risky clauses in contracts and calculates a structured risk score.

ContractIQ analyzes uploaded PDF contracts using a large language model to detect clauses such as unlimited liability, indemnification, automatic renewal, and termination restrictions. The system then calculates a risk exposure score using configurable weights stored in a Google Sheets database.

Features

Upload and analyze contract PDFs

AI-based clause detection using Groq LLaMA3

Evidence-based analysis with extracted quotes

Risk scoring based on clause weights

Industry-based risk multipliers

Live risk database using Google Sheets

Tech Stack

Backend

Python

FastAPI

Uvicorn

AI

Groq API (LLaMA3)

Data Source

Google Sheets API

gspread

PDF Processing

pdfplumber

Frontend

React + Tailwind (Lovable)

Deployment

Render

Project Structure
contractiq-backend/
│
├── main.py
├── risk_engine.py
├── sheets_db.py
├── requirements.txt
└── README.md

main.py
API entry point and contract analysis endpoint.

risk_engine.py
Handles LLM clause detection and risk scoring.

sheets_db.py
Connects to Google Sheets to retrieve risk weights and industry multipliers.

requirements.txt
Python dependencies.

Running the Backend

Install dependencies

pip install -r requirements.txt

Set environment variables

GROQ_API_KEY=your_api_key
GOOGLE_CREDENTIALS_JSON='your_google_service_account_json'

Run the server

uvicorn main:app --reload --port 8000

Open API docs

http://localhost:8000/docs
API Endpoint
POST /analyze

Analyzes a contract and returns a risk score.

Inputs:

file → contract PDF

industry → SaaS / Manufacturing / Consulting

Example output:

{
  "risk_score": 82,
  "exposure": "High",
  "industry_multiplier": 1.2,
  "detected_count": 3,
  "clause_breakdown": [...]
}
Deployment

Backend is deployed using Render.

Start command:

uvicorn main:app --host 0.0.0.0 --port $PORT

Required environment variables:

GROQ_API_KEY

GOOGLE_CREDENTIALS_JSON

Purpose

ContractIQ is designed as a first-pass contract risk screening tool to help teams quickly identify legal and financial exposure before signing agreements.
