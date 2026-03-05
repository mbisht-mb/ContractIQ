from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber, io
from risk_engine import extract_clauses_with_llm, calculate_risk_score

app = FastAPI(title='ContractIQ API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/')
def health():
    return {'status': 'ContractIQ API is running'}

@app.post('/analyze')
async def analyze_contract(
    file: UploadFile = File(...),
    industry: str = Form(...)
):
    contents = await file.read()
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        text = ''
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + ' '
    extracted_clauses = extract_clauses_with_llm(text)
    result = calculate_risk_score(extracted_clauses, industry)
    return result
