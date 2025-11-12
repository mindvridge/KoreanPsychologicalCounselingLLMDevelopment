"""
RAG 시스템 - 심리학 지식 기반
Retrieval-Augmented Generation System for Mental Health Knowledge

한국어 심리학 문서를 처리하고, 치료 기법 및 위기 대응 지식을 검색합니다.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from collections import Counter

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


# ============================================================================
# 데이터 클래스
# ============================================================================

@dataclass
class Document:
    """문서 데이터 클래스"""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    doc_id: str = field(default_factory=lambda: str(datetime.now().timestamp()))

    def __post_init__(self):
        """메타데이터 기본값 설정"""
        if "source" not in self.metadata:
            self.metadata["source"] = "unknown"
        if "chunk_index" not in self.metadata:
            self.metadata["chunk_index"] = 0


@dataclass
class SearchResult:
    """검색 결과 데이터 클래스"""
    document: Document
    score: float
    relevance: str  # "high", "medium", "low"
    search_type: str  # "semantic", "keyword", "hybrid"


# ============================================================================
# 문서 처리 파이프라인
# ============================================================================

class DocumentProcessor:
    """
    한국어 심리학 문서 처리기

    지원 형식: TXT, JSON, PDF (추가 라이브러리 필요)
    한국어 특화 처리 포함
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        """
        초기화

        Args:
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 간 겹침 크기
            separators: 텍스트 분할 구분자
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "。 ", " "]

        logger.info(
            f"DocumentProcessor initialized: chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}"
        )

    def process_file(self, file_path: str, metadata: Optional[Dict] = None) -> List[Document]:
        """
        파일 처리

        Args:
            file_path: 파일 경로
            metadata: 메타데이터

        Returns:
            List[Document]: 처리된 문서 리스트
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 파일 형식별 처리
        if file_path.suffix == ".txt":
            text = self._read_txt(file_path)
        elif file_path.suffix == ".json":
            text = self._read_json(file_path)
        elif file_path.suffix == ".pdf":
            text = self._read_pdf(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {file_path.suffix}")

        # 메타데이터 구성
        if metadata is None:
            metadata = {}

        metadata.update({
            "source": str(file_path),
            "file_type": file_path.suffix[1:],
            "processed_at": datetime.now().isoformat()
        })

        # 청크 분할
        chunks = self.split_text(text)

        # Document 객체 생성
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)

            doc = Document(
                content=chunk,
                metadata=chunk_metadata
            )
            documents.append(doc)

        logger.info(f"파일 처리 완료: {file_path.name}, {len(documents)}개 청크")

        return documents

    def _read_txt(self, file_path: Path) -> str:
        """TXT 파일 읽기"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _read_json(self, file_path: Path) -> str:
        """JSON 파일 읽기 및 텍스트 추출"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # JSON 구조를 텍스트로 변환
        if isinstance(data, dict):
            text_parts = []
            for key, value in data.items():
                if isinstance(value, (str, int, float)):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    text_parts.append(f"{key}: {', '.join(map(str, value))}")
            return "\n".join(text_parts)
        elif isinstance(data, list):
            return "\n".join(map(str, data))
        else:
            return str(data)

    def _read_pdf(self, file_path: Path) -> str:
        """
        PDF 파일 읽기 (PyPDF2 필요)

        Note: PyPDF2가 설치되지 않은 경우 에러 메시지 반환
        """
        try:
            import PyPDF2

            text_parts = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())

            return "\n\n".join(text_parts)

        except ImportError:
            logger.warning("PyPDF2가 설치되지 않았습니다. pip install PyPDF2")
            return f"[PDF 파일: {file_path.name}] - PyPDF2 라이브러리 필요"

    def split_text(self, text: str) -> List[str]:
        """
        텍스트를 청크로 분할

        Args:
            text: 입력 텍스트

        Returns:
            List[str]: 청크 리스트
        """
        chunks = []
        current_chunk = ""

        # 구분자로 분할
        for separator in self.separators:
            if separator in text:
                parts = text.split(separator)

                for part in parts:
                    if len(current_chunk) + len(part) <= self.chunk_size:
                        current_chunk += part + separator
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())

                        # 오버랩 처리
                        if chunks and self.chunk_overlap > 0:
                            overlap_text = current_chunk[-self.chunk_overlap:]
                            current_chunk = overlap_text + part + separator
                        else:
                            current_chunk = part + separator

                # 마지막 청크
                if current_chunk:
                    chunks.append(current_chunk.strip())

                break

        # 구분자를 찾지 못한 경우 단순 분할
        if not chunks:
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk = text[i:i + self.chunk_size]
                if chunk.strip():
                    chunks.append(chunk.strip())

        return chunks

    def process_korean_documents(self, docs_dir: str) -> List[Document]:
        """
        디렉토리 내 모든 한국어 문서 처리

        Args:
            docs_dir: 문서 디렉토리 경로

        Returns:
            List[Document]: 모든 문서 리스트
        """
        docs_path = Path(docs_dir)

        if not docs_path.exists():
            raise FileNotFoundError(f"디렉토리를 찾을 수 없습니다: {docs_dir}")

        all_documents = []

        # 지원 파일 형식
        supported_extensions = [".txt", ".json", ".pdf"]

        for file_path in docs_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in supported_extensions:
                try:
                    # 파일 경로에서 메타데이터 추출
                    metadata = self._extract_metadata_from_path(file_path)

                    # 문서 처리
                    documents = self.process_file(str(file_path), metadata)
                    all_documents.extend(documents)

                except Exception as e:
                    logger.error(f"파일 처리 오류 ({file_path}): {e}")

        logger.info(f"총 {len(all_documents)}개 문서 처리 완료")

        return all_documents

    def _extract_metadata_from_path(self, file_path: Path) -> Dict:
        """
        파일 경로에서 메타데이터 추출

        Args:
            file_path: 파일 경로

        Returns:
            Dict: 메타데이터
        """
        metadata = {}

        # 경로에서 카테고리 추출
        parts = file_path.parts

        if "therapy_techniques" in parts:
            metadata["category"] = "therapy_techniques"
        elif "crisis_protocols" in parts:
            metadata["category"] = "crisis_protocols"
        elif "cultural_context" in parts:
            metadata["category"] = "cultural_context"
        elif "medications" in parts:
            metadata["category"] = "medications"
        else:
            metadata["category"] = "general"

        # 파일명에서 치료법 추출
        filename = file_path.stem.lower()

        if "cbt" in filename or "인지행동" in filename:
            metadata["therapy_type"] = "CBT"
        elif "dbt" in filename or "변증법" in filename:
            metadata["therapy_type"] = "DBT"
        elif "act" in filename or "수용전념" in filename:
            metadata["therapy_type"] = "ACT"
        elif "mindfulness" in filename or "마음챙김" in filename:
            metadata["therapy_type"] = "Mindfulness"
        elif "psychodynamic" in filename or "정신역동" in filename:
            metadata["therapy_type"] = "Psychodynamic"

        return metadata


