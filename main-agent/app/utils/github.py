import hmac
import hashlib
from typing import Optional


def verify_webhook_signature(
    payload: bytes, 
    signature_header: Optional[str], 
    secret: str
) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw webhook payload bytes
        signature_header: X-Hub-Signature-256 header value
        secret: Webhook secret configured in GitHub
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature_header:
        return False
    
    # Extract the signature from the header (format: "sha256=<signature>")
    if not signature_header.startswith("sha256="):
        return False
    
    expected_signature = signature_header[7:]  # Remove "sha256=" prefix
    
    # Calculate HMAC signature
    mac = hmac.new(
        secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    )
    calculated_signature = mac.hexdigest()
    
    # Compare signatures using constant-time comparison
    return hmac.compare_digest(expected_signature, calculated_signature)