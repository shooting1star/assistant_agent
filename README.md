# assistant_agent

로컬 Ollama를 사용하는 Python용 VS Code AI 코딩 어시스턴트 MVP입니다.
저장 및 진단 오류를 자동 감지하고 `.codemate`에 기록하며, Ollama의 오류 수정과 코드 최적화 제안을 사용자 승인 흐름과 연결합니다.

## 핵심 기능

- VS Code 저장 및 진단 이벤트 자동 전송
- 같은 진단의 반복 전송과 중복 승인창 방지
- API key, token, password, secret 등 민감정보 마스킹
- 오류 원인과 해결 방법을 `.codemate/errors/`에 기록
- Ollama 기반 코드 최적화 제안과 간단한 AST 정적 분석
- 최적화 결과를 `.codemate/optimizations/`에 기록
- 승인된 변경만 문법 검증 후 적용
- 적용 후 Python 파일 재실행 및 런타임 오류 기록
- Ollama 미실행 시 fallback 응답

## 구조

```text
VS Code Extension -> FastAPI Agent :8000
                           |
                           +-- PrivacyFilter
                           +-- ErrorAnalyzer
                           +-- OptimizationEngine -> Ollama :11434
                           +-- RecordManager -> .codemate/
                           +-- ChangeManager -> 승인 + 문법 검증
                           +-- /run-file -> 적용 후 실행 검증
```

## 요구사항

- Python 3.12 이상
- VS Code 1.90 이상
- 선택 사항: [Ollama](https://ollama.com)

## 설치 및 실행

```bash
cd /workspaces/assistant_agent
python -m pip install -r requirements.txt
python -m uvicorn agent.server:app --host 127.0.0.1 --port 8000
```

다른 터미널에서 서버를 확인합니다.

```bash
curl http://127.0.0.1:8000/health
```

## Ollama 설치 및 설정

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama3.2
curl http://127.0.0.1:11434/api/tags
```

기본 모델과 주소는 다음과 같습니다.

```text
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

다른 모델을 사용하려면 Agent 서버를 실행하기 전에 설정합니다.

```bash
export OLLAMA_MODEL=codellama
export OLLAMA_BASE_URL=http://127.0.0.1:11434
python -m uvicorn agent.server:app --host 127.0.0.1 --port 8000
```

현재 개발 컨테이너에서 Ollama가 실행 중인지 확인하려면 다음을 사용합니다.

```bash
command -v ollama
curl --max-time 3 http://127.0.0.1:11434/api/tags
```

Ollama가 없거나 연결에 실패하면 `Ollama unavailable` fallback 응답을 반환합니다. 실제 AI 추천에는 Ollama 서버와 모델이 모두 필요합니다.

## 코드 최적화

`/optimize`는 코드를 Ollama에 보내 성능, 시간/공간 복잡도, 반복 작업, 가독성 개선을 요청하고 추천을 기록합니다. 파일은 자동으로 수정하지 않습니다.

```bash
curl -X POST http://127.0.0.1:8000/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/tmp/example.py",
    "code": "result = []\nfor i in range(1000):\n    result.append(i * 2)\n"
  }'
```

Ollama가 실패해도 AST 기반 분석으로 리스트 `append` 패턴과 중첩 반복문을 점검합니다.

관련 코드:

- [agent/optimization_engine.py](agent/optimization_engine.py): Ollama 프롬프트, 정적 분석, 기록
- [agent/ollama_client.py](agent/ollama_client.py): Ollama `/api/generate` 호출
- [agent/server.py](agent/server.py): `/optimize` API

## 오류 감지와 승인 흐름

```text
파일 저장 또는 진단 변경
        |
        v
500ms debounce + 같은 오류 중복 제거
        |
        v
/events -> /suggest-fix -> VS Code 승인 대화상자
                                      |
                         +------------+------------+
                         |                         |
                       무시                 승인하고 적용
                         |                         |
                    파일 변경 없음       /apply-change
                                                   |
                                          문법 검증 + 적용
                                                   |
                                             /run-file 실행
                                                   |
                                    실패 시 runtime_error 기록
```

확장 코드는 [extension/src/extension.js](extension/src/extension.js)입니다.

## API 예시

오류 기록:

```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -d '{"eventType":"error","filePath":"/tmp/example.py","message":"NameError: name x is not defined","stackTrace":"Traceback ..."}'
```

승인된 변경만 적용됩니다.

```bash
curl -X POST http://127.0.0.1:8000/apply-change \
  -H "Content-Type: application/json" \
  -d '{"file_path":"/tmp/example.py","new_content":"x = 1\nprint(x)\n","approved":true}'
```

파일 실행 결과 확인:

```bash
curl -X POST http://127.0.0.1:8000/run-file \
  -H "Content-Type: application/json" \
  -d '{"file_path":"/tmp/example.py","timeout":10}'
```

`/run-file`은 최대 30초까지 실행하며 `passed`, `failed`, `error` 상태와 표준 출력/오류를 반환합니다.

## VS Code 확장 실행

1. VS Code에서 `/workspaces/assistant_agent/extension` 폴더를 엽니다.
2. 확장 개발 환경에서 F5를 실행합니다.
3. Extension Development Host에서 Python 파일을 엽니다.
4. Agent 서버를 실행한 상태로 파일을 저장하거나 오류를 만듭니다.
5. 진단 오류가 감지되면 `승인하고 적용` 또는 `무시`를 선택합니다.

## 기록 구조

```text
.codemate/
├── errors/          # ERR-XXXX.md
├── issues/          # ISSUE-XXXX.md
└── optimizations/   # OPT-XXXX.md
```

## 테스트

```bash
cd /workspaces/assistant_agent
pytest -q
```

테스트는 이벤트 파이프라인, 개인정보 마스킹, 오류 기록, Ollama 호출, 최적화 기록, 승인, 파일 실행 성공/실패를 검증합니다. Ollama가 없어도 fallback 테스트는 실행됩니다.

## 주요 파일

- [agent/server.py](agent/server.py): FastAPI API
- [agent/optimization_engine.py](agent/optimization_engine.py): 최적화 엔진
- [agent/ollama_client.py](agent/ollama_client.py): Ollama 클라이언트
- [agent/error_analyzer.py](agent/error_analyzer.py): 오류 요약
- [agent/record_manager.py](agent/record_manager.py): Markdown 기록 저장
- [agent/change_manager.py](agent/change_manager.py): 승인, 문법 검증, 롤백
- [extension/src/extension.js](extension/src/extension.js): 자동 감지와 승인 UI
- [tests/](tests): 회귀 테스트

## 제한사항

- VS Code 확장은 현재 개발용 Extension Host에서 실행합니다.
- Ollama가 없으면 실제 LLM 분석 대신 fallback 또는 정적 분석을 사용합니다.
- 최적화 추천은 자동 적용하지 않으며, 파일 수정은 승인과 검증을 거쳐야 합니다.
- `/run-file`은 로컬 MVP용입니다. 운영 환경에서는 실행 대상과 권한을 제한해야 합니다.
