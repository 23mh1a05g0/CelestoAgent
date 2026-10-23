"""Command policy engine for sandbox safety validation."""
import re
import shlex
from typing import Tuple, List, Optional
from pydantic import BaseModel
from app.config import settings


class PolicyDecision(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL


class CommandPolicy:
    """Evaluates commands for security risks and containment violations."""

    CRITICAL_DENY_PATTERNS = [
        (re.compile(r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|--recursive\s+--force)\s+/\s*$', re.IGNORECASE), "Destructive root filesystem deletion"),
        (re.compile(r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|--recursive\s+--force)\s+/\*$', re.IGNORECASE), "Destructive root wildcard deletion"),
        (re.compile(r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', re.IGNORECASE), "Fork bomb attack"),
        (re.compile(r'mkfs\.[a-z0-9]+', re.IGNORECASE), "Filesystem format operation"),
        (re.compile(r'dd\s+if=.*?of=/dev/[shv]d[a-z]', re.IGNORECASE), "Direct block device overwrite"),
        (re.compile(r'>\s*/dev/[shv]d[a-z]', re.IGNORECASE), "Device clobbering redirection"),
    ]

    HIGH_RISK_PATTERNS = [
        (re.compile(r'curl.*(\bpastebin\b|\bngrok\b|\bwebhook\.site\b|\bburpcollaborator\b|/exfil)', re.IGNORECASE), "Potential data exfiltration endpoint"),
        (re.compile(r'wget.*(\bpastebin\b|\bngrok\b|\bwebhook\.site\b|/exfil)', re.IGNORECASE), "Potential data exfiltration endpoint"),
        (re.compile(r'nc(\.traditional)?\s+-[lpe]', re.IGNORECASE), "Reverse shell listener"),
        (re.compile(r'/dev/tcp/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', re.IGNORECASE), "Bash reverse socket"),
    ]

    def __init__(self, allowed_prefixes: Optional[List[str]] = None):
        if allowed_prefixes is None:
            raw = settings.ALLOWED_COMMAND_PREFIXES
            self.allowed_prefixes = [p.strip() for p in raw.split(",") if p.strip()]
        else:
            self.allowed_prefixes = allowed_prefixes

    def evaluate(self, command: str) -> PolicyDecision:
        """Validate command against security policies."""
        cleaned = command.strip()
        if not cleaned:
            return PolicyDecision(allowed=False, reason="Empty command", risk_level="LOW")

        # 1. Critical pattern checks
        for pattern, reason in self.CRITICAL_DENY_PATTERNS:
            if pattern.search(cleaned):
                return PolicyDecision(allowed=False, reason=f"Blocked: {reason}", risk_level="CRITICAL")

        # 2. High risk checks
        for pattern, reason in self.HIGH_RISK_PATTERNS:
            if pattern.search(cleaned):
                return PolicyDecision(allowed=False, reason=f"Blocked: {reason}", risk_level="HIGH")

        # 3. Check configurable blocked patterns
        if settings.BLOCKED_COMMAND_PATTERNS:
            custom_regex = re.compile(settings.BLOCKED_COMMAND_PATTERNS, re.IGNORECASE)
            if custom_regex.search(cleaned):
                return PolicyDecision(allowed=False, reason="Blocked by custom security policy pattern", risk_level="HIGH")

        # Passed all security filters
        return PolicyDecision(allowed=True, reason="Command cleared security policy", risk_level="LOW")
