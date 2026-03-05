import gspread
from google.oauth2.service_account import Credentials
import os, json

def get_sheets_client():
    # On Render, credentials come from environment variable.
    # In Codespaces for testing, you can also put your service account JSON in a
    # local `credentials.json` file and it will be used if the env var is missing.
    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if creds_json:
        creds_dict = json.loads(creds_json)
    else:
        with open('credentials.json', 'r') as f:
            creds_dict = json.load(f)

    scopes = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def get_risk_clauses():
    client = get_sheets_client()
    sheet = client.open('ContractIQ Risk Database')
    rows = sheet.worksheet('risk_clauses').get_all_records()
    return rows

def get_industry_multiplier(industry):
    client = get_sheets_client()
    sheet = client.open('ContractIQ Risk Database')
    rows = sheet.worksheet('industry_multipliers').get_all_records()
    for row in rows:
        if row['industry'].lower() == industry.lower():
            return float(row['multiplier'])
    return 1.0