# ============================================================================
# 벡터 스토어 관리자
# ============================================================================

class VectorStoreManager:
    """
    벡터 스토어 관리자

    한국어 특화 임베딩 모델을 사용하여 문서를 벡터화하고 검색합니다.
    """

    def __init__(
        self,
        embedding_model: str = "jhgan/ko-sroberta-multitask",
        persist_directory: str = "./mental_health_vectors"
    ):
        """
        초기화

        Args:
            embedding_model: 한국어 임베딩 모델 이름
            persist_directory: 벡터 저장 디렉토리
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)

        # 한국어 임베딩 모델 로드
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            logger.info(f"임베딩 모델 로드 완료: {embedding_model}")
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            logger.warning("대체 모델 사용: paraphrase-multilingual-MiniLM-L12-v2")
            self.embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

        # 문서 저장소
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None

        # 기존 데이터 로드
        self._load_from_disk()

    def add_documents(self, documents: List[Document]):
        """
        문서 추가 및 임베딩 생성

        Args:
            documents: 추가할 문서 리스트
        """
        if not documents:
            return

        # 문서 내용 추출
        texts = [doc.content for doc in documents]

        # 임베딩 생성
        new_embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            batch_size=32
        )

        # 문서에 임베딩 할당
        for doc, embedding in zip(documents, new_embeddings):
            doc.embedding = embedding

        # 저장소에 추가
        self.documents.extend(documents)

        # 전체 임베딩 업데이트
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

        logger.info(f"{len(documents)}개 문서 추가 완료 (총 {len(self.documents)}개)")

        # 디스크에 저장
        self._save_to_disk()

    def semantic_search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        의미적 검색

        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            threshold: 최소 유사도 임계값

        Returns:
            List[SearchResult]: 검색 결과
        """
        if not self.documents:
            logger.warning("문서가 없습니다")
            return []

        # 쿼리 임베딩
        query_embedding = self.embedding_model.encode([query])[0]

        # 코사인 유사도 계산
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # 상위 k개 인덱스
        top_indices = np.argsort(similarities)[::-1][:k]

        # SearchResult 생성
        results = []
        for idx in top_indices:
            similarity = similarities[idx]

            if similarity < threshold:
                continue

            # 관련성 판정
            if similarity >= 0.7:
                relevance = "high"
            elif similarity >= 0.5:
                relevance = "medium"
            else:
                relevance = "low"

            result = SearchResult(
                document=self.documents[idx],
                score=float(similarity),
                relevance=relevance,
                search_type="semantic"
            )

            results.append(result)

        return results

    def keyword_search(
        self,
        query: str,
        k: int = 5
    ) -> List[SearchResult]:
        """
        키워드 기반 검색

        Args:
            query: 검색 쿼리
            k: 반환할 결과 수

        Returns:
            List[SearchResult]: 검색 결과
        """
        if not self.documents:
            return []

        # 쿼리 토큰화 (간단한 공백 분리)
        query_tokens = set(query.lower().split())

        # 각 문서의 매칭 점수 계산
        scores = []

        for doc in self.documents:
            content_lower = doc.content.lower()
            doc_tokens = set(content_lower.split())

            # 토큰 매칭 점수
            matched_tokens = query_tokens & doc_tokens
            token_score = len(matched_tokens) / len(query_tokens) if query_tokens else 0

            # 부분 매칭 점수
            partial_matches = sum(1 for token in query_tokens if token in content_lower)
            partial_score = partial_matches / len(query_tokens) if query_tokens else 0

            # 최종 점수
            final_score = 0.6 * token_score + 0.4 * partial_score

            scores.append(final_score)

        # 상위 k개
        top_indices = np.argsort(scores)[::-1][:k]

        # SearchResult 생성
        results = []
        for idx in top_indices:
            score = scores[idx]

            if score == 0:
                continue

            # 관련성 판정
            if score >= 0.5:
                relevance = "high"
            elif score >= 0.3:
                relevance = "medium"
            else:
                relevance = "low"

            result = SearchResult(
                document=self.documents[idx],
                score=score,
                relevance=relevance,
                search_type="keyword"
            )

            results.append(result)

        return results

    def _save_to_disk(self):
        """벡터 및 문서를 디스크에 저장"""
        try:
            # 임베딩 저장
            if self.embeddings is not None:
                np.save(
                    os.path.join(self.persist_directory, "embeddings.npy"),
                    self.embeddings
                )

            # 문서 저장 (임베딩 제외)
            documents_data = []
            for doc in self.documents:
                doc_dict = {
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "doc_id": doc.doc_id
                }
                documents_data.append(doc_dict)

            with open(os.path.join(self.persist_directory, "documents.json"), 'w', encoding='utf-8') as f:
                json.dump(documents_data, f, ensure_ascii=False, indent=2)

            logger.info("벡터 스토어 저장 완료")

        except Exception as e:
            logger.error(f"벡터 스토어 저장 실패: {e}")

    def _load_from_disk(self):
        """디스크에서 벡터 및 문서 로드"""
        try:
            embeddings_path = os.path.join(self.persist_directory, "embeddings.npy")
            documents_path = os.path.join(self.persist_directory, "documents.json")

            if os.path.exists(embeddings_path) and os.path.exists(documents_path):
                # 임베딩 로드
                self.embeddings = np.load(embeddings_path)

                # 문서 로드
                with open(documents_path, 'r', encoding='utf-8') as f:
                    documents_data = json.load(f)

                self.documents = []
                for i, doc_dict in enumerate(documents_data):
                    doc = Document(
                        content=doc_dict["content"],
                        metadata=doc_dict["metadata"],
                        doc_id=doc_dict["doc_id"]
                    )
                    doc.embedding = self.embeddings[i]
                    self.documents.append(doc)

                logger.info(f"벡터 스토어 로드 완료: {len(self.documents)}개 문서")

        except Exception as e:
            logger.error(f"벡터 스토어 로드 실패: {e}")


