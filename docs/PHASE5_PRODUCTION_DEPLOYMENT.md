# Phase 5: Production Deployment (Part 1 Complete)

## 개요

Phase 5에서는 한국 정신건강 상담 LLM을 프로덕션 환경에 배포하기 위한 인프라를 구축했습니다. Docker 기반의 마이크로서비스 아키텍처, 실시간 모니터링, 그리고 한국 개인정보보호법을 준수하는 로깅 시스템을 구현했습니다.

## 완료된 작업 (Part 1)

### ✅ 1. Docker 배포 시스템

#### Dockerfile (Multi-stage Build)

**4단계 빌드 프로세스:**

```dockerfile
Stage 1: base
- CUDA 11.8 runtime (GPU support)
- Python 3.10
- 기본 시스템 패키지

Stage 2: dependencies
- Python 패키지 설치
- 한국어 임베딩 모델 사전 다운로드
  (jhgan/ko-sroberta-multitask)

Stage 3: application
- 애플리케이션 코드 복사
- 디렉토리 생성 (logs, data, backups, cache)
- Non-root user로 전환 (보안)

Stage 4: production (final)
- 프로덕션 최적화
- 스타트업 스크립트
- 환경 변수 설정
```

**보안 강화:**
- Non-root user 실행 (llmuser, UID 1000)
- 최소 권한 원칙
- 읽기 전용 설정 파일

**최적화:**
- 레이어 캐싱으로 빌드 시간 단축
- 멀티스테이지로 최종 이미지 크기 최소화
- 모델 캐싱으로 시작 시간 단축

**헬스체크:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1
```

#### docker-compose.yml

**7개 서비스 오케스트레이션:**

1. **mental-health-llm** (메인 LLM 서비스)
   - GPU 런타임 (NVIDIA)
   - 포트: 7860 (Gradio), 8000 (FastAPI)
   - 리소스 제한: 8 CPU, 64GB RAM, 1 GPU
   - 헬스체크 활성화

2. **redis** (캐싱 & 세션 관리)
   - 버전: 7-alpine
   - 비밀번호 보호
   - AOF 영속성

3. **postgres** (대화 히스토리 & 메트릭)
   - 버전: 15-alpine
   - 전용 DB: mental_health_db
   - 자동 초기화 스크립트

4. **prometheus** (메트릭 수집)
   - LLM 메트릭 스크래핑
   - TSDB 저장소
   - 보존 정책 설정 가능

5. **grafana** (시각화)
   - 대시보드 프로비저닝
   - Prometheus 데이터소스 연결
   - 관리자 계정

6. **nginx** (리버스 프록시, 선택사항)
   - SSL 종료
   - 로드 밸런싱 준비
   - Profile: with-nginx

**볼륨 관리:**
```yaml
volumes:
  - model_cache:/app/models          # 모델 캐시 (재시작 시 유지)
  - conversation_logs:/app/logs      # 암호화된 대화 로그
  - data_volume:/app/data            # 데이터 디렉토리
  - backup_volume:/app/backups       # 백업 디렉토리
```

**네트워킹:**
```yaml
networks:
  mental-health-network:
    driver: bridge
```

#### scripts/start.sh

**스타트업 자동화:**
```bash
#!/bin/bash
1. 환경 변수 로드 (.env)
2. CUDA 가용성 체크
3. 데이터베이스 마이그레이션 (필요 시)
4. 모드별 실행:
   - api: FastAPI만
   - gradio: Gradio 웹 인터페이스만
   - hybrid: 둘 다 (기본값)
```

### ✅ 2. 모니터링 시스템 (src/monitoring.py)

#### ProductionMonitor 클래스

**추적 메트릭:**

**대화 메트릭:**
- 응답 시간 (평균, p95, p99)
- 생성된 토큰 수
- 위기 감지 (레벨별)
- 사용자 만족도 (1-5)
- 사용 치료 기법 (CBT/DBT/ACT)
- 모델 신뢰도 (0-1)

**시스템 메트릭:**
- CPU 사용률
- 메모리 사용률
- GPU 메모리 사용량
- GPU 활용률
- 활성 세션 수

**대화 품질 메트릭:**
```python
track_conversation_quality(response, context, reference):
  returns {
    "relevance": 0.0-1.0,           # 컨텍스트 관련성
    "empathy_score": 0.0-1.0,       # 공감 표현 (한국어 키워드)
    "safety_score": 0.0-1.0,        # 안전성 체크
    "professional_boundary": 0.0-1.0 # 전문적 경계
  }
