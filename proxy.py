"""
Updated proxy.py to use the new AI-based detection pipeline
"""
from zero_harm_ai_detectors import ZeroHarmPipeline, PipelineConfig, RedactionStrategy, AI_DETECTION_AVAILABLE

# ==================== Pipeline Configuration ====================
# Initialize the pipeline once (reused for all requests)
PIPELINE = None
HARMFUL_DETECTOR = None
USE_AI_DETECTION = AI_DETECTION_AVAILABLE  # Automatically use AI if available

def get_or_create_pipeline():
    """Get or create the detection pipeline (lazy loading)"""
    global PIPELINE
    if PIPELINE is None:
        if USE_AI_DETECTION:
            print("Initializing AI-powered detection pipeline...")
            config = PipelineConfig(
                # PII detection settings
                pii_threshold=0.7,  # Confidence threshold for AI detections
                pii_aggregation_strategy="simple",
                
                # Harmful content settings
                harmful_threshold_per_label=0.5,
                harmful_overall_threshold=0.5,
                
                # Performance settings
                device="cpu"  # Change to "cuda" if you have GPU
            )
            PIPELINE = ZeroHarmPipeline(config)
            print("✅ AI pipeline ready!")
        else:
            print("⚠️ AI detection not available, falling back to regex")
            # Fallback will be handled by the detection functions
    return PIPELINE

def get_or_create_harmful_detector():
    """Get or create the harmful detector (lazy loading)"""
    global HARMFUL_DETECTOR
    if HARMFUL_DETECTOR is None:
        try:
            from zero_harm_ai_detectors.harmful_detectors import HarmfulTextDetector, DetectionConfig
            print("Initializing legacy harmful content detector...")
            config = DetectionConfig(
                threshold_per_label=0.5,
                overall_threshold=0.5
            )
            HARMFUL_DETECTOR = HarmfulTextDetector(config)
            print("✅ Legacy harmful detector ready!")
        except ImportError:
            print("⚠️ Harmful content detection unavailable (transformers not installed)")
            HARMFUL_DETECTOR = False  # Mark as unavailable
        except Exception as e:
            print(f"⚠️ Error initializing harmful detector: {e}")
            HARMFUL_DETECTOR = False
    return HARMFUL_DETECTOR

def detect_harmful_legacy(text: str) -> dict:
    """
    Detect harmful content using the legacy HarmfulTextDetector
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dictionary in the format expected by process_prompt:
        {
            "HARMFUL_CONTENT": [{
                "span": text,
                "start": 0,
                "end": len(text),
                "severity": "low" | "medium" | "high",
                "labels": list of detected labels,
                "scores": dict of label scores
            }]
        }
        Returns empty dict if not harmful or detector unavailable
    """
    detector = get_or_create_harmful_detector()
    
    # If detector is False, it means initialization failed
    if detector is False:
        return {}
    
    try:
        # Run detection
        result = detector.detect(text)
        
        # FIX: The result is ALREADY in the correct format!
        # detector.detect() returns either:
        # - {} (empty dict) if not harmful
        # - {"HARMFUL_CONTENT": [{...}]} if harmful
        
        # Just return it directly
        return result
            
    except Exception as e:
        print(f"⚠️ Error in harmful content detection: {e}")
        import traceback
        traceback.print_exc()
        return {}
    
# ==================== Main Processing Functions ====================

def process_prompt(prompt: str) -> tuple:
    """
    Main function used by app.py - detects and redacts sensitive content
    
    Args:
        prompt: User input text
        
    Returns:
        (redacted_text, detections_dict)
        
    Example:
        redacted, detected = process_prompt("Email me at test@example.com")
        # redacted = "Email me at [REDACTED_EMAIL]"
        # detected = {"EMAIL": [{"span": "test@example.com", ...}]}
    """
    if USE_AI_DETECTION:
        return process_prompt_ai(prompt)
    else:
        return process_prompt_legacy(prompt)


