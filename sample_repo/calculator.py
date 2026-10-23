"""Simple calculator module with a deliberate bug for autonomous agent evaluation."""

def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b

def multiply(a: float, b: float) -> float:
    return a * b

def divide(a: float, b: float) -> float:
    # Deliberate bug for the agent to find and fix:
    # Intentionally returns a + b instead of a / b
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a + b  # BUG: should be a / b
