from detectors import detect_pii, detect_secrets

REDACT_MAP = {
    "EMAIL": "[REDACTED_EMAIL]",
    "PHONE": "[REDACTED_PHONE]",
    "SSN": "[REDACTED_SSN]",
    "SECRET": "[REDACTED_SECRET]",
    "PERSON": "[REDACTED_NAME]",
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