```

**주요 기능:**

1. **실시간 통계**
```python
monitor.get_realtime_stats()
# Returns: 최근 1시간 요약
# - 총 대화 수
# - 평균 응답 시간
# - 위기 감지 건수
# - 평균 만족도
# - 시스템 리소스
```

2. **일일 보고서**
```python
monitor.generate_daily_report(date)
# Returns:
# - 개요: 대화 수, 사용자 수, 평균 대화 길이
# - 성능: 평균/p95/p99 응답 시간
# - 안전: 위기 감지 건수 및 레벨별 분류
# - 품질: 사용자 만족도, 응답률
# - 치료: 사용된 기법 분포
```

3. **주간 보고서**
```python
monitor.generate_weekly_report()
# Returns: 7일 집계
# - 일별 대화 수
# - 평균 일일 대화
# - 총 위기 감지
# - 주간 평균 응답 시간
```

4. **Prometheus 메트릭**
```python
monitor.get_prometheus_metrics()
# Exports:
# llm_response_time_seconds
# llm_crisis_detections_total
# llm_crisis_detections_last_hour
# llm_cpu_percent
# llm_memory_percent
# llm_active_sessions
# llm_gpu_memory_gb
# llm_user_satisfaction_avg
```

5. **메트릭 내보내기**
```python
monitor.export_metrics(filepath, format="json")
# Exports all metrics to JSON file
```

**사용 예시:**
```python
from src.monitoring import get_monitor

monitor = get_monitor()

# 대화 추적
monitor.track_conversation(
    session_id="abc123",
    response_time=1.234,
    tokens_generated=150,
    crisis_detected=False,
    therapy_technique="CBT",
    model_confidence=0.92
)

# 사용자 만족도
monitor.track_user_satisfaction(
    session_id="abc123",
    rating=4.5
)

# 시스템 리소스
metrics = monitor.track_system_resources()

# 일일 보고서
report = monitor.generate_daily_report()
print(f"Today: {report['overview']['total_conversations']} conversations")
print(f"Crisis: {report['safety']['crisis_rate_percent']}%")
```

### ✅ 3. 로깅 시스템 (src/logging_system.py)

#### 한국 개인정보보호법 준수

**개인정보보호법 (PIPA) 요구사항:**

1. ✅ **개인정보 최소 수집**
   - 필수 정보만 수집
   - 세션 ID 해싱 (SHA-256)
   - 비식별화

2. ✅ **개인정보 암호화**
   - Fernet 대칭 암호화
   - 저장 시 암호화 (at-rest)
   - 안전한 키 관리

3. ✅ **개인정보 보유 기간**
   - 기본값: 90일
   - 자동 삭제 (cleanup_old_logs)
   - Dry-run 모드 지원

4. ✅ **개인정보 마스킹**
   - 전화번호: 010-1234-5678 → [전화번호]
   - 주민등록번호: 123456-1234567 → [주민등록번호]
   - 이메일: user@example.com → [이메일]
   - 신용카드: 1234-5678-9012-3456 → [카드번호]
   - 주소: 서울시 강남구 역삼동 → [주소]

5. ✅ **개인정보 열람/수정/삭제 권리**
   - read_conversation(): 특정 대화 조회
   - get_session_history(): 세션 히스토리
   - export_logs(): 법적 요청 시 제공
   - cleanup_old_logs(): 삭제

6. ✅ **감사 추적**
   - 모든 로깅 작업 기록
   - 별도 감사 로그 파일
   - 타임스탬프, 작업 유형, 세션 ID

#### PrivacyMasker 클래스

**PII 패턴 매칭 (한국):**

```python
PII_PATTERNS = {
    "phone": [
        r"01[0-9]-\d{3,4}-\d{4}",  # 010-1234-5678
        r"01[0-9]\d{7,8}",          # 01012345678
        r"\d{2,3}-\d{3,4}-\d{4}"   # 02-123-4567
    ],
    "rrn": [  # 주민등록번호
        r"\d{6}-[1-4]\d{6}",
        r"\d{13}"
    ],
    "email": [...],
    "credit_card": [...],
    "address": [...]
}
```

**마스킹 예시:**
```python
# Before
"제 전화번호는 010-1234-5678이고, 주민등록번호는 900101-1234567입니다."

