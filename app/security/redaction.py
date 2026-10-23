"""Secret and credential redaction utility."""
import re
from typing import Any, Dict, List, Union

# Common credential patterns
PATTERNS = [
    # API Keys & Secrets
    (re.compile(r'(celesto[-_]?(key[-_]?)?[a-zA-Z0-9]{16,})', re.IGNORECASE), '[REDACTED_CELESTO_KEY]'),
    (re.compile(r'(cel_[a-zA-Z0-9_\-]{20,})', re.IGNORECASE), '[REDACTED_CELESTO_KEY]'),
    (re.compile(r'(sk-[a-zA-Z0-9]{20,})', re.IGNORECASE), '[REDACTED_API_KEY]'),
    (re.compile(r'(bearer\s+)[a-zA-Z0-9\._\-]{16,}', re.IGNORECASE), r'\1[REDACTED_BEARER_TOKEN]'),
    (re.compile(r'(password|passwd|secret|token|api_key|apikey)(["\']?\s*[:=]\s*["\']?)([^"\'\s&]+)', re.IGNORECASE), r'\1\2[REDACTED]'),
    # Private keys
    (re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----.*?-----END [A-Z ]+ PRIVATE KEY-----', re.DOTALL), '[REDACTED_PRIVATE_KEY]'),
]


def redact_text(text: str) -> str:
    """Redact sensitive patterns from a string."""
    if not isinstance(text, str):
        return text
    result = text
    for pattern, replacement in PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_data(data: Union[Dict, List, str, Any]) -> Any:
    """Recursively redact dictionaries, lists, or strings."""
    if isinstance(data, str):
        return redact_text(data)
    elif isinstance(data, dict):
        return {k: redact_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_data(item) for item in data]
    return data