# ============================================================================
# 하이브리드 검색 엔진
# ============================================================================

class HybridSearchEngine:
    """
    하이브리드 검색 엔진

    의미적 검색과 키워드 검색을 결합하여 최적의 결과를 제공합니다.
    """

    def __init__(self, vector_store: VectorStoreManager):
        """
        초기화

        Args:
            vector_store: 벡터 스토어 관리자
        """
        self.vector_store = vector_store

        # 한국어 동의어 사전
        self.korean_synonyms = {
            "우울": ["우울증", "우울감", "침울", "기분저하"],
            "불안": ["불안감", "초조", "긴장", "걱정"],
            "치료": ["치료법", "요법", "테라피", "상담"],
            "CBT": ["인지행동치료", "인지치료", "행동치료"],
            "ACT": ["수용전념치료", "수용치료"],
            "마음챙김": ["명상", "mindfulness", "마인드풀니스"]
        }

    def hybrid_search(
        self,
        query: str,
        k: int = 5,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ) -> List[SearchResult]:
        """
        하이브리드 검색

        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            semantic_weight: 의미적 검색 가중치
            keyword_weight: 키워드 검색 가중치

        Returns:
            List[SearchResult]: 검색 결과
        """
        # 동의어 확장
        expanded_query = self.expand_korean_synonyms(query)

        # 의미적 검색
        semantic_results = self.vector_store.semantic_search(expanded_query, k=k*2)

        # 키워드 검색
        keyword_results = self.vector_store.keyword_search(expanded_query, k=k*2)

        # 결과 병합 및 재순위화
        merged = self.merge_and_rank(
            semantic_results,
            keyword_results,
            semantic_weight,
            keyword_weight
        )

        return merged[:k]

    def expand_korean_synonyms(self, query: str) -> str:
        """
        한국어 동의어 확장

        Args:
            query: 원본 쿼리

        Returns:
            str: 확장된 쿼리
        """
        expanded_terms = [query]

        for term, synonyms in self.korean_synonyms.items():
            if term in query:
                expanded_terms.extend(synonyms)

        return " ".join(expanded_terms)

    def merge_and_rank(
        self,
        semantic_results: List[SearchResult],
        keyword_results: List[SearchResult],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[SearchResult]:
        """
        검색 결과 병합 및 재순위화

        Args:
            semantic_results: 의미적 검색 결과
            keyword_results: 키워드 검색 결과
            semantic_weight: 의미적 검색 가중치
            keyword_weight: 키워드 검색 가중치

        Returns:
            List[SearchResult]: 병합된 결과
        """
        # 문서 ID별 점수 집계
        doc_scores = {}

        for result in semantic_results:
            doc_id = result.document.doc_id
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "document": result.document,
                    "semantic_score": 0,
                    "keyword_score": 0
                }
            doc_scores[doc_id]["semantic_score"] = result.score

        for result in keyword_results:
            doc_id = result.document.doc_id
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    "document": result.document,
                    "semantic_score": 0,
                    "keyword_score": 0
                }
            doc_scores[doc_id]["keyword_score"] = result.score

        # 최종 점수 계산
        final_results = []

        for doc_id, scores in doc_scores.items():
            final_score = (
                semantic_weight * scores["semantic_score"] +
                keyword_weight * scores["keyword_score"]
            )

            # 관련성 판정
            if final_score >= 0.7:
                relevance = "high"
            elif final_score >= 0.5:
                relevance = "medium"
            else:
                relevance = "low"

            result = SearchResult(
                document=scores["document"],
                score=final_score,
                relevance=relevance,
                search_type="hybrid"
            )

            final_results.append(result)

        # 점수순 정렬
        final_results.sort(key=lambda x: x.score, reverse=True)

        return final_results


