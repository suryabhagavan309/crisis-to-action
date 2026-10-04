def calculate(expression):
    """
    Safely evaluate basic mathematical expressions.
    """

    allowed = "0123456789+-*/(). "

    if not all(char in allowed for char in expression):
        raise ValueError("Invalid characters in expression.")

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return result
    except Exception:
        raise ValueError("Could not calculate the expression.")


if __name__ == "__main__":
    print(calculate("40000 - 12000 - 5000"))