from detectors import detect_pii, detect_secrets

REDACT_MAP = {
    "EMAIL": "[REDACTED_EMAIL]",
    "PHONE": "[REDACTED_PHONE]",
    "SSN": "[REDACTED_SSN]",
    "SECRETS": "[REDACTED_SECRET]",  # Fixed: was "SECRET"
    "PERSON_NAME": "[REDACTED_NAME]",  # Fixed: was "PERSON"
    "CREDIT_CARD": "[REDACTED_CREDIT_CARD]",
    "BANK_ACCOUNT": "[REDACTED_BANK_ACCOUNT]",
    "DOB": "[REDACTED_DOB]",
    "DRIVERS_LICENSE": "[REDACTED_DRIVERS_LICENSE]",
    "MEDICAL_RECORD_NUMBER": "[REDACTED_MRN]",
    "ADDRESS": "[REDACTED_ADDRESS]",
}

def redact_text(text: str, findings: dict) -> str:
    spans = []
    for kind, items in findings.items():
        for it in items:
            start = it.get('start')
            end = it.get('end')
            spans.append((start, end, REDACT_MAP.get(kind, "[REDACTED]")))
    spans.sort(key=lambda s: s[0] or 0, reverse=True)
    out = text
    for start, end, token in spans:
        if start is None or end is None:
            continue
        out = out[:start] + token + out[end:]
    return out

def process_prompt(prompt: str):
    detected = {}
    pii = detect_pii(prompt)
    if pii:
        detected.update(pii)
    secrets = detect_secrets(prompt)
    if secrets:
        detected.update(secrets)
    redacted = redact_text(prompt, detected)
    return redacted, detected
