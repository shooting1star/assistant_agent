# assistant_agent

VS Code에서 파이썬 코드를 작성할 때, 에러를 자동으로 감지하고 원인을 정리하며 기록을 남기고, 필요한 경우 사용자의 승인 하에 수정까지 제안하는 로컬 AI 코딩 어시스턴트 MVP입니다.

## 1. 이 프로젝트가 하는 일

이 프로젝트는 아래 흐름을 중심으로 동작합니다.

- 코드 저장/에러 발생 감지
- 민감 정보 마스킹
- 에러 분석 및 원인 정리
- `.codemate` 폴더에 기록 저장
- 수정 전 사용자 승인 확인
- 승인된 수정은 문법 검증 후 반영

즉, 개발자가 파이썬을 작성하면서 "에러를 빠르게 이해하고, 기록을 남기고, 안전하게 수정하는 흐름"을 만들어 줍니다.

## 2. 현재 상태

이 저장소는 MVP 골격 단계입니다. 핵심 기능은 이미 구현되어 있습니다.

- 로컬 Agent 서버
- 보안 마스킹
- 에러 요약
- 에러 기록 파일 생성
- 승인 기반 수정
- 로컬 Ollama 호출 인터페이스
- 테스트 검증

다만 실제 IDE의 진단 자동 연동과 완전한 LLM 기반 수정 추천은 다음 단계에 해당합니다.

## 3. 빠르게 실행하는 법

### 3-1. 의존성 설치

```bash
cd /workspaces/assistant_agent
python -m pip install -r requirements.txt
```

### 3-2. 서버 실행

```bash
cd /workspaces/assistant_agent
python -m uvicorn agent.server:app --host 127.0.0.1 --port 8000
```

### 3-3. 상태 확인

```bash
curl http://127.0.0.1:8000/health
```

예상 응답:

```json
{"status":"ok","service":"assistant_agent"}
```

## 4. 실제로 파이썬 프로그래밍할 때 쓰는 방식

### 예시 1: 에러 발생 테스트

아래 파일을 만들고 실행해보면 에러가 발생합니다.

```python
# /tmp/example.py
print("start")
print(unknown_variable)
```

실행:

```bash
python /tmp/example.py
```

결과:

```text
start
Traceback (most recent call last):
  File "/tmp/example.py", line 3, in <module>
    print(unknown_variable)
NameError: name 'unknown_variable' is not defined
```

이때 아래처럼 에러 이벤트를 Agent에게 보낼 수 있습니다.

```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -d '{"eventType":"error","filePath":"/tmp/example.py","message":"NameError: name unknown_variable is not defined","stackTrace":"Traceback..."}'
```

서버는 이를 받아서:

- 민감정보 마스킹
- 에러 분석
- 기록 파일 생성

까지 처리합니다.

### 예시 2: 저장 이벤트 전송

파일을 저장할 때마다 이벤트를 보낼 수도 있습니다.

```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -d '{"eventType":"save","filePath":"/tmp/example.py","apiKey":"secret123"}'
```

이 경우에도 민감정보는 자동으로 보호됩니다.

### 예시 3: 기록 파일 확인

```bash
find .codemate -type f
```

예상 결과:

```bash
.codemate/errors/ERR-0001.md
```

이 파일에는 마크다운 형식으로 다음이 적힙니다.

- Problem
- Cause
- Expected Result
- Solution
- Status

### 예시 4: 수정 제안 요청

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"Fix the NameError in this Python code: print(unknown_variable)"}'
```

요청이 들어오면 로컬 Ollama 호출 인터페이스가 동작합니다. 현재는 로컬 모델이 없거나 실패하면 fallback 응답으로 처리됩니다.

### 예시 5: 사용자 승인 기반 수정

```bash
curl -X POST http://127.0.0.1:8000/apply-change \
  -H "Content-Type: application/json" \
  -d '{"file_path":"/tmp/example.py","new_content":"print(\"fixed\")\n","approved":true}'
