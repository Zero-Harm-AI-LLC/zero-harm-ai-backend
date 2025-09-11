from zero_harm_ai_detectors import detect_pii, detect_secrets, redact_text, RedactionStrategy, HarmfulTextDetector, DetectionConfig

# Initialize detector (do this once, not per request)
harmful_detector = HarmfulTextDetector()

def process_prompt_with_harmful_detection(prompt: str):
    """Process prompt with PII, secrets, and harmful content detection"""
    detected = {}
    
    # Detect PII and secrets
    pii = detect_pii(prompt)
    if pii:
        detected.update(pii)
    
    secrets = detect_secrets(prompt)
    if secrets:
        detected.update(secrets)
    
    # Detect harmful content
    harmful_result = harmful_detector.detect(prompt)
    if harmful_result['harmful']:
        detected['HARMFUL_CONTENT'] = [{
            'span': prompt,
            'start': 0,
            'end': len(prompt),
            'severity': harmful_result['severity'],
            'labels': harmful_result['active_labels']
        }]
    
    # Redact text
    if detected:
        redacted = redact_text(prompt, detected, strategy=RedactionStrategy.MASK_ALL)
    else:
        redacted = prompt
    
    return redacted, detected

# Optional: Keep custom redaction tokens if needed
def custom_redact_text(text: str, findings: dict) -> str:
    """Custom redaction with backend-specific tokens"""
    REDACT_MAP = {
        "EMAIL": "[REDACTED_EMAIL]",
        "PHONE": "[REDACTED_PHONE]",
        "SSN": "[REDACTED_SSN]",
        "SECRETS": "[REDACTED_SECRET]",
        "PERSON_NAME": "[REDACTED_NAME]",
        "CREDIT_CARD": "[REDACTED_CREDIT_CARD]",
        "BANK_ACCOUNT": "[REDACTED_BANK_ACCOUNT]",
        "DOB": "[REDACTED_DOB]",
        "DRIVERS_LICENSE": "[REDACTED_DRIVERS_LICENSE]",
        "MEDICAL_RECORD_NUMBER": "[REDACTED_MRN]",
        "ADDRESS": "[REDACTED_ADDRESS]",
    }
    
    spans = []
    for kind, items in findings.items():
        for item in items:
            start = item.get('start')
            end = item.get('end')
            if start is not None and end is not None:
                spans.append((start, end, REDACT_MAP.get(kind, "[REDACTED]")))
    
    # Sort by start position in reverse order to avoid index shifting
    spans.sort(key=lambda s: s[0], reverse=True)
    
    result = text
    for start, end, token in spans:
        result = result[:start] + token + result[end:]
    
    return result