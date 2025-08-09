"""\nDetectors using spaCy NER when available, falling back to regex heuristics.\n"""
try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    _nlp = None

import re

def _locate_spans(text, pattern):
    out = []
    for m in pattern.finditer(text):
        out.append({"span": m.group(0), "start": m.start(), "end": m.end()})
    return out

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
SSN_RE = re.compile(r"\\b\\d{3}-\\d{2}-\\d{4}\\b")
API_KEY_RE = re.compile(r"(?:api[_-]?key|secret|token)[\\s:=]*[A-Za-z0-9\\-_]{8,}")

def detect_pii(text):
    out = {}
    # Prefer spaCy named entity recognition for PERSON / ORG etc.
    if _nlp is not None:
        doc = _nlp(text)
        persons = []
        for ent in doc.ents:
            if ent.label_ in ("PERSON", "ORG", "GPE", "LOC"):
                persons.append({"span": ent.text, "start": ent.start_char, "end": ent.end_char, "label": ent.label_})
        if persons:
            out["PERSON"] = persons

    # Regex-based detectors for structured PII
    emails = _locate_spans(text, EMAIL_RE)
    if emails:
        out["EMAIL"] = emails
    phones = _locate_spans(text, PHONE_RE)
    if phones:
        out["PHONE"] = phones
    ssns = _locate_spans(text, SSN_RE)
    if ssns:
        out["SSN"] = ssns

    # If spaCy not available, provide a crude PERSON heuristic
    if _nlp is None:
        person_re = re.compile(r"\\b([A-Z][a-z]{1,20}\\s+[A-Z][a-z]{1,20})\\b")
        persons = _locate_spans(text, person_re)
        persons = [p for p in persons if not p['span'].lower().startswith('the ')]
        if persons:
            out["PERSON"] = persons

    return out

def detect_secrets(text):
    out = {}
    keys = _locate_spans(text, API_KEY_RE)
    if keys:
        out["SECRET"] = keys
    return out
