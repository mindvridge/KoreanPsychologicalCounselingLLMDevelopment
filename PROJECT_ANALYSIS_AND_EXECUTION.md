# 한국형 심리상담 LLM 프로젝트 - 전체 분석 및 실행 가이드

## 📋 프로젝트 개요

이 프로젝트는 **SOLAR-Ko-10.7B 기반 한국어 심리상담 AI 시스템**입니다. 한국 문화와 언어에 특화된 공감적이고 전문적인 디지털 심리상담 도우미를 제공합니다.

### 주요 특징
- 🤖 **다양한 LLM 지원**: 로컬 LLM (SOLAR-Ko) 또는 OpenAI API (GPT-4o-mini 등)
- 💬 **실시간 대화**: 텍스트 및 음성 상담 지원
- 🎭 **감정 분석**: 한국어 특화 감정 인식 시스템
- 🚨 **위기 감지**: 자살, 자해 등 위기 상황 실시간 감지 및 개입
- 📚 **RAG 시스템**: 치료 기법 지식베이스 통합
- 📊 **심리검사**: PHQ-9, GAD-7, K-10 등 자동화된 검사
- 🎤 **음성 상담**: STT (Whisper) + TTS (Zonos) 지원
- 🔒 **개인정보 보호**: PIPA 준수 로깅 시스템

---

## 🏗️ 프로젝트 구조

```
KoreanPsychologicalCounselingLLMDevelopment/
├── app.py                          # Gradio 웹 인터페이스 (포트 7860)
├── main_integrated.py              # 통합 시스템 실행
├── start_server.py                 # FastAPI 서버 시작 스크립트
├── start_all.py                    # 모든 서버 통합 실행
├── start.sh / start.bat            # 간편 실행 스크립트
│
├── src/                            # 핵심 소스 코드
│   ├── api.py                      # FastAPI 메인 서버 (포트 8000)
│   ├── voice_api.py                # 음성 API 서버 (포트 8001)
│   ├── main.py                     # 로컬 LLM 엔진
│   ├── openai_adapter.py           # OpenAI API 어댑터
│   ├── emotion_analyzer_v2.py      # 감정 분석기
│   ├── safety_system_v2.py         # 위기 감지 시스템
│   ├── rag_system.py               # RAG 지식베이스
│   ├── assessments.py              # 심리검사 관리
│   ├── monitoring.py              # 시스템 모니터링
│   └── ... (기타 모듈들)
│
├── configs/                        # 설정 파일
│   ├── config.yaml                 # 기본 설정 (OpenAI API 사용)
│   ├── config.local-test.yaml      # 로컬 테스트용
│   ├── config.openai-test.yaml     # OpenAI API 테스트용
│   └── config.a100-80gb.yaml       # 고성능 서버용
│
├── frontend/                       # 프론트엔드 (HTML/JS)
│   ├── index.html                  # 메인 페이지
│   ├── voice-app.js                # 음성 상담 클라이언트
│   └── ...
│
├── knowledge_base/                 # RAG 지식베이스
│   ├── counseling_techniques.json  # 상담 기법
│   ├── crisis_protocols/           # 위기 대응 프로토콜
│   └── therapy_techniques/         # 치료 매뉴얼
│
├── data/                           # 데이터 파일
│   ├── crisis_keywords.json        # 위기 키워드
│   └── therapeutic_responses.json  # 치료적 응답 템플릿
│
├── tests/                          # 테스트 코드
├── docs/                           # 문서
└── requirements.txt                # Python 패키지 의존성
```

---

## 🚀 실행 방법

### 방법 1: 간편 실행 (권장)

#### Windows
```powershell
# 배치 파일 실행
.\start.bat

# 또는 PowerShell에서
python start_all.py
```

#### Linux/Mac
```bash
# 쉘 스크립트 실행
./start.sh

# 또는 직접 실행
python3 start_all.py
```

이 방법은 **모든 서버를 자동으로 시작**합니다:
- 메인 API 서버 (포트 8000)
- 음성 API 서버 (포트 8001)

---

### 방법 2: 개별 서버 실행

#### 옵션 A: Gradio 웹 인터페이스 (가장 쉬움)

```bash
# 가상환경 활성화 (있는 경우)
# Windows: .\venv\Scripts\Activate.ps1
# Linux/Mac: source venv/bin/activate

# Gradio 서버 실행
python app.py
```

