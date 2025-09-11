#!/usr/bin/env python3
"""
Test script to verify the workflow works end-to-end
"""

def test_library_import():
    """Test that the library can be imported"""
    try:
        from zero_harm_ai_detectors import detect_pii, detect_secrets, HarmfulTextDetector  # Fixed import
        print("✅ Library import successful")
        return True
    except ImportError as e:
        print(f"❌ Library import failed: {e}")
        return False

def test_proxy_integration():
    """Test the proxy.py integration"""
    try:
        from proxy import process_prompt
        
        text = "Email me at test@example.com with secret sk-abc123"
        redacted, detected = process_prompt(text)
        
        # Check that redaction occurred (exact format depends on strategy chosen)
        assert redacted != text
        assert len(detected) > 0
        
        print("✅ Proxy integration working")
        print(f"Original: {text}")
        print(f"Redacted: {redacted}")
        print(f"Detected: {list(detected.keys())}")
        return True
    except Exception as e:
        print(f"❌ Proxy integration failed: {e}")
        return False

def test_pii_detection():
    """Test PII detection functionality"""
    try:
        from zero_harm_ai_detectors import detect_pii
        
        text = "Contact John Doe at john@example.com or 555-123-4567"
        results = detect_pii(text)
        
        assert 'EMAIL' in results
        assert 'PHONE' in results
        assert len(results['EMAIL']) == 1
        assert len(results['PHONE']) == 1
        
        print("✅ PII detection working")
        return True
    except Exception as e:
        print(f"❌ PII detection failed: {e}")
        return False

def test_secrets_detection():
    """Test secrets detection functionality"""
    try:
        from zero_harm_ai_detectors import detect_secrets
        
        text = "My API key is sk-1234567890abcdef1234567890abcdef"
        results = detect_secrets(text)
        
        assert 'SECRETS' in results
        assert len(results['SECRETS']) == 1
        
        print("✅ Secrets detection working")
        return True
    except Exception as e:
        print(f"❌ Secrets detection failed: {e}")
        return False

def test_harmful_content():
    """Test harmful content detection (may be slow due to model loading)"""
    try:
        from zero_harm_ai_detectors import HarmfulTextDetector
        
        detector = HarmfulTextDetector()
        result = detector.detect("Hello, how are you?")
        
        assert 'harmful' in result
        assert 'severity' in result
        assert 'scores' in result
        
        print("✅ Harmful content detection working")
        return True
    except Exception as e:
        print(f"❌ Harmful content detection failed: {e}")
        return False

def test_proxy_integration():
    """Test the proxy.py integration"""
    try:
        from proxy import process_prompt
        
        text = "Email me at test@example.com with secret sk-abc123"
        redacted, detected = process_prompt(text)
        
        assert '[REDACTED_EMAIL]' in redacted
        assert '[REDACTED_SECRET]' in redacted
        assert len(detected) > 0
        
        print("✅ Proxy integration working")
        return True
    except Exception as e:
        print(f"❌ Proxy integration failed: {e}")
        return False

def main():
    print("🧪 Testing zero-harm-detectors workflow...")
    print("=" * 50)
    
    tests = [
        test_library_import,
        test_pii_detection,
        test_secrets_detection,
        test_proxy_integration,
        # test_harmful_content,  # Uncomment if you want to test (slow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Workflow is working correctly.")
    else:
        print("🚨 Some tests failed. Check your setup.")

if __name__ == "__main__":
    main()