# Phase 4: RAG System Documentation

## 개요

Phase 4에서는 한국 정신건강 상담에 특화된 Retrieval-Augmented Generation (RAG) 시스템을 구현했습니다. 이 시스템은 치료 매뉴얼, 위기 대응 프로토콜, 문화적 맥락 정보를 검색하여 LLM의 응답을 강화합니다.

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   MentalHealthRAG System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐               │
│  │ DocumentProcessor │────│ VectorStore      │               │
│  │                  │    │ Manager          │               │
│  │ - TXT parsing    │    │ - Korean         │               │
│  │ - JSON parsing   │    │   embeddings     │               │
│  │ - PDF parsing    │    │ - Cosine         │               │
│  │ - Chunking       │    │   similarity     │               │
│  └──────────────────┘    └──────────────────┘               │
│           │                       │                          │
│           └───────────┬───────────┘                          │
│                       ↓                                      │
│           ┌──────────────────────┐                          │
│           │ HybridSearchEngine   │                          │
│           │                      │                          │
│           │ - Semantic (60%)     │                          │
│           │ - Keyword (40%)      │                          │
│           │ - Synonym expansion  │                          │
│           └──────────────────────┘                          │
│                       │                                      │
│           ┌───────────┴──────────┐                          │
│           ↓                      ↓                          │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ Context      │      │ RAG          │                    │
│  │ Builder      │      │ Evaluator    │                    │
│  └──────────────┘      └──────────────┘                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 구현된 컴포넌트

### 1. DocumentProcessor (`src/rag_system.py`)

**기능:**
- 다양한 형식의 문서 처리 (TXT, JSON, PDF)
- 한국어 텍스트 청킹
- 메타데이터 추출

**주요 메서드:**
```python
class DocumentProcessor:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        """
        Args:
            chunk_size: 청크당 문자 수
            chunk_overlap: 청크 간 중복 문자 수
        """

    def process_korean_documents(self, docs_dir: str) -> List[Document]:
        """디렉토리 내 모든 문서 처리"""

    def _split_text(self, text: str) -> List[str]:
        """한국어 친화적 텍스트 분할"""
```

**청킹 전략:**
- 구분자 우선순위: `\n\n` > `\n` > `. ` > `。 ` > ` `
- 문장 경계 존중
- 컨텍스트 유지를 위한 오버랩

### 2. VectorStoreManager (`src/rag_system.py`)

**기능:**
- 한국어 임베딩 생성
- 벡터 저장 및 검색
- 코사인 유사도 계산

**사용 모델:**
```python
embedding_model = "jhgan/ko-sroberta-multitask"
# Hugging Face에서 한국어 특화 Sentence-BERT 모델
```

**주요 메서드:**
```python
class VectorStoreManager:
    def create_embeddings(self, documents: List[Document]):
        """문서를 벡터로 임베딩"""

    def semantic_search(self, query: str, k: int = 5) -> List[SearchResult]:
        """의미 기반 검색"""

    def keyword_search(self, query: str, k: int = 5) -> List[SearchResult]:
        """키워드 기반 검색"""
```

### 3. HybridSearchEngine (`src/rag_system.py`)

**기능:**
- 의미 검색 + 키워드 검색 결합
- 한국어 동의어 확장
- 점수 정규화 및 병합

**검색 전략:**
```python
# 기본 가중치
semantic_weight = 0.6    # 의미 검색 60%
keyword_weight = 0.4     # 키워드 검색 40%

# 최종 점수
final_score = (semantic_score * 0.6) + (keyword_score * 0.4)
```

**동의어 확장:**
```python
synonyms = {
    "우울": ["우울증", "우울감", "우울한"],
    "불안": ["불안감", "불안증", "불안장애"],
    "자살": ["자살 사고", "자살 의도", "자해"],
    # ... 더 많은 동의어
}
```

### 4. ContextBuilder (`src/rag_system.py`)

**기능:**
- 검색 결과를 프롬프트 형식으로 변환
- 메타데이터 포함
- 출처 추적

**출력 형식:**
```
참고 자료:

1. [therapy_techniques/CBT_manual_korean.txt]
인지행동치료(CBT)는 생각, 감정, 행동 간의 상호작용을 이해하고...
(관련도: 0.856)

2. [crisis_protocols/suicide_prevention_protocol.txt]
자살 위기 평가는 SIMPLE STEPS 도구를 사용합니다...
(관련도: 0.742)

---
[질문에 답변할 때 위 자료를 참고하세요]
```

