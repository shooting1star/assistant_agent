class ErrorAnalyzer:
    @staticmethod
    def summarize(error_message: str, context: str = "") -> dict:
        message = (error_message or "Unknown error").strip()
        lower_message = message.lower()

        if "nameerror" in lower_message:
            cause = "A variable or symbol is being referenced before it is defined or imported."
            solution = "Check the variable scope and ensure the symbol is initialized before use."
        elif "importerror" in lower_message or "modulenotfounderror" in lower_message:
            cause = "A required module or package cannot be resolved in the current runtime environment."
            solution = "Verify the module name, installation state, and the active Python environment."
        elif "syntaxerror" in lower_message:
            cause = "The code structure is invalid and cannot be parsed by Python."
            solution = "Review the offending line and fix the syntax issue before rerunning."
        else:
            cause = "Investigate the failing code path and the most recent changes in the active file."
            solution = "Review the stack trace, isolate the root cause, and validate the fix with a focused rerun."

        return {
            "problem": message,
            "cause": cause,
            "expected_result": "The code should execute without an error.",
            "solution": solution,
            "context": context,
            "status": "OPEN",
        }
