class ErrorAnalyzer:
    @staticmethod
    def summarize(error_message: str, context: str = "") -> dict:
        message = (error_message or "알 수 없는 오류").strip()
        lower_message = message.lower()

        if "nameerror" in lower_message:
            cause = "정의되거나 import되지 않은 변수 또는 기호를 사용하고 있습니다."
            solution = "변수의 범위를 확인하고 사용 전에 값을 초기화하거나 필요한 모듈을 import하세요."
        elif "importerror" in lower_message or "modulenotfounderror" in lower_message:
            cause = "현재 실행 환경에서 필요한 모듈 또는 패키지를 찾을 수 없습니다."
            solution = "모듈 이름, 설치 상태, 현재 선택된 Python 환경을 확인하세요."
        elif "syntaxerror" in lower_message:
            cause = "코드 구조가 올바르지 않아 Python이 해석할 수 없습니다."
            solution = "오류가 발생한 줄의 괄호, 콜론, 들여쓰기와 문법을 확인한 뒤 다시 실행하세요."
        else:
            cause = "현재 파일에서 오류가 발생한 코드 경로를 확인해야 합니다."
            solution = "스택 트레이스를 확인해 근본 원인을 찾고 수정 후 해당 파일을 다시 실행하세요."

        return {
            "problem": message,
            "cause": cause,
            "expected_result": "오류 없이 코드가 실행되어야 합니다.",
            "solution": solution,
            "context": context,
            "status": "열림",
        }