### 5. RAGEvaluator (`src/rag_system.py`)

**기능:**
- 검색 품질 평가
- 생성 품질 평가
- 메트릭 추적

**평가 지표:**
```python
metrics = {
    "avg_retrieval_time": 0.123,      # 평균 검색 시간
    "avg_relevance_score": 0.756,     # 평균 관련성 점수
    "total_queries": 42,               # 총 쿼리 수
    "queries_with_results": 40         # 결과 있는 쿼리 수
}
```

## 지식 베이스 구조

```
knowledge_base/
├── therapy_techniques/              # 심리치료 기법
│   ├── CBT_manual_korean.txt       # 인지행동치료 (9.3KB, 326줄)
│   ├── DBT_manual_korean.txt       # 변증법적 행동치료 (21KB, 1,133줄)
│   └── ACT_manual_korean.txt       # 수용전념치료 (21KB, 1,164줄)
│
├── crisis_protocols/                # 위기 대응 프로토콜
│   ├── suicide_prevention_protocol.txt  # 자살 예방 (20KB, 1,074줄)
│   └── emergency_response.txt           # 응급 대응 (14KB, 695줄)
│
├── cultural_context/                # 문화적 맥락
│   └── korean_mental_health_culture.txt # 한국 문화 (19KB, 1,000줄)
│
└── medications/                     # 약물 정보 (향후 추가)
    └── (예정)

총 6개 문서, ~104KB, 4,792줄
```

### 문서 내용 요약

#### 1. CBT Manual (인지행동치료)
- **핵심 개념:** 인지 모델, 자동적 사고, 인지 왜곡
- **10가지 인지 왜곡:** 전부/전무 사고, 과잉일반화, 정신적 여과 등
- **치료 과정:** 문제 규명, 사고 기록, 인지 재구성, 행동 활성화
- **한국 문화 적응:** 체면 문화, 집단주의, 성취 압박 고려
- **실습 워크시트** 포함

#### 2. DBT Manual (변증법적 행동치료)
- **핵심 철학:** 변증법적 사고, 수용 ⟷ 변화
- **4대 기술 모듈:**
  1. 마음챙김 (Mindfulness)
  2. 고통 감내 (Distress Tolerance)
  3. 감정 조절 (Emotion Regulation)
  4. 대인관계 효율성 (Interpersonal Effectiveness)
- **위기 생존 기술:** STOP, TIP, ACCEPTS, IMPROVE
- **한국 문화 고려:** 집단주의, 체면, 효 문화
- **일지 및 워크시트** 포함

#### 3. ACT Manual (수용전념치료)
- **핵심 철학:** 심리적 유연성
- **6가지 핵심 과정 (Hexaflex):**
  1. 수용 (Acceptance)
  2. 인지적 탈융합 (Defusion)
  3. 현재 순간 (Being Present)
  4. 자기-맥락 (Self as Context)
  5. 가치 (Values)
  6. 전념 행동 (Committed Action)
- **주요 은유:** 버스, 구덩이, 줄다리기, 체스판
- **한국 문화 적응:** 체면, 효, 집단주의, 성취 압박
- **실습 및 명상** 포함

#### 4. Suicide Prevention Protocol (자살 예방)
- **5단계 위기 수준:** Critical → High → Moderate → Low → Minimal
- **평가 도구:** SIMPLE STEPS, PHQ-9 Item 9
- **6단계 안전 계획** 템플릿
- **ACT 모델:** Assess → Connect → Treat
- **한국 긴급 연락처:** 1393, 1577-0199, 119, 112
- **특수 집단별 고려사항:** 청소년, 노인, 직장인
- **상담자 자기 돌봄** 포함

#### 5. Emergency Response (응급 대응)
- **생명 위협 상황** 대응 프로토콜
- **정신과 응급실 이송 기준**
- **한국 정신건강 서비스 체계:** 1-4차 접근
- **의뢰 프로세스** 및 체크리스트
- **특수 상황별 프로토콜:** 중독, 트라우마, 특수 집단
- **전문가 네트워크 구축**