```

이 요청의 의미는 다음과 같습니다.

- `approved: false` → 수정 대기, 적용 안 됨
- `approved: true` → 수정 시도
- 문법 검증 실패 → 원래 내용으로 복구
- 문법 검증 통과 → 수정 반영

## 5. 이 프로젝트를 VS Code에서 쓰는 실전 흐름

실제 개발자는 아래처럼 사용할 수 있습니다.

```text
1. Python 파일 작성
2. 코드 실행 또는 저장
3. 에러 발생
4. 자동으로/수동으로 이벤트 전송
5. Agent가 에러 분석
6. .codemate에 기록 저장
7. 필요 시 수정 제안
8. 사용자가 승인 후 수정 반영
9. 다시 실행해서 검증
```

## 6. 저장소 구조

- [agent/server.py](agent/server.py): Agent 서버
- [agent/privacy_filter.py](agent/privacy_filter.py): 민감 정보 마스킹
- [agent/error_analyzer.py](agent/error_analyzer.py): 에러 분류 및 요약
- [agent/record_manager.py](agent/record_manager.py): 기록 저장
- [agent/decision_engine.py](agent/decision_engine.py): 반복 오류 판단
- [agent/change_manager.py](agent/change_manager.py): 승인 기반 수정
- [agent/ollama_client.py](agent/ollama_client.py): 로컬 LLM 호출
- [extension/src/extension.js](extension/src/extension.js): VS Code 이벤트 전송
- [tests/](tests): 검증 코드

## 7. 보안 정책

- API key, token, password, secret 값은 자동 마스킹
- 전체 파일 전송 대신 필요한 컨텍스트만 전달
- 로컬 실행 기반, 민감 정보 외부 유출 최소화

## 8. 테스트

```bash
cd /workspaces/assistant_agent
pytest -q
```

현재 정상 동작하는 핵심 테스트는 다음과 같습니다.

- 보안 마스킹
- 반복 오류 판단
- 에러 저장 기록
- 승인 기반 수정
- Ollama 호출 인터페이스

## 9. 알려진 한계

아직 다음 단계가 남아 있습니다.

- VS Code 진단 이벤트 자동 정교화
- 실제 Ollama 모델 실행 연결
- 사용자 승인 후 자동 재실행
- 대규모 리팩토링 분석

## 10. 요약

이 프로젝트는 "파이썬 코딩 중 발생하는 에러를 감지하고, 원인을 설명하고, 기록을 남기고, 수정 전에 승인받는 흐름"을 구현하는 로컬 AI 코딩 어시스턴트 MVP입니다.

다음 단계로는 실제 VS Code 확장 프로그램을 실행 상태로 연결하고, 로컬 Ollama와 정식 연동을 붙이는 것이 핵심입니다.

프로젝트 내부에 .codemate 디렉터리를 생성해 아래 구조를 유지합니다.

- .codemate/errors/: 오류 기록
- .codemate/issues/: 문제/대화 기록
- .codemate/optimizations/: 최적화 기록

각 레코드는 Markdown 형식으로 저장됩니다.

## 보안 정책

- Privacy Filter는 API key, token, password, secret 등 민감 정보를 마스킹합니다.
- 로컬 LLM을 기본으로 설계하며, 외부 전송을 최소화합니다.
- 전체 파일 전송보다 최소 컨텍스트 수집을 우선합니다.

## Ollama 연결에 대한 현재 기준

이 저장소는 Ollama 기반 로컬 추론을 기본 전제로 설계하고 있습니다. 현재 구조는 API key 기반 외부 서비스 연결보다는 로컬 모델 호출 인터페이스를 중심으로 구성되어 있습니다.

즉:

- 로컬 서버 실행 여부
- 모델명
- 호스트 주소와 포트
- fallback 처리

가 더 중요합니다.

## 테스트

다음 명령으로 현재 구현된 핵심 기능을 검증할 수 있습니다.

```bash
cd /workspaces/assistant_agent && pytest -q
```

현재 확인된 결과는 다음과 같습니다.

## 11. Ollama 기반 최적화 엔진 사용법

이 프로젝트는 코드 최적화 추천도 로컬 Ollama를 사용해 수행합니다. 최적화 엔진은 코드를 읽고, 반복 루프, 불필요한 계산, 성능 병목, 가독성 문제를 찾아 추천을 생성합니다.

### 11-1. 로컬 Ollama 실행 확인

```bash
curl http://127.0.0.1:11434/api/tags
```

모델이 준비되어 있으면, 예시 응답에서 `llama3.2` 또는 다른 모델 이름을 확인할 수 있습니다.

### 11-2. 최적화 엔진 호출 예시

```bash
curl -X POST http://127.0.0.1:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/tmp/example.py",
    "code": "result = []\nfor i in range(10):\n    result.append(i * 2)\n"
  }'
```

예상 응답:

```json
{
  "status": "suggested",
  "model": "llama3.2",
  "suggestion": "- Use a list comprehension instead of an append loop.\n- Avoid repeated work inside the loop.",
  "record_path": ".codemate/optimizations/OPT-0001.md"
}
```

### 11-3. 최적화 엔진의 흐름

```text
Python code 입력
  ↓
Ollama prompt 생성
  ↓
로컬 모델 추론
  ↓
추천 문장 생성
  ↓