# After (masked)
"제 전화번호는 [전화번호]이고, 주민등록번호는 [주민등록번호]입니다."
```

#### ConversationLogger 클래스

**핵심 기능:**

1. **안전한 로깅**
```python
logger.log_conversation(
    session_id="user_abc",
    turn_data={
        "user_message": "우울해요. 제 전화번호는 010-1234-5678입니다.",
        "assistant_response": "힘드시군요. 어떤 일이 있으셨나요?",
        "timestamp": datetime.now(),
        "crisis_detected": False,
        "metadata": {"source": "web"}
    },
    mask_pii=True  # PII 자동 마스킹
)
```

2. **암호화 저장**
```python
# 평문 로그 (파일에 저장되지 않음)
{
    "entry_id": "uuid-1234",
    "session_id": "hashed_abc",  # 해싱됨
    "user_message": "우울해요. 제 전화번호는 [전화번호]입니다.",  # 마스킹됨
    "assistant_response": "...",
    "timestamp": "2025-11-12T10:30:00"
}

# 실제 파일 저장 (암호화됨)
gAAAAABl... [encrypted blob] ...xyz==
```

3. **보존 기간 관리**
```python
# 90일 이상 된 로그 삭제
deleted = logger.cleanup_old_logs(dry_run=False)
print(f"{deleted} files deleted")
```

4. **법적 요청 대응**
```python
# 특정 기간 로그 내보내기
logger.export_logs(
    output_path=Path("export_2025-01.json"),
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
    anonymize=True  # 익명화 유지
)
```

5. **통계 조회**
```python
stats = logger.get_statistics(
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now()
)
# Returns:
# - total_entries
# - unique_sessions
# - crisis_detections
# - crisis_rate
```

**파일 구조:**
```
logs/
├── .encryption_key           # 암호화 키 (secure!)
├── audit.log                 # 감사 로그
├── conversations_20251112.log  # 일별 로그 (암호화됨)
├── conversations_20251113.log
└── ...
```

**보안 모범 사례:**
- 암호화 키를 환경 변수 또는 Key Management Service에 저장
- 로그 파일 접근 권한 제한 (600)
- 정기적인 백업 및 오프사이트 저장
- 감사 로그 별도 관리

## 배포 가이드

### 1. 사전 요구사항

```bash
# Docker & Docker Compose
docker --version  # >= 20.10
docker-compose --version  # >= 2.0

# NVIDIA Docker Runtime (GPU 사용 시)
nvidia-docker --version

# 최소 시스템 요구사항
# - CPU: 8+ cores
# - RAM: 64GB+
# - GPU: NVIDIA GPU with 24GB+ VRAM (권장: RTX A100)
# - Disk: 100GB+ SSD
```

### 2. 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
REDIS_PASSWORD=your_secure_password
POSTGRES_PASSWORD=your_secure_password
GRAFANA_PASSWORD=your_secure_password
ENVIRONMENT=production
```

### 3. 빌드 및 실행

```bash
# 프로덕션 빌드
docker build --target production -t korean-mental-health-llm:latest .

# 전체 스택 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f mental-health-llm

# 상태 확인
docker-compose ps
```

### 4. 헬스체크

```bash
# LLM 서비스
curl http://localhost:7860/health

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health
```

### 5. 접속

- **Gradio 웹 인터페이스**: http://localhost:7860
- **FastAPI 문서**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/changeme)

## 모니터링 & 운영

### 일일 체크리스트

```bash
# 1. 서비스 상태
docker-compose ps

# 2. 리소스 사용량
docker stats

# 3. 로그 확인
docker-compose logs --tail=100 mental-health-llm

# 4. 위기 감지 확인
# Grafana 대시보드에서 확인
# 또는
curl http://localhost:8000/metrics | grep crisis
```

### 주간 작업

```bash
# 1. 로그 백업
docker-compose exec mental-health-llm \
    python -c "from src.logging_system import get_conversation_logger; \
               logger = get_conversation_logger(); \
               logger.export_logs(Path('backup_weekly.json'), ...)"

# 2. 메트릭 리뷰
# Grafana에서 주간 보고서 확인

# 3. 디스크 공간 확인
df -h

# 4. 오래된 로그 정리 (dry-run)
docker-compose exec mental-health-llm \
    python -c "from src.logging_system import get_conversation_logger; \
               logger = get_conversation_logger(); \
               print(f'Would delete: {logger.cleanup_old_logs(dry_run=True)} files')"
```

### 월간 작업

```bash
# 1. 보안 업데이트
docker-compose pull
docker-compose up -d

# 2. 데이터베이스 백업
docker-compose exec postgres \
    pg_dump -U llmuser mental_health_db > backup_monthly.sql

# 3. 모니터링 데이터 아카이브
# Prometheus/Grafana 데이터 백업

# 4. 성능 리뷰
# 월간 보고서 생성 및 검토
```

## 트러블슈팅

### 일반적인 문제

**1. GPU 인식 안 됨**
```bash
# NVIDIA 런타임 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi

# docker-compose.yml에서 runtime: nvidia 확인
```