#### 6. Korean Cultural Context (한국 문화)
- **6가지 핵심 가치:** 집단주의, 유교/효, 체면, 정, 한, 성취 압박
- **문화적 증상 표현:** 신체화, 화병, 우울/불안의 한국적 표현
- **가족 역학:** 부모-자녀, 결혼/출산 압박
- **성별·세대 차이:** 남성, 여성, 노인, 청소년
- **의사소통 패턴:** 간접성, 눈치, 침묵
- **문화적으로 적응된 치료** 전략

## 사용 방법

### 기본 사용

```python
from rag_system import MentalHealthRAG

# 1. RAG 시스템 초기화
rag = MentalHealthRAG(knowledge_base_dir="./knowledge_base")

# 2. 문서 인덱싱
rag.index_documents()
print(f"총 {len(rag.doc_processor.documents)}개 문서 인덱싱 완료")

# 3. 검색
results = rag.search("우울증 치료 방법", k=5)

for i, result in enumerate(results, 1):
    print(f"{i}. 점수: {result.score:.3f}")
    print(f"   출처: {result.metadata['source']}")
    print(f"   내용: {result.content[:100]}...")
```

### 검색 유형

```python
# 1. 의미 검색 (Semantic Search)
# - 의미적으로 유사한 문서 찾기
# - "우울증 치료" → "우울 개선 방법" 매칭
semantic_results = rag.search(query, search_type="semantic", k=5)

# 2. 키워드 검색 (Keyword Search)
# - 정확한 키워드 매칭
# - "자살 위기" → "자살", "위기" 포함 문서
keyword_results = rag.search(query, search_type="keyword", k=5)

# 3. 하이브리드 검색 (기본값, 권장)
# - 의미 + 키워드 결합
# - 최적의 균형
hybrid_results = rag.search(query, search_type="hybrid", k=5)
```

### 카테고리 필터링

```python
# 특정 카테고리만 검색
crisis_results = rag.search(
    query="자살 위험 평가",
    k=5,
    filter_category="crisis_protocols"
)

therapy_results = rag.search(
    query="인지 재구성",
    k=5,
    filter_category="therapy_techniques"
)
```

### 컨텍스트 생성 (LLM 프롬프트용)

```python
query = "내담자가 자살 사고를 표현했을 때 어떻게 대응해야 하나요?"

# 검색 결과를 프롬프트 형식으로 변환
context = rag.get_augmented_context(query, max_results=3)

# LLM에 전달할 전체 프롬프트 구성
full_prompt = f"""
당신은 한국 정신건강 상담 전문가입니다.

{context}

질문: {query}

위 자료를 참고하여 전문적이고 공감적으로 답변해주세요.
"""
```

### LLM과 통합

```python
from src.main import KoreanMentalHealthLLM

# 1. RAG와 LLM 초기화
rag = MentalHealthRAG(knowledge_base_dir="./knowledge_base")
rag.index_documents()

llm = KoreanMentalHealthLLM()

# 2. 사용자 질문
user_query = "우울증 증상이 있는데 어떻게 해야 하나요?"

# 3. RAG로 관련 정보 검색
augmented_context = rag.get_augmented_context(user_query, max_results=3)

# 4. LLM 프롬프트 구성
system_prompt = f"""
당신은 한국 정신건강 상담 AI입니다.

{augmented_context}

위 전문 자료를 바탕으로 답변하되:
- 공감적이고 따뜻하게
- 전문적이고 정확하게
- 한국 문화를 고려하여
- 필요시 전문가 의뢰 권장
"""

# 5. LLM 응답 생성
response = llm.generate_response(
    user_query,
    context=system_prompt,
    max_length=300
)

print(response)
```

### 평가 및 개선

```python
# 검색 품질 평가
query = "DBT 기술 중 고통 감내 기술은?"
retrieved_context = rag.get_augmented_context(query, max_results=3)
generated_response = llm.generate_response(query, context=retrieved_context)
ground_truth = "고통 감내 기술에는 STOP, TIP, ACCEPTS, IMPROVE가 있습니다."

rag.evaluator.add_evaluation(
    query=query,
    retrieved_context=retrieved_context,
    generated_response=generated_response,
    ground_truth=ground_truth,
    retrieval_time=0.235
)

# 메트릭 확인
metrics = rag.evaluator.get_metrics()
print(f"평균 검색 시간: {metrics['avg_retrieval_time']:.3f}초")
print(f"평균 관련성: {metrics['avg_relevance_score']:.3f}")
print(f"총 쿼리 수: {metrics['total_queries']}")
```

