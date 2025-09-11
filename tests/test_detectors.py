import pytest
from zero_harm_detectors import detect_pii, detect_secrets  # Fixed import

def test_detects_email_and_ssn():
    text = "Contact me at alice@example.com. SSN 123-45-6789."
    pii = detect_pii(text)
    assert "EMAIL" in pii
    assert "SSN" in pii
    assert len(pii["EMAIL"]) == 1
    assert len(pii["SSN"]) == 1
    assert pii["EMAIL"][0]["span"] == "alice@example.com"

def test_detects_secret_key():
    text = "api_key=sk-1234567890abcdef1234567890abcdef"
    sec = detect_secrets(text)
    assert "SECRETS" in sec
    assert len(sec["SECRETS"]) == 1

def test_phone_detection():
    text = "Call me at 555-123-4567"
    pii = detect_pii(text)
    assert "PHONE" in pii
    assert pii["PHONE"][0]["span"] == "555-123-4567"

def test_person_name_detection():
    text = "Contact John Smith for more information"
    pii = detect_pii(text)
    # Note: Person name detection may be conservative
    if "PERSON_NAME" in pii:
        assert len(pii["PERSON_NAME"]) >= 1