**2. 메모리 부족**
```bash
# 메모리 사용량 확인
docker stats

# 리소스 제한 조정 (docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 64G  # 증가
```

**3. 느린 응답 시간**
```bash
# 모니터링 메트릭 확인
curl http://localhost:8000/metrics

# GPU 활용률 확인
nvidia-smi -l 1

# 동시 요청 수 제한 검토
```

**4. 로그 파일 과다**
```bash
# 자동 정리
docker-compose exec mental-health-llm \
    python -c "from src.logging_system import get_conversation_logger; \
               logger = get_conversation_logger(); \
               logger.cleanup_old_logs()"

# 보존 기간 조정 (logging_system.py)
retention_days=60  # 90 → 60일
```

## 보안 고려사항

### 1. 네트워크 보안
```yaml
# docker-compose.yml
# 내부 서비스는 외부 노출 안 함
redis:
  ports:
    - "127.0.0.1:6379:6379"  # localhost만

postgres:
  ports:
    - "127.0.0.1:5432:5432"  # localhost만
```

### 2. 비밀 관리
```bash
# Docker Secrets 사용 (권장)
echo "my_secret_password" | docker secret create postgres_password -

# 또는 환경 변수 파일
chmod 600 .env
```

### 3. SSL/TLS
```bash
# Nginx 프로필로 SSL 활성화
docker-compose --profile with-nginx up -d

# Let's Encrypt 인증서
certbot certonly --standalone -d your-domain.com
```

### 4. 접근 제어
```bash
# 방화벽 설정
ufw allow 443/tcp  # HTTPS
ufw deny 7860/tcp  # Gradio (내부만)
ufw deny 8000/tcp  # API (내부만)
```

## 성능 최적화

### 1. 모델 캐싱
```python
# 모델을 볼륨에 캐시
volumes:
  - model_cache:/app/models

# 첫 실행 후 재사용
```

### 2. Redis 캐싱
```python
# 자주 사용되는 응답 캐시
# 세션 데이터 캐시
# TTL 설정으로 메모리 관리
```

### 3. 데이터베이스 최적화
```sql
-- 인덱스 생성
CREATE INDEX idx_session_id ON conversations(session_id);
CREATE INDEX idx_timestamp ON conversations(timestamp);

-- 정기적인 VACUUM
```

### 4. 로드 밸런싱
```yaml
# docker-compose.yml
# 여러 인스턴스 실행
docker-compose up -d --scale mental-health-llm=3

# Nginx로 로드 밸런싱
```

## 다음 단계 (Phase 5 Part 2)

### 예정된 작업:

- [ ] **FastAPI REST API** (src/api.py)
  - POST /chat - 대화 엔드포인트
  - GET /health - 헬스체크
  - GET /metrics - Prometheus 메트릭
  - POST /feedback - 사용자 피드백

- [ ] **A/B 테스팅 프레임워크**
  - 프롬프트 버전 비교
  - 모델 파라미터 실험
  - 통계적 유의성 검증

- [ ] **종합 테스트 스위트**
  - test_safety_critical.py (100% 커버리지)
  - test_cultural_sensitivity.py
  - test_therapeutic_accuracy.py
  - test_performance.py
  - test_integration.py

- [ ] **성능 벤치마크**
  - 응답 시간 < 3초
  - 동시 사용자 100명 처리
  - 메모리 사용량 < 40GB

- [ ] **완전한 문서화**
  - API 문서
  - 운영 가이드
  - 장애 대응 매뉴얼

## 참고 자료

### 공식 문서
- Docker: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/

### 한국 법규
- 개인정보보호법: https://www.pipc.go.kr/
- 정보통신망법: https://www.kisa.or.kr/

### 관련 프로젝트
- Sentence Transformers: https://www.sbert.net/
- Transformers: https://huggingface.co/docs/transformers/

---

## 요약

Phase 5 Part 1에서는 프로덕션 배포를 위한 핵심 인프라를 완성했습니다:

✅ **Docker 멀티스테이지 빌드**
✅ **7-서비스 오케스트레이션** (LLM, Redis, PostgreSQL, Prometheus, Grafana, Nginx)
✅ **실시간 모니터링 시스템** (응답 시간, 위기 감지, 품질 메트릭)
✅ **개인정보보호법 준수 로깅** (PII 마스킹, 암호화, 자동 보존)
✅ **헬스체크 & 자동 복구**
✅ **보안 강화** (non-root, 암호화, 접근 제어)

**프로덕션 준비 완료! 🚀**

다음 단계로 API 엔드포인트와 테스트 스위트를 완성하면 전체 시스템이 배포 가능합니다.