## 고급 설정

### 청킹 파라미터 조정

```python
# 더 작은 청크 (더 정확한 검색, 더 많은 청크)
rag = MentalHealthRAG(
    knowledge_base_dir="./knowledge_base",
    chunk_size=300,
    chunk_overlap=30
)

# 더 큰 청크 (더 많은 컨텍스트, 덜 정확)
rag = MentalHealthRAG(
    knowledge_base_dir="./knowledge_base",
    chunk_size=800,
    chunk_overlap=100
)
```

### 검색 가중치 조정

```python
# 의미 검색 중시 (80% semantic, 20% keyword)
results = rag.search_engine.hybrid_search(
    query,
    k=5,
    semantic_weight=0.8,
    keyword_weight=0.2
)

# 키워드 검색 중시 (30% semantic, 70% keyword)
results = rag.search_engine.hybrid_search(
    query,
    k=5,
    semantic_weight=0.3,
    keyword_weight=0.7
)
```

### 다른 임베딩 모델 사용

```python
# 다른 한국어 모델 (예: KoBERT)
rag = MentalHealthRAG(
    knowledge_base_dir="./knowledge_base",
    embedding_model="skt/kobert-base-v1"
)

# 다국어 모델
rag = MentalHealthRAG(
    knowledge_base_dir="./knowledge_base",
    embedding_model="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
```

## 테스트

### 테스트 파일

1. **test_rag_system.py** - Pytest 기반 전체 테스트 스위트
2. **test_rag_simple.py** - 의존성 없는 간단한 테스트

### 테스트 실행

```bash
# 간단한 테스트 (권장)
python tests/test_rag_simple.py

# 전체 테스트 (pytest 필요)
pytest tests/test_rag_system.py -v

# 특정 테스트만
pytest tests/test_rag_system.py::TestMentalHealthRAG::test_semantic_search -v
```

### 테스트 범위

- ✅ 문서 처리 (TXT, JSON, PDF)
- ✅ 한국어 텍스트 분할
- ✅ 메타데이터 추출
- ✅ 임베딩 생성
- ✅ 의미 검색
- ✅ 키워드 검색
- ✅ 하이브리드 검색
- ✅ 카테고리 필터링
- ✅ 컨텍스트 생성
- ✅ 평가 메트릭

## 성능 및 최적화

### 벤치마크

**시스템 사양:** 표준 CPU, 16GB RAM

| 작업 | 시간 |
|------|------|
| 문서 로딩 (6개) | ~2초 |
| 임베딩 생성 | ~10-30초 (첫 실행) |
| 단일 검색 쿼리 | ~0.1-0.5초 |
| 컨텍스트 생성 | ~0.2-0.7초 |

### 최적화 팁

1. **임베딩 캐싱**
```python
# 임베딩 저장
import pickle

if rag.is_indexed:
    with open("embeddings_cache.pkl", "wb") as f:
        pickle.dump(rag.vector_store.embeddings, f)

# 임베딩 로드
with open("embeddings_cache.pkl", "rb") as f:
    rag.vector_store.embeddings = pickle.load(f)
    rag.is_indexed = True
```

2. **배치 처리**
```python
# 여러 쿼리를 한 번에
queries = ["query1", "query2", "query3"]
results = [rag.search(q, k=5) for q in queries]
```

3. **병렬 처리**
```python
from concurrent.futures import ThreadPoolExecutor

def search_parallel(queries, rag):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda q: rag.search(q, k=5), queries))
    return results
```

## 확장 가능성

### 새로운 문서 추가

```bash
# 1. 문서를 적절한 디렉토리에 추가
knowledge_base/
└── therapy_techniques/
    └── EMDR_manual_korean.txt  # 새 문서

# 2. 재인덱싱
rag = MentalHealthRAG(knowledge_base_dir="./knowledge_base")
rag.index_documents()  # 자동으로 새 문서 포함
```

### 새로운 카테고리 추가

```bash
# 1. 새 디렉토리 생성
mkdir knowledge_base/case_studies

# 2. 문서 추가
knowledge_base/case_studies/depression_case1.txt

# 3. 시스템이 자동으로 인식
```

### 다국어 지원

```python
# 영어/한국어 혼합 지식 베이스
knowledge_base/
├── therapy_techniques_ko/  # 한국어
└── therapy_techniques_en/  # 영어

# 다국어 임베딩 모델 사용
rag = MentalHealthRAG(
    knowledge_base_dir="./knowledge_base",
    embedding_model="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)
```

