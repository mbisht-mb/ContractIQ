import requests, os, json
from sheets_db import get_risk_clauses, get_industry_multiplier

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
# Override with GROQ_MODEL if you need to swap models without code changes
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

def extract_clauses_with_llm(contract_text):
    """
    Sends contract text to Groq (LLaMA3 model).
    Returns a dict of which risk clauses were found,
    plus supporting quotes and confidence levels.
    """
    prompt = f"""
You are a senior corporate contract attorney with 20 years of experience
reviewing vendor agreements, SaaS contracts, and service agreements.

Carefully read the contract below and analyze it for the following four
risk clauses. Look for the MEANING of each clause, not just exact words.

--- CLAUSE DEFINITIONS ---

1. UNLIMITED LIABILITY
   The vendor or party faces no cap on financial damages they could owe.
   Look for: absence of liability caps, phrases like 'shall not be limited',
   'liable for all damages', 'unlimited damages', or any section where a
   liability limitation clause is explicitly waived or absent.

2. BROAD INDEMNIFICATION
   One party must defend and pay costs for the other party's legal claims,
   including third-party lawsuits.
   Look for: 'shall indemnify and hold harmless', 'defend against any claims',
   indemnification covering third parties, IP infringement indemnity,
   or indemnity with no carve-outs for gross negligence.

3. AUTOMATIC RENEWAL
   The contract renews automatically without requiring explicit action.
   Look for: 'automatically renew', 'shall continue unless terminated',
   'evergreen clause', or renewal language with short cancellation windows.

4. TERMINATION RESTRICTION
   The contract is difficult or costly to exit before the term ends.
   Look for: long notice periods (90+ days), early termination fees,
   penalties for cancellation, or language requiring cause to terminate.

--- INSTRUCTIONS ---

Return ONLY a valid JSON object. No explanation, no markdown, no code fences.
If you are uncertain about a clause, lean toward true and note it in the quote.
For quotes: copy the most relevant 1-2 sentences directly from the contract.
For confidence: use high if clearly present, medium if implied, low if uncertain.

{{
    "unlimited_liability": true or false,
    "broad_indemnification": true or false,
    "automatic_renewal": true or false,
    "termination_restriction": true or false,
    "unlimited_liability_quote": "1-2 sentence quote from contract, or empty string",
    "broad_indemnification_quote": "1-2 sentence quote or empty string",
    "automatic_renewal_quote": "1-2 sentence quote or empty string",
    "termination_restriction_quote": "1-2 sentence quote or empty string",
    "unlimited_liability_confidence": "high, medium, or low",
    "broad_indemnification_confidence": "high, medium, or low",
    "automatic_renewal_confidence": "high, medium, or low",
    "termination_restriction_confidence": "high, medium, or low"
}}

Contract:
{contract_text[:8000]}
    """

    if not GROQ_API_KEY:
        raise RuntimeError(
            'Missing GROQ_API_KEY environment variable. Set GROQ_API_KEY to a valid Groq API key.'
        )

    # If the configured/default model is not available in the account, try a few common alternatives.
    candidates = [GROQ_MODEL, 'llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768']
    last_error = None
    for model in candidates:
        if not model:
            continue
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1
            }
        )

        if response.ok:
            data = response.json()
            if 'choices' in data and data['choices']:
                raw = data['choices'][0]['message']['content']
                break
            last_error = RuntimeError(f'Groq API response missing choices: {data}')
            break

        # If the model isn't found or is decommissioned, try the next candidate.
        try:
            err = response.json().get('error', {})
        except Exception:
            err = {}

        if err.get('code') in {'model_not_found', 'model_decommissioned'}:
            last_error = RuntimeError(
                f'Groq API model issue (model={model}): {response.text}'
            )
            continue

        # Otherwise, stop and surface the error.
        last_error = RuntimeError(
            f'Groq API request failed (status {response.status_code}): {response.text}'
        )
        break

    if last_error is not None and 'raw' not in locals():
        raise last_error

    # Groq sometimes wraps JSON in ```json ... ``` markdown fences.
    # This strips them so json.loads() does not crash.
    clean = raw.strip()
    if clean.startswith('```'):
        clean = clean.split('```')[1]
        if clean.startswith('json'):
            clean = clean[4:]
    clean = clean.strip()

    return json.loads(clean)


def calculate_risk_score(extracted, industry):
    """
    Takes the LLM output and calculates a numeric risk score
    using weights from Google Sheets.
    Confidence level adjusts the weight: medium = 70%, low = 40%.
    """
    clauses    = get_risk_clauses()
    multiplier = get_industry_multiplier(industry)

    key_map = {
        'unlimited liability':     'unlimited_liability',
        'broad indemnification':   'broad_indemnification',
        'automatic renewal':       'automatic_renewal',
        'termination restriction': 'termination_restriction',
    }

    confidence_weights = {'high': 1.0, 'medium': 0.7, 'low': 0.4}

    total_score   = 0
    clause_results = []

    for clause in clauses:
        json_key   = key_map.get(clause['clause_keyword'], '')
        detected   = extracted.get(json_key, False)
        quote      = extracted.get(json_key + '_quote', '')
        confidence = extracted.get(json_key + '_confidence', 'high')

        if detected:
            conf_mult    = confidence_weights.get(confidence, 1.0)
            total_score += int(clause['risk_weight']) * conf_mult

        clause_results.append({
            'name':       clause['clause_keyword'].title(),
            'category':   clause['category'],
            'weight':     clause['risk_weight'],
            'detected':   detected,
            'quote':      quote,
            'confidence': confidence,
        })

    final_score = int(total_score * multiplier)

    exposure = 'Low'
    if final_score > 70:   exposure = 'High'
    elif final_score > 40: exposure = 'Medium'

    return {
        'risk_score':          final_score,
        'exposure':            exposure,
        'industry_multiplier': multiplier,
        'clause_breakdown':    clause_results,
        'detected_count':      sum(1 for c in clause_results if c['detected'])
    }