# ============================================================================
# 컨텍스트 빌더
# ============================================================================

class ContextBuilder:
    """
    RAG 컨텍스트 구성기

    검색 결과를 자연스러운 컨텍스트로 구성합니다.
    """

    def __init__(self, max_context_length: int = 2000):
        """
        초기화

        Args:
            max_context_length: 최대 컨텍스트 길이
        """
        self.max_context_length = max_context_length

    def build_augmented_context(
        self,
        query: str,
        search_results: List[SearchResult],
        conversation_history: Optional[List[Dict]] = None,
        min_score: float = 0.5
    ) -> str:
        """
        증강된 컨텍스트 구성

        Args:
            query: 검색 쿼리
            search_results: 검색 결과
            conversation_history: 대화 이력
            min_score: 최소 점수 임계값

        Returns:
            str: 구성된 컨텍스트
        """
        # 신뢰도 기반 필터링
        filtered_results = [
            r for r in search_results
            if r.score >= min_score
        ]

        if not filtered_results:
            return ""

        context_parts = ["## 참고 자료\n"]

        current_length = 0

        for i, result in enumerate(filtered_results, 1):
            doc = result.document

            # 출처 정보
            source = doc.metadata.get("source", "알 수 없음")
            therapy_type = doc.metadata.get("therapy_type", "")
            category = doc.metadata.get("category", "")

            # 컨텍스트 구성
            source_info = f"**[참고 {i}]** "

            if therapy_type:
                source_info += f"({therapy_type}) "

            source_info += f"{Path(source).name}"

            if category:
                source_info += f" - {category}"

            source_info += f" (관련도: {result.score:.2f})\n"

            content = f"{doc.content}\n\n"

            # 길이 체크
            new_length = current_length + len(source_info) + len(content)

            if new_length > self.max_context_length:
                break

            context_parts.append(source_info)
            context_parts.append(content)

            current_length = new_length

        # 대화 이력 요약 (옵션)
        if conversation_history:
            history_summary = self._summarize_conversation(conversation_history)
            context_parts.insert(1, f"\n## 대화 맥락\n{history_summary}\n\n")

        return "".join(context_parts)

    def _summarize_conversation(
        self,
        conversation_history: List[Dict],
        max_turns: int = 3
    ) -> str:
        """
        대화 이력 요약

        Args:
            conversation_history: 대화 이력
            max_turns: 최대 턴 수

        Returns:
            str: 요약된 대화
        """
        recent = conversation_history[-max_turns*2:] if len(conversation_history) > max_turns*2 else conversation_history

        summary_parts = []

        for turn in recent:
            role = "사용자" if turn.get("role") == "user" else "상담사"
            content = turn.get("content", "")[:100]  # 최대 100자

            summary_parts.append(f"- {role}: {content}")

        return "\n".join(summary_parts)