**접속**: http://localhost:7860

- ✅ 웹 브라우저에서 바로 사용 가능
- ✅ 감정 분석, 위기 감지 시각화
- ✅ 대화형 인터페이스

---

#### 옵션 B: FastAPI 서버 (API 사용)

```bash
# 방법 1: start_server.py 사용
python start_server.py

# 방법 2: uvicorn 직접 실행
uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

**접속**:
- API: http://localhost:8000
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

#### 옵션 C: 통합 시스템

```bash
python main_integrated.py
```

이 방법은 모든 컴포넌트를 초기화하고 대화형 모드로 실행합니다.

---

### 방법 3: 음성 상담 포함 실행

```bash
# 모든 서버 시작 (채팅 + 음성)
python start_all.py
```

**접속**:
- 채팅 API: http://localhost:8000
- 음성 API: http://localhost:8001
- WebSocket: ws://localhost:8001/ws/voice/{session_id}

---

## ⚙️ 사전 설정

### 1. 환경 변수 설정 (.env 파일)

프로젝트 루트에 `.env` 파일을 생성하세요:

```env
# =============================================================================
# 필수 설정
# =============================================================================

# OpenAI API 키 (OpenAI 사용 시 필수)
OPENAI_API_KEY=your_openai_api_key_here

# Hugging Face 토큰 (로컬 LLM 사용 시)
HUGGINGFACE_TOKEN=your_hf_token_here

# 설정 파일 경로
CONFIG_PATH=configs/config.yaml

# API 설정
API_HOST=127.0.0.1
API_PORT=8000

# 로그 레벨
LOG_LEVEL=INFO

# =============================================================================
# 데이터베이스 설정 (선택사항)
# =============================================================================
DATABASE_PATH=./data/mental_health.db
DATABASE_URL=sqlite:///./data/mental_health.db
ENABLE_LONG_TERM_MEMORY=true
```

---

### 2. 패키지 설치

```bash
# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows: .\venv\Scripts\Activate.ps1
# Linux/Mac: source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

---

### 3. 설정 파일 선택

프로젝트에는 여러 설정 파일이 있습니다:

| 설정 파일 | 용도 | LLM 제공자 |
|---------|------|-----------|
| `config.yaml` | 기본 설정 | OpenAI API (GPT-4o-mini) |
| `config.local-test.yaml` | 로컬 테스트 | 로컬 LLM (SOLAR-Ko) |
| `config.openai-test.yaml` | OpenAI 테스트 | OpenAI API |
| `config.a100-80gb.yaml` | 고성능 서버 | 로컬 LLM (큰 모델) |

`.env` 파일에서 선택:
```env
CONFIG_PATH=configs/config.yaml
```

---

## 🔧 주요 설정 옵션

### config.yaml 주요 설정

```yaml
# 모델 설정
model:
  provider: "openai"  # "local", "openai", "mock"
  name: "gpt-4o-mini"  # OpenAI 모델명
  openai:
    temperature: 0.7
    max_tokens: 500

# 위기 감지
safety:
  crisis_detection_threshold: 0.7
  auto_alert_professionals: false

# RAG 시스템
rag:
  knowledge_base_dir: "./knowledge_base"
  embedding_model: "jhgan/ko-sroberta-multitask"

# 음성 상담
stt:
  model: "medium"  # Whisper 모델 크기
  use_faster_whisper: true
tts:
  model: "Zyphra/Zonos-v0.1-transformer"
```

---

## 📡 API 사용 예시

### 1. 기본 대화

```python
import requests

# 대화 시작
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "message": "요즘 너무 불안하고 걱정이 많아요.",
        "session_id": "test-session-123"
    }
)

result = response.json()
print(f"응답: {result['response']}")
print(f"감정: {result['emotions']['primary_emotion']}")
print(f"위기 감지: {result['crisis_detected']}")
```

### 2. 음성 상담 (WebSocket)

```javascript
// JavaScript 예시
const ws = new WebSocket('ws://localhost:8001/ws/voice/session-123');

ws.onopen = () => {
    // 오디오 스트림 전송
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // 오디오 데이터 전송
        });
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'audio') {
        // TTS 오디오 재생
    }
};
```

---

## 🎯 실행 모드별 비교

