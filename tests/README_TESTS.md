# 테스트 가이드

한국형 심리상담 LLM 시스템의 종합 테스트 스위트 사용 가이드

## 📋 목차

- [테스트 개요](#테스트-개요)
- [설치](#설치)
- [테스트 실행](#테스트-실행)
- [테스트 파일 설명](#테스트-파일-설명)
- [커버리지 목표](#커버리지-목표)
- [CI/CD 통합](#cicd-통합)

---

## 테스트 개요

### 테스트 구조

```
tests/
├── test_safety_critical.py      # 위기 감지 (100% 커버리지 목표)
├── test_api.py                   # FastAPI 엔드포인트
├── test_integration.py           # 엔드-투-엔드 통합
├── test_cultural_sensitivity.py  # 한국 문화 적합성
├── test_performance.py           # 성능 벤치마크
├── test_therapeutic_accuracy.py  # 치료 기법 정확성
├── test_safety.py                # 기존 안전 테스트
├── test_phase2_systems.py        # Phase 2 시스템 테스트
├── test_rag_system.py            # RAG 시스템
├── conftest.py                   # 공유 픽스처
└── README_TESTS.md               # 이 파일
```

### 테스트 유형

| 유형 | 설명 | 우선순위 |
|------|------|----------|
| **Safety Critical** | 생명과 직결된 위기 감지 | 🔴 최고 |
| **API** | REST API 엔드포인트 | 🔴 높음 |
| **Integration** | 전체 시스템 통합 | 🟡 중간 |
| **Cultural** | 한국 문화 적합성 | 🟡 중간 |
| **Performance** | 성능 벤치마크 | 🟢 낮음 |
| **Therapeutic** | 치료 기법 검증 | 🟡 중간 |

---

## 설치

### 1. 테스트 의존성 설치

```bash
pip install -r requirements.txt
```

주요 테스트 패키지:
- `pytest>=7.4.0` - 테스트 프레임워크
- `pytest-cov>=4.1.0` - 커버리지 리포트
- `pytest-asyncio>=0.21.0` - 비동기 테스트
- `pytest-mock>=3.12.0` - Mocking
- `httpx>=0.25.0` - FastAPI 테스트
- `psutil>=5.9.0` - 성능 모니터링

### 2. 설정 확인

```bash
# pytest.ini 확인
cat pytest.ini

# conftest.py 확인
cat tests/conftest.py
```

---

## 테스트 실행

### 전체 테스트

```bash
# 모든 테스트 실행
pytest

# 상세 출력
pytest -v

# 커버리지 포함
pytest --cov=src --cov-report=html
```

### 특정 테스트 파일

```bash
# 위기 감지 테스트만
pytest tests/test_safety_critical.py -v

# API 테스트만
pytest tests/test_api.py -v

# 통합 테스트만
pytest tests/test_integration.py -v
```

### 마커로 필터링

```bash
# Safety critical 테스트만 (최우선)
pytest -m safety_critical -v

# API 테스트만
pytest -m api -v

# 통합 테스트만
pytest -m integration -v

# 성능 테스트만
pytest -m performance -v

# 느린 테스트 제외
pytest -m "not slow" -v
```

### 특정 테스트 함수/클래스

```bash
# 특정 테스트 함수
pytest tests/test_safety_critical.py::TestSuicideDetection::test_direct_suicide_detection -v

# 특정 클래스의 모든 테스트
pytest tests/test_safety_critical.py::TestSuicideDetection -v

# 키워드로 검색
pytest -k "suicide" -v
pytest -k "api and not slow" -v
```

### 병렬 실행

```bash
# pytest-xdist 설치 (선택사항)
pip install pytest-xdist

# 4개 프로세스로 병렬 실행
pytest -n 4
```

### 실패한 테스트만 재실행

```bash
# 실패한 테스트만
pytest --lf

# 실패한 테스트를 먼저, 그 다음 나머지
pytest --ff
```

---

## 테스트 파일 설명

### 1. test_safety_critical.py (🔴 최우선)

**목적**: 위기 감지 시스템의 100% 정확성 검증

**테스트 항목**:
- ✅ 직접적 자살 표현 감지
- ✅ 구체적 자살 계획 감지
- ✅ 즉각적 위험 감지
- ✅ 부정 표현 처리
- ✅ 은유적 표현 감지
- ✅ 자해 행동 및 충동 감지
- ✅ 타해 의도 감지
- ✅ 위급성 수준 분류
- ✅ 긴급 연락처 제공
- ✅ 대화 맥락 분석
- ✅ 오탐 최소화

**실행**:
```bash
pytest tests/test_safety_critical.py -v
```

**커버리지 목표**: **100%** (필수)

---

### 2. test_api.py (🔴 높음)

**목적**: FastAPI REST API 엔드포인트 검증

**테스트 항목**:
- ✅ 루트 엔드포인트
- ✅ 건강 체크 (GET /api/v1/health)
- ✅ 대화 처리 (POST /api/v1/chat)
- ✅ 세션 관리 (GET/DELETE /api/v1/session/{id})
- ✅ 심리 평가 (POST /api/v1/assessment)
- ✅ 피드백 (POST /api/v1/feedback)
- ✅ 통계 (GET /api/v1/stats)
- ✅ 시스템 정보 (GET /api/v1/system/info)
- ✅ 메트릭 (GET /metrics)
- ✅ 에러 처리
- ✅ 입력 검증
- ✅ 인증 (API Key)
- ✅ CORS

**실행**:
```bash
pytest tests/test_api.py -v
pytest -m api -v
```

---

### 3. test_integration.py (🟡 중간)

**목적**: 전체 시스템의 엔드-투-엔드 통합 검증

**테스트 항목**:
- ✅ 완전한 대화 흐름
- ✅ 위기 개입 흐름
- ✅ API 통합
- ✅ 세션 지속성
- ✅ RAG 시스템 통합
- ✅ 모니터링 통합
- ✅ 로깅 통합
- ✅ 실제 사용자 시나리오

**실행**:
```bash
pytest tests/test_integration.py -v
pytest -m integration -v
```

---

### 4. test_cultural_sensitivity.py (🟡 중간)

**목적**: 한국 문화에 특화된 상담 접근법 검증

**테스트 항목**:
- ✅ 한국 특유 감정 (한, 정, 눈치)
- ✅ 가족 관계 맥락 (부모-자녀, 시댁)
- ✅ 간접 표현 이해
- ✅ 존댓말/반말 처리
- ✅ 집단주의 맥락
- ✅ 나이와 서열
- ✅ 학업/직업 압박
- ✅ 사회적 낙인

**실행**:
```bash
pytest tests/test_cultural_sensitivity.py -v
```

---

### 5. test_performance.py (🟢 낮음)

**목적**: 시스템 성능 및 확장성 검증

**테스트 항목**:
- ✅ 응답 시간 (위기 감지 < 1초, 감정 분석 < 0.5초, API < 3초)
- ✅ 처리량 (메시지/초)
- ✅ 메모리 사용량 (< 40GB)
- ✅ 메모리 누수 검사
- ✅ 동시 사용자 처리 (100명 목표)
- ✅ 지속 부하 테스트

**실행**:
```bash
pytest tests/test_performance.py -v
pytest -m performance -v

# 느린 테스트 제외
pytest tests/test_performance.py -m "not slow" -v
```

**성능 목표**:
| 메트릭 | 목표 |
|--------|------|
| 위기 감지 응답 시간 | < 1초 |
| 감정 분석 응답 시간 | < 0.5초 |
| RAG 검색 시간 | < 0.5초 |
| API 엔드포인트 응답 | < 3초 |
| GPU 메모리 | < 40GB |
| 동시 사용자 | 100명 |

---

### 6. test_therapeutic_accuracy.py (🟡 중간)

**목적**: 심리치료 기법의 정확성 검증

**테스트 항목**:
- ✅ CBT 기법 (인지 재구성, 행동 활성화)
- ✅ DBT 기법 (마음챙김, 고통 감내, 감정 조절)
- ✅ ACT 기법 (수용, 가치 명료화, 탈융합)
- ✅ 치료적 경계 (진단/처방 금지)
- ✅ 공감과 타당화
- ✅ 안전성과 윤리
- ✅ 문화적 역량

**실행**:
```bash
pytest tests/test_therapeutic_accuracy.py -v
```

---

## 커버리지 목표

### 전체 목표

| 컴포넌트 | 목표 커버리지 |
|----------|--------------|
| **안전 기능** (safety_system_v2.py) | **100%** 🔴 |
| **핵심 기능** (LLM, 감정 분석) | **90%** 🟡 |
| **API** (api.py) | **85%** 🟡 |
| **전체** | **80%** 🟢 |

### 커버리지 리포트 생성

```bash
# HTML 리포트 생성
pytest --cov=src --cov-report=html

# 브라우저에서 확인
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# 터미널에서 누락된 라인 확인
pytest --cov=src --cov-report=term-missing

# XML 리포트 (CI/CD용)
pytest --cov=src --cov-report=xml

# 커버리지 기준 미달 시 실패
pytest --cov=src --cov-fail-under=80
```

---

## CI/CD 통합

### GitHub Actions 예제

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run safety critical tests
      run: |
        pytest tests/test_safety_critical.py -v
    
    - name: Run all tests with coverage
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## 문제 해결

### 테스트 실패 시

1. **Safety Critical 테스트 실패**:
   ```bash
   # 상세 로그 확인
   pytest tests/test_safety_critical.py -vv -s
   
   # 특정 테스트만 디버그
   pytest tests/test_safety_critical.py::TestSuicideDetection::test_direct_suicide_detection -vv -s
   ```

2. **Import 에러**:
   ```bash
   # Python 경로 확인
   echo $PYTHONPATH
   
   # 수동으로 경로 추가
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Mock 관련 에러**:
   ```bash
   # pytest-mock 재설치
   pip install --upgrade pytest-mock
   ```

4. **성능 테스트 실패**:
   ```bash
   # GPU 메모리 확인
   nvidia-smi
   
   # CPU 모드로 테스트
   export CUDA_VISIBLE_DEVICES=""
   pytest tests/test_performance.py
   ```

---

## 테스트 작성 가이드

### 새 테스트 추가하기

1. **파일 생성**:
   ```python
   # tests/test_new_feature.py
   import pytest
   
   def test_new_feature():
       """테스트 설명"""
       assert True
   ```

2. **마커 추가**:
   ```python
   @pytest.mark.your_marker
   def test_something():
       pass
   ```

3. **픽스처 사용**:
   ```python
   def test_with_fixture(sample_conversation_history):
       assert len(sample_conversation_history) > 0
   ```

---

## 베스트 프랙티스

### DO ✅

- ✅ Safety critical 테스트는 100% 통과
- ✅ 테스트 이름은 명확하게 (`test_direct_suicide_detection`)
- ✅ 각 테스트는 하나의 기능만 검증
- ✅ Mock을 사용하여 외부 의존성 격리
- ✅ Parametrize로 여러 입력 테스트
- ✅ 테스트 문서화 (docstring)

### DON'T ❌

- ❌ 외부 API에 의존하는 테스트
- ❌ 실제 모델 로딩 (Mock 사용)
- ❌ 테스트 간 의존성
- ❌ 랜덤한 결과 (일관성 필요)
- ❌ 너무 긴 테스트 (분리 필요)

---

## 리소스

- [Pytest 공식 문서](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**문서 버전**: 1.0.0  
**마지막 업데이트**: 2024-01-15
