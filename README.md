# 한국형 심리상담 LLM (Korean Mental Health Counseling LLM)

> 🧠 **SOLAR-Ko-10.7B 기반 한국어 심리상담 AI 시스템**

한국 문화와 언어에 특화된 공감적이고 전문적인 디지털 심리상담 도우미입니다.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 목차

- [주요 기능](#주요-기능)
- [시스템 요구사항](#시스템-요구사항)
- [설치 방법](#설치-방법)
- [사용 방법](#사용-방법)
- [프로젝트 구조](#프로젝트-구조)
- [설정](#설정)
- [테스트](#테스트)
- [배포](#배포)
- [주의사항](#주의사항)
- [기여하기](#기여하기)
- [라이선스](#라이선스)

## ✨ 주요 기능

### 1. 공감적 대화 생성
- **페르소나**: "마음이" - 따뜻하고 전문적인 디지털 심리상담 도우미
- **치료적 접근법**: CBT(인지행동치료), ACT(수용전념치료), 마음챙김 통합
- **한국 문화 맥락 이해**: 체면, 집단주의, 가족관계 등 고려

### 2. 감정 분석
- 실시간 감정 인식 (불안, 우울, 분노, 스트레스 등)
- 감정 강도 측정
- 한국어 특유의 간접 표현("그냥 그래요") 이해

### 3. 위기 감지 및 개입
- 자살, 자해 관련 표현 실시간 감지
- 심각도 평가 및 신뢰도 계산
- 즉각적인 전문기관 연계
- 응급 연락처 자동 제공 (자살예방상담전화 1393 등)

### 4. 대화 관리
- 최대 10턴 대화 이력 유지
- 문맥 기반 응답 생성
- 대화 요약 및 저장 기능

### 5. 메모리 최적화
- 4비트 양자화로 GPU 메모리 절약
- RTX A100 (80GB) 최적화
- 약 5-6GB 메모리 사용 (4비트 양자화 시)

## 🖥️ 시스템 요구사항

### 하드웨어
- **GPU**: NVIDIA RTX A100 (80GB) 또는 동급 이상
  - 최소 VRAM: 8GB (4비트 양자화)
  - 권장 VRAM: 16GB 이상
- **RAM**: 16GB 이상
- **저장공간**: 30GB 이상 (모델 캐시 포함)

### 소프트웨어
- **OS**: Ubuntu 22.04 LTS (권장) 또는 Windows 10/11
- **Python**: 3.10 이상
- **CUDA**: 12.1 이상
- **cuDNN**: 8.x

## 📦 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/yourusername/korean-mental-health-llm.git
cd korean-mental-health-llm
```

### 2. 가상환경 생성 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 설정 조정
```

### 5. GPU 확인

```bash
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

## 🚀 사용 방법

### 기본 사용 (Python 스크립트)

```python
from src.main import KoreanMentalHealthLLM

# LLM 초기화
llm = KoreanMentalHealthLLM(
    model_name="beomi/OPEN-SOLAR-KO-10.7B",
    load_in_4bit=True
)

# 인사말
print(llm.get_greeting())

# 대화
user_input = "요즘 너무 불안하고 걱정이 많아요."
result = llm.generate_response(user_input)

print(f"감정: {result['emotion']['primary_emotion']}")
print(f"응답: {result['response']}")

# 위기 감지 시
if result['crisis'] and result['crisis']['is_crisis']:
    print(f"⚠️ 위기 감지: {result['crisis']['crisis_type']}")
    print(result['intervention_message'])
```

### CLI 인터페이스

```bash
python -m src.main
```

### 웹 인터페이스 (Gradio)

```bash
python app.py
```

브라우저에서 `http://localhost:7860` 접속

### API 서버 (FastAPI)

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

API 문서: `http://localhost:8000/docs`

## 📁 프로젝트 구조

```
korean-mental-health-llm/
├── src/
│   ├── __init__.py                 # 패키지 초기화
│   ├── main.py                     # 메인 LLM 클래스
│   │
│   ├── # 감정 분석 시스템
│   ├── emotion_analyzer.py         # 감정 분석 (v1 호환 래퍼)
│   ├── emotion_analyzer_v2.py      # 감정 분석 v2 (권장)
│   │
│   ├── # 안전 시스템 (4층 구조)
│   ├── safety_system.py            # 위기 감지 (v1 호환 래퍼)
│   ├── safety_system_v2.py         # 4층 위기 감지 v2 (권장)
│   ├── response_guardrails.py      # 응답 가드레일
│   ├── ethical_boundaries.py       # 윤리적 경계
│   ├── emotional_safety.py         # 정서적 안전
│   ├── consistency_checker.py      # 일관성 검사
│   ├── hallucination_prevention.py # 환각 방지
│   ├── self_check_system.py        # 자기 점검 (6종 통합)
│   │
│   ├── # 프롬프트 시스템
│   ├── prompts.py                  # 프롬프트 템플릿 (v1 호환 래퍼)
│   ├── prompts_enhanced.py         # MIND-SAFE 프롬프트 v4 (권장)
│   │
│   ├── # 상담 효과 시스템
│   ├── counseling_effectiveness.py # 상담 품질 분석
│   ├── empathy_system.py           # 공감 시스템
│   ├── therapeutic_questions.py    # 치료적 질문
│   ├── session_structure.py        # 세션 구조
│   │
│   ├── # 세션 및 데이터
│   ├── session_storage.py          # SQLite 세션 저장소
│   ├── conversation_state.py       # 대화 상태 관리
│   │
│   ├── # RAG 및 개인화
│   ├── rag_system.py               # RAG 시스템
│   ├── personalization.py          # 개인화
│   ├── long_term_memory.py         # 장기 기억
│   │
│   └── utils.py                    # 유틸리티 함수
├── data/
│   ├── crisis_keywords.json        # 위기 키워드 목록
│   └── therapeutic_responses.json  # 치료적 응답 템플릿
├── tests/
│   ├── test_safety.py              # 안전 시스템 테스트
│   ├── test_new_systems.py         # 새 시스템 테스트
│   └── ...
├── app.py                          # Gradio 웹 인터페이스
├── main_integrated.py              # 통합 실행 파일
├── configs/
│   └── config.yaml                 # 설정 파일
├── requirements.txt                # Python 패키지 의존성
├── Dockerfile                      # Docker 이미지 빌드
├── .env.example                    # 환경 변수 예시
└── README.md                       # 프로젝트 문서
```

## ⚙️ 설정

### config.yaml 주요 설정

```yaml
# 모델 설정
model:
  name: "beomi/OPEN-SOLAR-KO-10.7B"
  quantization:
    enabled: true
    bits: 4  # 4비트 양자화

# 생성 파라미터
generation:
  temperature: 0.7      # 창의성 (0.0-1.0)
  top_p: 0.9           # 누적 확률
  max_new_tokens: 512  # 최대 토큰 수

# 대화 설정
conversation:
  max_turns: 10        # 최대 대화 턴 수

# 안전 시스템
safety:
  enable_crisis_detection: true
  crisis_threshold: 0.8
```

### 환경 변수 (.env)

```bash
# 모델 설정
MODEL_NAME=beomi/OPEN-SOLAR-KO-10.7B
USE_4BIT_QUANTIZATION=true

# GPU 설정
CUDA_VISIBLE_DEVICES=0
MAX_GPU_MEMORY=80GB

# 생성 파라미터
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=512

# 위기 상황 연락처
CRISIS_HOTLINE=1577-0199
SUICIDE_PREVENTION_HOTLINE=1393
```

## 🧪 테스트

### 전체 테스트 실행

```bash
pytest tests/ -v
```

### 특정 테스트 실행

```bash
# 안전 시스템 테스트
pytest tests/test_safety.py -v

# 감정 분석 테스트
pytest tests/test_safety.py::TestEmotionAnalyzer -v

# 위기 감지 테스트
pytest tests/test_safety.py::TestCrisisDetectionSystem -v
```

### 수동 테스트

```bash
# 위기 감지 시스템
python src/safety_system.py

# 감정 분석기
python src/emotion_analyzer.py

# 전체 시스템
python src/main.py
```

## 🐳 배포

### Docker 빌드

```bash
docker build -t korean-mental-health-llm:latest .
```

### Docker 실행 (GPU 사용)

```bash
docker run --gpus all \
  -p 7860:7860 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  korean-mental-health-llm:latest
```

### Docker Compose

```bash
docker-compose up -d
```

## ⚠️ 주의사항

### 법적 및 윤리적 고려사항

1. **전문 의료 서비스 아님**
   - 본 시스템은 전문 의료 진단이나 치료를 제공하지 않습니다
   - 심각한 정신건강 문제는 반드시 전문가와 상담하세요

2. **위기 상황 대응**
   - 자살, 자해 등 위기 상황에서는 즉시 전문기관에 연락하세요
   - 자살예방상담전화: **1393** (24시간)
   - 정신건강위기상담전화: **1577-0199** (24시간)
   - 응급상황: **119**

3. **개인정보 보호**
   - 대화 내용은 민감한 개인정보를 포함할 수 있습니다
   - 적절한 보안 조치를 취하세요
   - 대화 로그 저장 시 암호화 권장

4. **책임 제한**
   - 본 시스템 사용으로 인한 결과에 대해 개발자는 책임을 지지 않습니다
   - 보조 도구로만 사용하세요

### 기술적 제한사항

1. **모델 한계**
   - LLM의 응답이 항상 정확하거나 적절하지 않을 수 있습니다
   - 환각(hallucination) 현상이 발생할 수 있습니다

2. **위기 감지 정확도**
   - 위기 감지 시스템이 모든 위기 상황을 감지하지 못할 수 있습니다
   - 과감지(false positive)나 미감지(false negative) 가능

3. **문화적 맥락**
   - 한국 문화에 특화되어 있어 다른 문화권에서는 적절하지 않을 수 있습니다

## 🔧 트러블슈팅

### GPU 메모리 부족

```python
# config.yaml에서 양자화 비트 수 조정
model:
  quantization:
    bits: 4  # 8 대신 4 사용

# 또는 배치 크기 감소
generation:
  max_new_tokens: 256  # 512 대신 256
```

### 모델 로딩 느림

```bash
# 모델 캐시 디렉토리 설정
export HF_HOME=/path/to/cache
export TRANSFORMERS_CACHE=/path/to/cache
```

### CUDA 오류

```bash
# CUDA 버전 확인
nvcc --version
nvidia-smi

# PyTorch CUDA 호환성 확인
python -c "import torch; print(torch.version.cuda)"
```

## 🤝 기여하기

기여를 환영합니다! 다음 방법으로 기여할 수 있습니다:

1. 이슈 제기 (버그 리포트, 기능 제안)
2. 풀 리퀘스트 생성
3. 문서 개선
4. 테스트 케이스 추가

### 개발 가이드라인

```bash
# 개발 환경 설정
git clone https://github.com/yourusername/korean-mental-health-llm.git
cd korean-mental-health-llm
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 코드 스타일 체크
black src/ tests/
flake8 src/ tests/

# 테스트 실행
pytest tests/ -v --cov=src
```

## 📞 응급 연락처

- **자살예방상담전화**: 1393 (24시간)
- **정신건강위기상담전화**: 1577-0199 (24시간)
- **청소년전화**: 1388 (24시간)
- **여성긴급전화**: 1366 (24시간)
- **응급상황**: 119

## 📚 참고 자료

### 논문 및 연구
- [SOLAR 10.7B 모델](https://huggingface.co/upstage/SOLAR-10.7B-v1.0)
- [Korean Language Model](https://github.com/SKTBrain/KoBERT)

### 심리상담 가이드라인
- 한국심리학회 윤리강령
- 내담자 중심 치료 (Carl Rogers)
- 인지행동치료 (CBT)
- 수용전념치료 (ACT)

## 📄 라이선스

본 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👥 개발팀

- **프로젝트 리더**: [이름]
- **AI 엔지니어**: [이름]
- **심리상담 전문가**: [이름]

## 🙏 감사의 말

- [Upstage](https://www.upstage.ai/) - SOLAR 모델 제공
- [Beomi](https://github.com/beomi) - SOLAR-Ko 모델
- Hugging Face - Transformers 라이브러리
- 한국 심리상담 커뮤니티

---

**⚠️ 중요**: 이 시스템은 보조 도구일 뿐이며, 전문 의료 서비스를 대체할 수 없습니다. 심각한 정신건강 문제는 반드시 전문가와 상담하세요.

**📧 문의**: [이메일 주소]

**🌐 웹사이트**: [프로젝트 웹사이트]

**📱 GitHub**: [GitHub 저장소]

---

Made with ❤️ for Korean Mental Health