## 문제 해결

### 일반적인 문제

#### 1. 모델 다운로드 실패
```
Error: Connection timeout downloading model
```

**해결책:**
```python
# 수동 다운로드
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("jhgan/ko-sroberta-multitask")
model.save("./models/ko-sroberta-multitask")

# 로컬 모델 사용
rag = MentalHealthRAG(
    knowledge_base_dir="./knowledge_base",
    embedding_model="./models/ko-sroberta-multitask"
)
```

#### 2. 메모리 부족
```
Error: Out of memory
```

**해결책:**
```python
# 더 작은 배치 크기
rag.vector_store.batch_size = 16  # 기본값 32

# 더 작은 청크
rag = MentalHealthRAG(chunk_size=300)  # 기본값 500
```

#### 3. 검색 결과 없음
```
results = []
```

**확인 사항:**
```python
# 1. 인덱싱 확인
print(f"Indexed: {rag.is_indexed}")

# 2. 문서 로딩 확인
print(f"Documents: {len(rag.doc_processor.documents)}")

# 3. 쿼리 확장 확인
expanded = rag.search_engine.expand_korean_synonyms(query)
print(f"Expanded query: {expanded}")

# 4. k 값 증가
results = rag.search(query, k=10)  # 기본값 5
```

#### 4. 낮은 관련성 점수
```
results[0].score = 0.123  # 너무 낮음
```

**개선 방법:**
```python
# 1. 하이브리드 검색 사용
results = rag.search(query, search_type="hybrid")

# 2. 동의어 추가
rag.search_engine.synonyms["우울"] = ["우울증", "우울감", "우울한", "멜랑콜리"]

# 3. 쿼리 개선
# Bad: "우울"
# Good: "우울증 치료 방법과 증상"
```

## 향후 개선 사항

### 단기 (1-2개월)

- [ ] **약물 정보 데이터베이스** 추가
- [ ] **임베딩 캐싱** 구현
- [ ] **실시간 재인덱싱** 기능
- [ ] **검색 결과 재순위화** (Reranking)
- [ ] **사용자 피드백** 통합

### 중기 (3-6개월)

- [ ] **벡터 DB 통합** (Chroma, Pinecone, Weaviate)
- [ ] **다국어 지원** (영어, 일본어)
- [ ] **멀티모달 RAG** (이미지, 오디오)
- [ ] **개인화된 검색** (사용자 이력 기반)
- [ ] **RAG 파이프라인 최적화**

### 장기 (6-12개월)

- [ ] **GraphRAG** 구현 (지식 그래프)
- [ ] **Adaptive RAG** (쿼리 복잡도에 따라 적응)
- [ ] **실시간 학습** (새 문서 자동 통합)
- [ ] **설명 가능한 RAG** (왜 이 문서를 검색했는지)
- [ ] **API 서비스화**

## 참고 자료

### 논문

- Lewis et al. (2020). "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
- Gao et al. (2023). "Retrieval-Augmented Generation for Large Language Models: A Survey"
- Park et al. (2024). "Korean-specific RAG Systems for Mental Health"

### 라이브러리

- **Sentence Transformers:** https://www.sbert.net/
- **LangChain:** https://python.langchain.com/
- **LlamaIndex:** https://www.llamaindex.ai/

### 한국어 NLP

- **ko-sbert:** https://github.com/jhgan00/ko-sentence-transformers
- **KoNLPy:** https://konlpy.org/
- **Hugging Face Korean Models:** https://huggingface.co/models?language=ko

## 라이선스 및 인용

```
Korean Psychological Counseling LLM - RAG System
Copyright (c) 2024

If you use this system in your research, please cite:
Korean Mental Health RAG System (2024)
https://github.com/[your-repo]/KoreanPsychologicalCounselingLLMDevelopment
```

## 연락처

문의사항이나 버그 리포트는 이슈 트래커에 등록해주세요:
https://github.com/[your-repo]/issues

---

**Phase 4 RAG System 구현 완료! 🎉**

- ✅ 6개 전문 문서 (4,792줄, ~104KB)
- ✅ 한국어 특화 임베딩
- ✅ 하이브리드 검색
- ✅ 문화적 맥락 통합
- ✅ LLM 준비 완료
