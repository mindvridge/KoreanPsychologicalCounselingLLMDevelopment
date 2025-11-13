# 장기 기억 및 개인화 기능 가이드

한국형 심리상담 LLM 시스템의 장기 기억 및 사용자 개인화 기능 완벽 가이드

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [데이터베이스 구조](#데이터베이스-구조)
- [사용 방법](#사용-방법)
- [프라이버시 및 보안](#프라이버시-및-보안)
- [API 통합](#api-통합)

---

## 개요

### 기존 시스템의 한계

**이전 (단기 기억만):**
- ❌ 세션 종료 후 대화 내용 소실
- ❌ 24시간 후 자동 삭제
- ❌ 이름 등 개인정보 기억 불가
- ❌ 증상 변화 추적 불가

### 새로운 시스템 (장기 기억)

**현재 (장기 기억 + 개인화):**
- ✅ 대화 내용 영구 저장 (암호화)
- ✅ 사용자 프로필 관리
- ✅ 이름 자동 추출 및 기억
- ✅ 증상 변화 장기 추적
- ✅ 개인화된 인사말 및 응답
- ✅ PIPA 완벽 준수

---

## 주요 기능

### 1. 사용자 프로필 관리

```python
# 자동 추출되는 정보:
- 이름 (예: "김철수" → "철수님"으로 호칭)
- 나이대 (예: "28살" → "20대")
- 성별
- 직업 (학생, 회사원 등)
- 주요 고민 (우울, 불안, 직장 스트레스 등)
```

**예시**:
```
사용자: "안녕하세요, 제 이름은 김철수입니다. 28살 회사원이에요."
시스템: [자동 추출]
  - 이름: 김철수
  - 선호 호칭: 철수님
  - 나이대: 20대
  - 직업: 회사원

# 다음 대화 (며칠 후)
사용자: "안녕하세요"
시스템: "어제 이후 처음이시네요, 철수님! 오늘은 어떠신가요?"
```

### 2. 대화 기록 영구 저장

```python
# 저장되는 정보:
- 모든 대화 내용 (PII 마스킹)
- 감지된 감정
- 위기 감지 이력
- 응답 시간
- 타임스탬프
```

**프라이버시 보호**:
- 전화번호 → `[전화번호]`
- 주민등록번호 → `[주민등록번호]`
- 이메일 → `[이메일]`
- 주소 → `[주소]`

### 3. 심리 평가 이력 추적

```python
# PHQ-9 (우울증) 추이:
2024-01-01: 18점 (중증 우울)
2024-01-15: 14점 (중등도 우울) ↓ 개선
2024-02-01: 10점 (경증 우울)  ↓ 개선

# 시스템 응답:
"지난 평가에 비해 우울 증상이 개선되고 있네요, 철수님! 
 계속 좋은 방향으로 가고 계십니다."
```

### 4. 개인화된 인사말

```python
# 신규 사용자:
"안녕하세요, 손님! 반갑습니다. 편안하게 이야기 나눠봐요."

# 이름 알게 된 후:
"안녕하세요, 철수님!"

# 재방문 (오늘):
"다시 만나서 반갑습니다, 철수님!"

# 재방문 (며칠 후):
"며칠 만이시네요, 철수님! 그동안 어떻게 지내셨어요?"

# 재방문 (오랜만):
"오랜만입니다, 철수님! 잘 지내셨나요?"
```

### 5. NER (이름 추출)

**지원되는 패턴**:
```python
✅ "제 이름은 김철수입니다"
✅ "김철수라고 합니다"
✅ "이름이 김철수예요"
✅ "저는 김철수입니다"
✅ "김철수라고 불러요"
```

**자동 검증**:
- ✅ 한국 성씨 확인 (김, 이, 박, 최 등 100개)
- ✅ 이름 길이 검증 (2-4자)
- ✅ 한글만 허용

---

## 데이터베이스 구조

### 테이블 구조

#### 1. Users (사용자)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(64) UNIQUE,  -- 익명 해시 ID
    created_at DATETIME,
    last_active DATETIME,
    consent_given BOOLEAN,        -- 데이터 저장 동의
    data_retention_days INTEGER,  -- 보관 기간
    total_conversations INTEGER,
    total_messages INTEGER,
    crisis_count INTEGER
);
```

#### 2. UserMetadata (사용자 메타데이터)
```sql
CREATE TABLE user_metadata (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    preferred_name VARCHAR(100),  -- 선호 호칭
    extracted_name VARCHAR(100),  -- 추출된 이름 (암호화 권장)
    age_range VARCHAR(20),        -- 나이대
    main_concerns JSON,            -- 주요 고민 배열
    conversation_style VARCHAR(20),
    updated_at DATETIME
);
```

#### 3. Conversations (대화 기록)
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(64),
    role VARCHAR(20),             -- 'user' or 'assistant'
    content TEXT,                  -- PII 마스킹된 내용
    timestamp DATETIME,
    detected_emotion VARCHAR(50),
    crisis_detected BOOLEAN,
    crisis_level INTEGER
);
```

#### 4. Assessments (평가 결과)
```sql
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    assessment_type VARCHAR(20),   -- phq9, gad7, k10
    score INTEGER,
    severity VARCHAR(50),
    conducted_at DATETIME
);
```

---

## 사용 방법

### Python에서 직접 사용

```python
from src.personalization import PersonalizationManager

# 초기화
pm = PersonalizationManager()

# 1. 사용자 생성/조회
user_id, is_new = pm.get_or_create_user(
    user_identifier="user@example.com",  # 선택사항
    consent=True
)

# 2. 대화 저장
pm.save_conversation_turn(
    user_id=user_id,
    session_id="session-123",
    role="user",
    content="제 이름은 김철수입니다. 우울해요.",
    detected_emotion="슬픔",
    crisis_detected=False
)

# 3. 개인화된 인사말
greeting = pm.get_personalized_greeting(user_id, is_new)
print(greeting)
# 출력: "안녕하세요, 철수님! 반갑습니다."

# 4. 대화 기록 조회
history = pm.get_conversation_history(user_id, limit=10)

# 5. 사용자 맥락 조회
context = pm.get_user_context(user_id)
print(context)
# {
#   "preferred_name": "철수님",
#   "age_range": "20대",
#   "main_concerns": ["우울", "직장 스트레스"],
#   "total_conversations": 5,
#   "crisis_count": 0
# }

# 6. 평가 저장
pm.save_assessment(
    user_id=user_id,
    session_id="session-123",
    assessment_type="phq9",
    responses=[2, 2, 2, 1, 1, 0, 1, 2, 1],
    score=12,
    severity="중등도 우울",
    interpretation="중등도 우울 증상이 있습니다",
    recommendations=["전문가 상담 권장"]
)

# 7. 평가 추이 확인
trend = pm.get_assessment_trend(user_id, "phq9")
print(trend)
# {
#   "trend": "improving",
#   "assessments": [...],
#   "latest_score": 12
# }
```

### NER (이름 추출) 사용

```python
from src.ner_extractor import KoreanNERExtractor

ner = KoreanNERExtractor()

# 이름 추출
text = "안녕하세요, 제 이름은 김철수입니다."
name = ner.extract_name(text)
print(name)  # "김철수"

# 나이 추출
text = "저는 28살이에요"
age = ner.extract_age(text)
print(age)  # 28

# 모든 정보 추출
text = "저는 김철수이고 28살 회사원입니다. 직장 스트레스가 심해요."
info = ner.extract_all(text)
print(info)
# ExtractedInfo(
#     name="김철수",
#     age=28,
#     occupation="회사원",
#     concerns=["스트레스", "직장"]
# )

# 선호 호칭 생성
preferred = ner.generate_preferred_name("김철수", "male")
print(preferred)  # "김철수님"
```

---

## 프라이버시 및 보안

### PIPA 준수

**개인정보 보호법 준수 사항**:

1. **✅ 동의 기반 수집**
   ```python
   user = UserManager.create_user(
       db, 
       user_id="...", 
       consent=True  # 동의 필수
   )
   ```

2. **✅ 익명화**
   ```python
   # 실제 식별자를 SHA-256 해시로 변환
   user_id = hashlib.sha256("user@example.com".encode()).hexdigest()
   # → "a1b2c3d4..." (64자 해시)
   ```

3. **✅ PII 마스킹**
   ```python
   # 대화 저장 전 자동 마스킹
   원본: "제 전화번호는 010-1234-5678입니다"
   저장: "제 전화번호는 [전화번호]입니다"
   ```

4. **✅ 암호화 저장** (권장)
   ```python
   # 민감 정보는 암호화하여 저장
   from cryptography.fernet import Fernet
   
   key = Fernet.generate_key()
   cipher = Fernet(key)
   
   encrypted_name = cipher.encrypt("김철수".encode())
   ```

5. **✅ 보관 기간 제한**
   ```python
   # 90일 후 자동 삭제
   user.data_retention_days = 90
   
   # 정기적으로 오래된 데이터 삭제
   from src.database import cleanup_old_data
   cleanup_old_data(db, retention_days=90)
   ```

6. **✅ 동의 철회 시 즉시 삭제**
   ```python
   user.consent_given = False
   db.commit()
   
   # 다음 정리 시 자동 삭제
   cleanup_old_data(db)
   ```

### 보안 권장사항

**프로덕션 배포 시**:

1. **PostgreSQL 사용 (SQLite 대신)**
   ```bash
   DATABASE_URL=postgresql://user:password@localhost:5432/mental_health
   ```

2. **암호화 키 관리**
   ```bash
   # 환경 변수로 관리
   export DB_ENCRYPTION_KEY="..."
   
   # 또는 AWS KMS, Vault 사용
   ```

3. **접근 제어**
   ```bash
   # 데이터베이스 접근 제한
   - VPN 필수
   - IP 화이트리스트
   - 방화벽 설정
   ```

4. **백업 및 복구**
   ```bash
   # 정기 백업
   pg_dump mental_health > backup.sql
   
   # 암호화 백업
   pg_dump mental_health | gpg -c > backup.sql.gpg
   ```

---

## API 통합

### FastAPI 통합 예제

```python
# src/api.py 업데이트 예시

from src.personalization import PersonalizationManager

pm = PersonalizationManager()

@app.post("/api/v1/chat")
async def chat(chat_request: ChatRequest):
    # 1. 사용자 식별/생성
    user_id, is_new = pm.get_or_create_user(
        user_identifier=request.headers.get("X-User-ID"),
        consent=True
    )
    
    # 2. 개인화된 인사말
    if is_new or not chat_request.message:
        greeting = pm.get_personalized_greeting(user_id, is_new)
        return {"response": greeting}
    
    # 3. 사용자 맥락 조회
    context = pm.generate_personalized_context(user_id)
    
    # 4. LLM 응답 생성 (맥락 포함)
    response = llm.generate_response(
        chat_request.message,
        context=context  # 개인화된 맥락
    )
    
    # 5. 대화 저장
    pm.save_conversation_turn(
        user_id=user_id,
        session_id=chat_request.session_id,
        role="user",
        content=chat_request.message
    )
    
    pm.save_conversation_turn(
        user_id=user_id,
        session_id=chat_request.session_id,
        role="assistant",
        content=response
    )
    
    return {"response": response}
```

---

## 데이터베이스 초기화

### SQLite (기본값)

```bash
# 자동으로 생성됨
python -c "from src.database import get_db_manager; get_db_manager()"

# 확인
ls -lh ./data/mental_health.db
```

### PostgreSQL (프로덕션)

```bash
# 1. PostgreSQL 설치 및 시작
sudo apt-get install postgresql
sudo systemctl start postgresql

# 2. 데이터베이스 생성
sudo -u postgres psql
CREATE DATABASE mental_health;
CREATE USER mh_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE mental_health TO mh_user;

# 3. .env 설정
echo "DATABASE_URL=postgresql://mh_user:secure_password@localhost:5432/mental_health" >> .env

# 4. 테이블 생성
python -c "from src.database import get_db_manager; get_db_manager()"
```

---

## 마이그레이션 (선택사항)

### Alembic 사용

```bash
# 초기화
alembic init alembic

# 마이그레이션 생성
alembic revision --autogenerate -m "Add user tables"

# 마이그레이션 실행
alembic upgrade head
```

---

## 예제 시나리오

### 시나리오 1: 신규 사용자

```python
# Day 1
user: "안녕하세요"
assistant: "안녕하세요, 손님! 반갑습니다. 편안하게 이야기 나눠봐요."

user: "제 이름은 김철수입니다. 28살 회사원이에요."
assistant: "반갑습니다, 철수님! 어떤 점이 힘드셔서 찾아오셨나요?"
# [시스템: 이름 "김철수", 나이 28, 직업 "회사원" 자동 저장]

user: "직장 스트레스가 심해요"
assistant: "직장에서 어떤 부분이 가장 스트레스를 주시나요?"
# [시스템: 고민 "직장 스트레스" 저장]
```

### 시나리오 2: 재방문 사용자

```python
# Day 2 (다음 날)
user: "안녕하세요"
assistant: "어제 이후 처음이시네요, 철수님! 오늘은 어떠신가요?"
# [시스템: 이름 "철수님" 기억, 마지막 방문 시간 확인]

user: "어제보다는 좀 나아요"
assistant: "다행이네요! 어제 말씀하신 직장 스트레스는 좀 나아지셨나요?"
# [시스템: 이전 대화의 주요 고민 "직장 스트레스" 기억]
```

### 시나리오 3: 평가 추이 추적

```python
# Week 1
user: "PHQ-9 검사 받고 싶어요"
assistant: [PHQ-9 실시]
result: 점수 18 (중증 우울)

# Week 3
user: "다시 검사 받을게요"
assistant: [PHQ-9 실시]
result: 점수 12 (중등도 우울)
assistant: "철수님, 지난번 평가에 비해 점수가 18점에서 12점으로 낮아졌네요! 
          증상이 개선되고 있습니다. 계속 이렇게 잘 하고 계세요."
# [시스템: 평가 이력 비교, 추이 분석]
```

---

## 문제 해결

### Q1: 데이터베이스 파일이 생성되지 않음

```bash
# data 디렉토리 권한 확인
mkdir -p ./data
chmod 755 ./data

# 수동 생성
python -c "from src.database import get_db_manager; get_db_manager()"
```

### Q2: 이름이 추출되지 않음

```python
# 지원되는 패턴 확인
from src.ner_extractor import KoreanNERExtractor

ner = KoreanNERExtractor()
print(ner.NAME_PATTERNS)

# 테스트
name = ner.extract_name("제 이름은 홍길동입니다")
print(name)  # "홍길동" 출력되어야 함
```

### Q3: 마스킹이 작동하지 않음

```python
# PrivacyMasker 테스트
from src.logging_system import PrivacyMasker

masker = PrivacyMasker()
text = "제 전화번호는 010-1234-5678입니다"
masked = masker.mask_pii(text)
print(masked)  # "제 전화번호는 [전화번호]입니다"
```

---

## 리소스

- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [PIPA 개인정보보호법](https://www.privacy.go.kr/)
- [데이터베이스 설계 모범 사례](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)

---

**문서 버전**: 1.0.0  
**마지막 업데이트**: 2024-01-15