def process_prompt_ai(prompt: str) -> tuple:
    """
    Process prompt using AI-based detection pipeline
    
    This provides:
    - More accurate PII detection using transformer models
    - Better person name detection
    - Contextual understanding of entities
    - Harmful content detection
    """
    pipeline = get_or_create_pipeline()
    
    # Run full detection pipeline
    result = pipeline.detect(
        prompt,
        redaction_strategy=RedactionStrategy.TOKEN,
        detect_pii=True,
        detect_secrets=True,
        detect_harmful=True  # Also check for harmful content
    )
    
    # Convert to backend format
    detected = {}
    
    # Group detections by type
    for detection in result.detections:
        det_type = detection.type
        
        # Skip harmful content from regular detections (handle separately)
        if det_type == "HARMFUL_CONTENT":
            continue
        
        if det_type not in detected:
            detected[det_type] = []
        
        detected[det_type].append({
            "span": detection.text,
            "start": detection.start,
            "end": detection.end,
            "confidence": detection.confidence,
            "metadata": detection.metadata
        })
    
    # Add harmful content info if detected
    if result.harmful:
        detected["HARMFUL_CONTENT"] = [{
            "span": prompt,
            "start": 0,
            "end": len(prompt),
            "severity": result.severity,
            "labels": list(result.harmful_scores.keys()),
            "scores": result.harmful_scores
        }]
    
    # Use custom redaction for backend
    if result.harmful:
        # If harmful content detected, redact entire text
        redacted = f"[⚠️ HARMFUL CONTENT BLOCKED - {result.severity.upper()} SEVERITY]"
    elif detected:
        redacted = custom_redact_text(prompt, detected)
    else:
        redacted = result.redacted_text
    
    return redacted, detected

def process_prompt_legacy(prompt: str) -> tuple:
    """
    Fallback to legacy regex-based detection
    (Used when AI models are not available)
    """
    from zero_harm_ai_detectors import detect_pii, detect_secrets
    
    detected = {}
    
    # Detect PII
    pii = detect_pii(prompt, use_ai=False)
    if pii:
        detected.update(pii)
    
    # Detect secrets
    secrets = detect_secrets(prompt, use_ai=False)
    if secrets:
        detected.update(secrets)
    
    # Detect harmful content using legacy detector
    harmful_result = detect_harmful_legacy(prompt)
    if harmful_result:
        detected.update(harmful_result)
    
    # Redact using custom tokens
    if detected:
        # Check if harmful content was detected for full redaction
        if "HARMFUL_CONTENT" in detected:
            harmful_info = detected["HARMFUL_CONTENT"][0]
            redacted = f"[⚠️ HARMFUL CONTENT BLOCKED - {harmful_info['severity'].upper()} SEVERITY]"
        else:
            redacted = custom_redact_text(prompt, detected)
    else:
        redacted = prompt
    
    return redacted, detected

# ==================== Custom Redaction ====================

def custom_redact_text(text: str, findings: dict) -> str:
    """
    Custom redaction with backend-specific tokens
    
    This maintains the exact token format expected by the frontend/API
    """
    REDACT_MAP = {
        # PII types
        "EMAIL": "[REDACTED_EMAIL]",
        "PHONE": "[REDACTED_PHONE]",
        "SSN": "[REDACTED_SSN]",
        "CREDIT_CARD": "[REDACTED_CREDIT_CARD]",
        "BANK_ACCOUNT": "[REDACTED_BANK_ACCOUNT]",
        "DOB": "[REDACTED_DOB]",
        "DRIVERS_LICENSE": "[REDACTED_DRIVERS_LICENSE]",
        "MEDICAL_RECORD_NUMBER": "[REDACTED_MRN]",
        "ADDRESS": "[REDACTED_ADDRESS]",
        
        # Person and location (AI detections)
        "PERSON": "[REDACTED_NAME]",
        "PERSON_NAME": "[REDACTED_NAME]",
        "LOCATION": "[REDACTED_LOCATION]",
        "ORGANIZATION": "[REDACTED_ORG]",
        "DATE": "[REDACTED_DATE]",
        
        # Secrets
        "SECRETS": "[REDACTED_SECRET]",
        "API_KEY": "[REDACTED_SECRET]",
        "TOKEN": "[REDACTED_SECRET]",
        "PASSWORD": "[REDACTED_SECRET]",
        
        # Harmful content
        "HARMFUL_CONTENT": "[REDACTED_HARMFUL_CONTENT]",
        "TOXIC": "[REDACTED_HARMFUL_CONTENT]",
        "THREAT": "[REDACTED_HARMFUL_CONTENT]",
        "INSULT": "[REDACTED_HARMFUL_CONTENT]",
    }
    
    spans = []
    for kind, items in findings.items():
        for item in items:
            start = item.get('start')
            end = item.get('end')
            if start is not None and end is not None:
                token = REDACT_MAP.get(kind, f"[REDACTED_{kind}]")
                spans.append((start, end, token))
    
    # Sort by start position in reverse order to avoid index shifting
    spans.sort(key=lambda s: s[0], reverse=True)
    
    result = text
    for start, end, token in spans:
        result = result[:start] + token + result[end:]
    
    return result


