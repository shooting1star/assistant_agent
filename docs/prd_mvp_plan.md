# PRD 기반 MVP 구현 계획

## 1단계: 프로젝트 구조 및 범위 정의
- 폴더 구조 생성
- 기능 경계 정의
- In-scope / Out-of-scope 명시

## 2단계: VS Code Extension 기본 구조
- 이벤트 수집 로직 설계
- 저장/실행 이벤트 감지
- 로컬 Agent로 통신

## 3단계: Python Agent 서버 구현
- FastAPI 기반 HTTP Web API
- 이벤트 수신 엔드포인트 작성
- 기본 health check

## 4단계: Context Collector 및 Privacy Filter
- 활성 파일 컨텍스트 수집
- 최소 컨텍스트 추출
- 민감 문자열 마스킹

## 5단계: Error Analyzer 구현
- 컴파일/런타임 에러 구조화
- 문제/원인/해결책 형식 정의
- 자동 수정 금지 정책 반영

## 6단계: Ollama 연동
- 로컬 모델 호출 인터페이스
- prompt template 정의
- fallback 설계

## 7단계: Decision Engine
- 침묵 → 관찰 → 개입 후보 → 개입
- 반복 오류 누적 로직
- Quiet Mode 처리

## 8단계: Optimization Engine
- 시간/공간 복잡도 분석
- 코드 구조 개선 제안
- 사용자 승인 기반 수정 제안

## 9단계: .codemate 기록 시스템
- errors/, issues/, optimizations/ 구조
- ERR-XXXX.md, ISSUE-XXXX.md, OPT-XXXX.md 규칙
- 반복 오류 재사용 정책

## 10단계: 통합 검증 및 데모
- 통합 테스트 작성
- 전체 워크플로우 검증
- README 사용법 정리
