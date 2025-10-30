# Testing Guide

이 프로젝트는 pytest를 사용한 포괄적인 단위 테스트 스위트를 포함합니다.

## 테스트 설정

### 의존성 설치

```bash
# pytest 및 필수 플러그인 설치
python3 -m pip install pytest pytest-asyncio pytest-mock

# 프로젝트 의존성 설치
python3 -m pip install -r requirements.txt
# 또는 uv 사용
uv sync
```

## 테스트 실행

### 모든 테스트 실행

```bash
pytest
```

### 특정 테스트 파일 실행

```bash
pytest test_realtime_utils.py
pytest test_mcp_service.py
pytest test_realtime_classes.py
```

### 상세한 출력으로 테스트 실행

```bash
pytest -v
```

### 특정 테스트 클래스 또는 메서드 실행

```bash
# 특정 테스트 클래스 실행
pytest test_realtime_utils.py::TestFloat16BitPCM

# 특정 테스트 메서드 실행
pytest test_realtime_utils.py::TestFloat16BitPCM::test_basic_conversion
```

## 테스트 구조

### test_realtime_utils.py
`realtime.py`의 유틸리티 함수 테스트:
- **TestFloat16BitPCM**: float32를 int16 PCM으로 변환하는 함수 테스트
- **TestBase64ArrayConversion**: base64 인코딩/디코딩 함수 테스트
- **TestMergeInt16Arrays**: int16 배열 병합 함수 테스트

### test_mcp_service.py
MCP (Model Context Protocol) 서비스 컴포넌트 테스트:
- **TestMCPTool**: MCPTool 데이터 클래스 테스트
- **TestMCPServerClient**: MCP 서버 클라이언트 기능 테스트
  - 서버 시작/종료
  - JSON-RPC 요청/응답 처리
  - 도구 관리
- **TestMCPService**: 고수준 MCP 서비스 기능 테스트
  - 초기화 및 구성
  - 도구 응답 처리
  - 에러 핸들링

### test_realtime_classes.py
실시간 API 클래스 테스트:
- **TestRealtimeEventHandler**: 이벤트 핸들러 기능 테스트
  - 이벤트 등록 및 디스패치
  - 비동기 이벤트 대기
- **TestRealtimeConversation**: 대화 관리 테스트
  - 항목 생성, 삭제, 업데이트
  - 텍스트 및 오디오 델타 처리
  - 음성 시작/종료 처리
- **TestRealtimeClient**: 실시간 클라이언트 테스트
  - 세션 구성
  - 도구 추가/제거
  - 시스템 프롬프트 및 토큰 제한 업데이트

## 테스트 커버리지

현재 테스트 스위트는 다음을 포함합니다:
- 70개의 단위 테스트
- 유틸리티 함수, MCP 서비스, 실시간 클래스 커버리지
- 동기 및 비동기 함수 테스트
- 모킹을 통한 외부 의존성 격리

## 모범 사례

1. **격리된 테스트**: 각 테스트는 독립적으로 실행되어야 하며 다른 테스트에 의존하지 않아야 합니다
2. **픽스처 사용**: pytest 픽스처를 사용하여 테스트 데이터 및 인스턴스 설정
3. **모킹**: 외부 서비스 및 API 호출을 모킹하여 빠르고 안정적인 테스트 보장
4. **비동기 테스트**: pytest-asyncio를 사용하여 비동기 코드 테스트
5. **명확한 명명**: 테스트 이름은 테스트 중인 내용을 명확하게 설명해야 합니다

## CI/CD 통합

테스트를 CI/CD 파이프라인에 통합하려면:

```yaml
# GitHub Actions 예시
- name: Run tests
  run: |
    python -m pip install pytest pytest-asyncio pytest-mock
    pytest -v
```

## 새 테스트 추가

새로운 기능을 추가할 때:
1. 해당 테스트 파일에 테스트 작성 (또는 새 파일 생성)
2. pytest 명명 규칙 준수 (`test_*.py`, `Test*` 클래스, `test_*` 메서드)
3. 필요에 따라 픽스처 및 모킹 사용
4. 테스트가 통과하는지 확인: `pytest -v`

## 문제 해결

### 테스트 실패 시
```bash
# 전체 스택 트레이스와 함께 실행
pytest -v --tb=long

# 첫 번째 실패 후 중지
pytest -x

# 실패한 테스트만 재실행
pytest --lf
```

### 모듈을 찾을 수 없음
필요한 모든 의존성이 설치되었는지 확인:
```bash
python3 -m pip install -r requirements.txt
```