# ============================================================================
# RAG 평가기
# ============================================================================

class RAGEvaluator:
    """
    RAG 시스템 평가기

    검색 정확도, 응답 관련성 등을 평가합니다.
    """

    def __init__(self):
        """초기화"""
        self.metrics = {
            "search_accuracy": [],
            "response_relevance": [],
            "source_reliability": []
        }

    def evaluate_search_accuracy(
        self,
        query: str,
        results: List[SearchResult],
        ground_truth: Optional[List[str]] = None
    ) -> float:
        """
        검색 정확도 평가

        Args:
            query: 쿼리
            results: 검색 결과
            ground_truth: 정답 문서 ID 리스트

        Returns:
            float: 정확도 (0-1)
        """
        if not results:
            return 0.0

        if ground_truth:
            # 정답이 있는 경우 Precision 계산
            retrieved_ids = {r.document.doc_id for r in results}
            correct = sum(1 for doc_id in ground_truth if doc_id in retrieved_ids)
            precision = correct / len(results)

            self.metrics["search_accuracy"].append(precision)

            return precision
        else:
            # 정답이 없는 경우 평균 점수 반환
            avg_score = sum(r.score for r in results) / len(results)

            self.metrics["search_accuracy"].append(avg_score)

            return avg_score

    def evaluate_response_relevance(
        self,
        response: str,
        context: str
    ) -> float:
        """
        응답 관련성 평가

        Args:
            response: 생성된 응답
            context: 사용된 컨텍스트

        Returns:
            float: 관련성 (0-1)
        """
        # 간단한 토큰 오버랩 기반 평가
        response_tokens = set(response.lower().split())
        context_tokens = set(context.lower().split())

        if not response_tokens:
            return 0.0

        overlap = len(response_tokens & context_tokens)
        relevance = overlap / len(response_tokens)

        self.metrics["response_relevance"].append(relevance)

        return relevance

    def detect_hallucination(
        self,
        response: str,
        context: str,
        threshold: float = 0.3
    ) -> bool:
        """
        환각(hallucination) 감지

        Args:
            response: 생성된 응답
            context: 사용된 컨텍스트
            threshold: 임계값

        Returns:
            bool: 환각 감지 여부
        """
        relevance = self.evaluate_response_relevance(response, context)

        # 관련성이 임계값 미만이면 환각으로 판정
        return relevance < threshold

    def get_metrics_summary(self) -> Dict[str, float]:
        """
        평가 메트릭 요약

        Returns:
            Dict: 메트릭 요약
        """
        summary = {}

        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "count": len(values)
                }

        return summary