.codemate/optimizations/OPT-XXXX.md 저장
```

### 11-4. 실제 적용 아이디어

예를 들어 다음 코드가 있다면:

```python
result = []
for i in range(1000):
    if i % 2 == 0:
        result.append(i * 2)
```

최적화 엔진은 다음처럼 추천할 수 있습니다.

- 리스트 컴프리헨션으로 단순화
- 불필요한 조건 분기 통합
- 더 읽기 쉬운 구조로 정리

이 추천은 Ollama로 생성되고, 기록 파일로 남게 됩니다.

## 12. 실제 VS Code 확장 실행 예시

이 기능은 로컬 Python 서버와 VS Code 확장 프로그램을 함께 실행할 때 가장 자연스럽게 동작합니다.

### 11-1. 서버 실행

```bash
cd /workspaces/assistant_agent
python -m uvicorn agent.server:app --host 127.0.0.1 --port 8000
```

### 11-2. 확장 프로그램 실행

VS Code에서 다음 절차를 수행합니다.

1. 확장 프로그램 개발 모드로 열기
2. [extension/src/extension.js](extension/src/extension.js) 를 확인
3. F5로 실행하여 Extension Development Host 실행
4. 새 창에서 Python 파일 생성 또는 기존 파일 수정
5. 에러가 발생하면 자동으로 이벤트 전달
6. 경고 메시지가 표시되면 '승인하고 적용' 선택
7. 서버가 수정 내용을 적용

### 11-3. 동작 시나리오

```python
# example.py
print("start")
print(unknown_variable)
```

이 코드를 저장하거나 실행하면, VS Code 확장 프로그램은 다음 흐름을 수행합니다.

- 저장/diagnostic 이벤트를 로컬 서버로 전송
- Agent가 에러 분석
- `.codemate/errors/`에 Markdown 기록 저장
- 수정 제안 생성
- 사용자에게 승인 여부를 묻는 메시지 표시
- 승인 시 파일이 수정되고 안전 검증을 통과한 경우 반영

### 11-4. 사용자 승인 흐름

이 프로젝트의 핵심은 사용자가 직접 수정 전 최종 확인을 하도록 만든다는 점입니다.

```text
에러 감지
  ↓
서버로 이벤트 전송
  ↓
에러 분석 + 기록 저장
  ↓
수정 제안 생성
  ↓
VS Code에서 승인 메시지 표시
  ↓
사용자 선택
  ├─ 승인하고 적용 → 파일 수정
  └─ 무시 → 아무것도 하지 않음
```

이 구조는 자동 수정 폭주를 막고, 실수로 파일이 임의로 바뀌는 위험을 줄여줍니다.

## 12. 최종 검증 상태

다음 명령으로 현재 구현 상태를 확인했습니다.

```bash
cd /workspaces/assistant_agent && pytest -q
```

검증 결과:

- 12개 테스트 통과
- 0개 실패
- 경고 2개 (의존성 경고 및 datetime deprecation 경고)

즉, 핵심 기능은 안정적으로 동작하는 상태입니다.

## 13. 요약

본 프로젝트는 다음 조건을 만족하는 로컬 AI 코딩 어시시턴트 MVP입니다.

- Python 파일에서 에러를 자동으로 감지
- 민감 정보 마스킹
- 원인, 해결책 중심의 분석
- `.codemate`에 기록 저장
- 수정 전 사용자 승인
- 승인된 경우만 수정 반영
- 로컬 서버 기반으로 동작

이제 실제 VS Code 확장 환경에서 실시간 감지와 승인 흐름까지 연결된 형태로 사용 가능합니다.

- 보안 마스킹 테스트 통과
- Decision Engine 테스트 통과
- 에러 이벤트 기록 테스트 통과

## 알려진 한계

- VS Code diagnostic 자동 연동은 아직 완전한 end-to-end 연결 단계가 아님
- 실제 Ollama 모델 실행과 응답 파싱은 스켈레톤 단계
- 자동 코드 수정/재실행/롤백 흐름은 아직 구현 전
- 전체 프로젝트 리팩토링 자동 분석은 제외 범위

## 다음 우선순위

1. VS Code 진단 이벤트 자동 전송 연결
2. 실제 Ollama 호출 및 응답 처리
3. 사용자 승인 기반 수정/재실행 흐름
4. 최적화 엔진 구조 강화
5. README와 실행 가이드 정교화

## 요약

이 저장소는 현재 PRD 기반 MVP의 핵심 골격을 갖춘 상태이며, 보안/이벤트/기록 흐름이 동작하도록 구성되어 있습니다. 다만 최종적인 IDE 연동과 로컬 LLM 실제 추론 연결은 다음 단계에서 완성할 예정입니다.