| 모드 | 실행 명령 | 포트 | 특징 |
|------|----------|------|------|
| **Gradio** | `python app.py` | 7860 | 웹 UI, 가장 쉬움 |
| **FastAPI** | `python start_server.py` | 8000 | REST API, 개발용 |
| **통합** | `python start_all.py` | 8000, 8001 | 모든 기능 포함 |
| **통합 시스템** | `python main_integrated.py` | - | CLI 모드 |

---

## 🐛 문제 해결

### 문제 1: OpenAI API 키 오류

**증상**: `OPENAI_API_KEY 환경 변수가 설정되지 않았습니다`

**해결**:
1. `.env` 파일에 `OPENAI_API_KEY=your_key` 추가
2. 또는 환경 변수로 직접 설정:
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="your_key"
   
   # Linux/Mac
   export OPENAI_API_KEY="your_key"
   ```

---

### 문제 2: 포트가 이미 사용 중

**증상**: `Address already in use`

**해결**:
```bash
# 다른 포트 사용
uvicorn src.api:app --host 127.0.0.1 --port 8001 --reload

# 또는 사용 중인 프로세스 종료
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

---

### 문제 3: GPU 메모리 부족

**증상**: `CUDA out of memory`

**해결**:
1. `config.yaml`에서 모델 크기 줄이기:
   ```yaml
   stt:
     model: "small"  # large-v3 → small
   ```
2. 4-bit 양자화 사용 (이미 기본값)
3. 배치 크기 줄이기

---

### 문제 4: 모델 다운로드 실패

**증상**: `401 Client Error: Unauthorized`

**해결**:
```bash
# Hugging Face 로그인
huggingface-cli login

# 또는 .env에 토큰 추가
HUGGINGFACE_TOKEN=your_token
```

---

## 📊 시스템 요구사항

### 최소 사양
- **Python**: 3.10+
- **RAM**: 8GB
- **디스크**: 10GB
- **GPU**: 선택사항 (CPU 모드 가능)

### 권장 사양
- **Python**: 3.10+
- **RAM**: 16GB+
- **디스크**: 30GB+
- **GPU**: NVIDIA GPU (8GB+ VRAM)
  - RTX 3060 이상
  - RTX 5060 Ti (프로젝트 최적화 대상)

---

## 🎓 주요 기능 상세

### 1. 감정 분석
- 한국어 특화 감정 인식
- 간접 표현 이해 ("그냥 그래요" 등)
- 감정 강도 측정 (0-10)

### 2. 위기 감지
- 자살, 자해 키워드 실시간 감지
- 심각도 평가 (1-5단계)
- 자동 개입 메시지 생성
- 전문기관 연계 정보 제공

### 3. RAG 시스템
- 치료 기법 지식베이스 검색
- 문맥 기반 응답 생성
- 한국 문화 맥락 고려

### 4. 심리검사
- PHQ-9 (우울증)
- GAD-7 (불안)
- K-10 (정신건강 선별)

### 5. 음성 상담
- 실시간 STT (Whisper)
- 자연스러운 TTS (Zonos)
- WebSocket 스트리밍

---

## 📚 추가 문서

- **API 가이드**: `docs/API_GUIDE.md`
- **프론트엔드 통합**: `docs/FRONTEND_INTEGRATION.md`
- **로컬 설정**: `SETUP_LOCAL.md`
- **프로젝트 완료 보고**: `docs/PROJECT_COMPLETE.md`

---

## ✅ 빠른 시작 체크리스트

- [ ] Python 3.10+ 설치 확인
- [ ] `requirements.txt` 패키지 설치
- [ ] `.env` 파일 생성 및 API 키 설정
- [ ] `config.yaml` 확인 (또는 원하는 설정 파일)
- [ ] `python app.py` 또는 `python start_all.py` 실행
- [ ] http://localhost:7860 또는 http://localhost:8000 접속

---

## 🆘 긴급 연락처

시스템 사용 중 위기 상황이 감지되면 다음 연락처를 안내합니다:

- **자살예방상담전화**: 1393 (24시간)
- **정신건강위기상담전화**: 1577-0199 (24시간)
- **청소년전화**: 1388
- **응급상황**: 119

---

## 📝 주의사항

⚠️ **중요**: 이 시스템은 보조 도구일 뿐이며, 전문 의료 서비스를 대체할 수 없습니다. 심각한 정신건강 문제는 반드시 전문가와 상담하세요.

---

**Made with ❤️ for Korean Mental Health**