# ==================== Advanced Features ====================

def analyze_text_detailed(text: str) -> dict:
    """
    Provide detailed analysis of text including confidence scores
    
    Returns:
        {
            "original": original text,
            "redacted": redacted text,
            "detections": list of all detections with confidence,
            "harmful_analysis": detailed harmful content scores,
            "risk_score": overall risk score (0-1),
            "recommendations": list of recommended actions
        }
    """
    pipeline = get_or_create_pipeline()
    
    result = pipeline.detect(
        text,
        redaction_strategy=RedactionStrategy.TOKEN,
        detect_pii=True,
        detect_secrets=True,
        detect_harmful=True
    )
    
    # Calculate overall risk score
    risk_factors = []
    
    # PII risk
    pii_count = len([d for d in result.detections if d.type != "HARMFUL_CONTENT"])
    if pii_count > 0:
        risk_factors.append(min(pii_count * 0.2, 0.5))
    
    # Secrets risk (high priority)
    secret_count = len([d for d in result.detections if d.type in ["API_KEY", "TOKEN", "PASSWORD", "SECRETS"]])
    if secret_count > 0:
        risk_factors.append(0.8)
    
    # Harmful content risk
    if result.harmful:
        severity_scores = {"low": 0.3, "medium": 0.6, "high": 0.9}
        risk_factors.append(severity_scores.get(result.severity, 0.5))
    
    risk_score = max(risk_factors) if risk_factors else 0.0
    
    # Generate recommendations
    recommendations = []
    if pii_count > 0:
        recommendations.append(f"Found {pii_count} PII instance(s) - consider data minimization")
    if secret_count > 0:
        recommendations.append("CRITICAL: API keys/secrets detected - rotate credentials immediately")
    if result.harmful:
        recommendations.append(f"Harmful content detected ({result.severity} severity) - review content policy")
    
    return {
        "original": text,
        "redacted": result.redacted_text,
        "detections": [
            {
                "type": d.type,
                "text": d.text,
                "start": d.start,
                "end": d.end,
                "confidence": d.confidence,
                "metadata": d.metadata
            }
            for d in result.detections
        ],
        "harmful_analysis": {
            "is_harmful": result.harmful,
            "severity": result.severity,
            "scores": result.harmful_scores
        } if result.harmful_scores else None,
        "risk_score": risk_score,
        "recommendations": recommendations
    }


def batch_process(texts: list) -> list:
    """
    Process multiple texts efficiently
    
    Args:
        texts: List of text strings
        
    Returns:
        List of (redacted_text, detections) tuples
    """
    pipeline = get_or_create_pipeline()
    
    results = []
    for text in texts:
        result = pipeline.detect(text)
        
        # Convert to format expected by app
        detected = {}
        for detection in result.detections:
            if detection.type not in detected:
                detected[detection.type] = []
            detected[detection.type].append({
                "span": detection.text,
                "start": detection.start,
                "end": detection.end
            })
        
        redacted = custom_redact_text(text, detected) if detected else text
        results.append((redacted, detected))
    
    return results


# ==================== Testing & Debug ====================

def test_pipeline():
    """Test the detection pipeline with various inputs"""
    test_cases = [
        "Contact John Smith at john.smith@email.com",
        "My phone is 555-123-4567 and SSN is 123-45-6789",
        "API key: sk-1234567890abcdef1234567890abcdef",
        "I hate you and want to hurt you",
        "Credit card: 4532-0151-1283-0366",
        "Meet me at 123 Main Street, New York, NY 10001"
    ]
    
    print("Testing Zero Harm AI Pipeline")
    print("=" * 60)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Original: {text}")
        
        redacted, detected = process_prompt(text)
        print(f"Redacted: {redacted}")
        print(f"Found: {', '.join(detected.keys()) if detected else 'Nothing'}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed")


if __name__ == "__main__":
    # Run tests when executed directly
    test_pipeline()
    
    # Example of detailed analysis
    print("\n\nDetailed Analysis Example:")
    print("=" * 60)
    result = analyze_text_detailed(
        "Contact me at admin@company.com with API key sk-abc123. I'll hurt anyone who tries to stop me!"
    )
    print(f"Risk Score: {result['risk_score']:.2f}")
    print(f"Recommendations:")
    for rec in result['recommendations']:
        print(f"  - {rec}")