# ============================================================================
# 통합 RAG 시스템
# ============================================================================

class MentalHealthRAG:
    """
    심리학 지식 기반 RAG 시스템

    문서 처리, 벡터 검색, 컨텍스트 증강을 통합합니다.
    """

    def __init__(
        self,
        knowledge_base_dir: str = "./knowledge_base",
        persist_directory: str = "./mental_health_vectors"
    ):
        """
        초기화

        Args:
            knowledge_base_dir: 지식 베이스 디렉토리
            persist_directory: 벡터 저장 디렉토리
        """
        self.knowledge_base_dir = knowledge_base_dir
        self.persist_directory = persist_directory

        # 컴포넌트 초기화
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStoreManager(persist_directory=persist_directory)
        self.search_engine = HybridSearchEngine(self.vector_store)
        self.context_builder = ContextBuilder()
        self.evaluator = RAGEvaluator()

        logger.info("MentalHealthRAG 시스템 초기화 완료")

    def index_knowledge_base(self):
        """지식 베이스 인덱싱"""
        if not os.path.exists(self.knowledge_base_dir):
            logger.warning(f"지식 베이스 디렉토리가 없습니다: {self.knowledge_base_dir}")
            return

        # 모든 문서 처리
        documents = self.doc_processor.process_korean_documents(self.knowledge_base_dir)

        # 벡터 스토어에 추가
        self.vector_store.add_documents(documents)

        logger.info(f"지식 베이스 인덱싱 완료: {len(documents)}개 문서")

    def retrieve(
        self,
        query: str,
        k: int = 5,
        search_type: str = "hybrid"
    ) -> List[SearchResult]:
        """
        문서 검색

        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            search_type: 검색 유형 ("semantic", "keyword", "hybrid")

        Returns:
            List[SearchResult]: 검색 결과
        """
        if search_type == "semantic":
            results = self.vector_store.semantic_search(query, k=k)
        elif search_type == "keyword":
            results = self.vector_store.keyword_search(query, k=k)
        else:  # hybrid
            results = self.search_engine.hybrid_search(query, k=k)

        return results

    def augment(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None,
        k: int = 3
    ) -> str:
        """
        컨텍스트 증강

        Args:
            query: 쿼리
            conversation_history: 대화 이력
            k: 검색 결과 수

        Returns:
            str: 증강된 컨텍스트
        """
        # 검색
        results = self.retrieve(query, k=k, search_type="hybrid")

        # 컨텍스트 구성
        context = self.context_builder.build_augmented_context(
            query=query,
            search_results=results,
            conversation_history=conversation_history
        )

        return context

    def get_stats(self) -> Dict:
        """
        시스템 통계

        Returns:
            Dict: 통계 정보
        """
        return {
            "total_documents": len(self.vector_store.documents),
            "metrics": self.evaluator.get_metrics_summary()
        }


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    logger.info("=== RAG 시스템 테스트 ===\n")

    # RAG 시스템 초기화
    rag = MentalHealthRAG(
        knowledge_base_dir="./knowledge_base",
        persist_directory="./mental_health_vectors"
    )

    # 테스트 쿼리
    test_queries = [
        "CBT로 우울증을 치료하는 방법",
        "자살 위기 상황 대응 프로토콜",
        "한국인의 감정 표현 특성"
    ]

    for query in test_queries:
        print(f"쿼리: {query}")
        print("-" * 70)

        # 검색
        results = rag.retrieve(query, k=3, search_type="hybrid")

        print(f"검색 결과: {len(results)}개\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. 점수: {result.score:.3f} | 관련성: {result.relevance}")
            print(f"   출처: {result.document.metadata.get('source', 'unknown')}")
            print(f"   내용: {result.document.content[:100]}...")
            print()

        # 컨텍스트 증강
        context = rag.augment(query, k=3)
        print("증강된 컨텍스트:")
        print(context[:300] + "..." if len(context) > 300 else context)
        print("\n" + "=" * 70 + "\n")

    # 통계
    stats = rag.get_stats()
    print(f"시스템 통계: {stats}")
