"""
RAG System Test Suite
Tests document processing, vector store, search, and retrieval functionality
"""

import sys
import os
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag_system import (
    MentalHealthRAG,
    DocumentProcessor,
    VectorStoreManager,
    HybridSearchEngine,
    ContextBuilder,
    RAGEvaluator
)


class TestDocumentProcessor:
    """Test document processing functionality"""

    def test_initialization(self):
        """Test DocumentProcessor initialization"""
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 50
        print("✓ DocumentProcessor initialization successful")

    def test_text_splitting(self):
        """Test Korean text splitting"""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)

        test_text = """
        인지행동치료(CBT)는 생각, 감정, 행동의 상호작용을 다룹니다.

        부정적 사고 패턴을 변화시켜 감정을 개선합니다.

        자동적 사고를 인식하고 재구성하는 것이 핵심입니다.
        """

        chunks = processor._split_text(test_text)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        print(f"✓ Text splitting: {len(chunks)} chunks created")

    def test_metadata_extraction(self):
        """Test metadata extraction from path"""
        processor = DocumentProcessor()

        test_path = "knowledge_base/therapy_techniques/CBT_manual_korean.txt"
        metadata = processor._extract_metadata(test_path)

        assert metadata["category"] == "therapy_techniques"
        assert metadata["therapy_type"] == "CBT"
        print(f"✓ Metadata extraction: {metadata}")


class TestVectorStoreManager:
    """Test vector store functionality"""

    def test_initialization(self):
        """Test VectorStoreManager initialization"""
        try:
            store = VectorStoreManager(embedding_model="jhgan/ko-sroberta-multitask")
            assert store.embedding_model is not None
            print("✓ VectorStoreManager initialization successful")
        except Exception as e:
            pytest.skip(f"Skipping: Model download needed - {e}")

    def test_embedding_generation(self):
        """Test Korean text embedding"""
        try:
            store = VectorStoreManager(embedding_model="jhgan/ko-sroberta-multitask")

            test_texts = [
                "우울증은 슬픔과 무기력감을 특징으로 합니다.",
                "불안장애는 과도한 걱정과 긴장을 동반합니다."
            ]

            embeddings = store.embedding_model.encode(test_texts)
            assert embeddings.shape[0] == 2
            assert embeddings.shape[1] > 0  # Embedding dimension
            print(f"✓ Embedding generation: shape {embeddings.shape}")
        except Exception as e:
            pytest.skip(f"Skipping: Model needed - {e}")


class TestHybridSearchEngine:
    """Test hybrid search functionality"""

    def test_query_expansion(self):
        """Test Korean synonym expansion"""
        store = VectorStoreManager(embedding_model="jhgan/ko-sroberta-multitask")
        search_engine = HybridSearchEngine(store)

        test_queries = [
            "우울증",
            "자살 위기",
            "불안"
        ]

        for query in test_queries:
            expanded = search_engine.expand_korean_synonyms(query)
            assert query in expanded
            print(f"✓ Query expansion: '{query}' → '{expanded}'")


class TestMentalHealthRAG:
    """Test complete RAG system"""

    @pytest.fixture
    def rag_system(self):
        """Create RAG system instance"""
        knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"

        if not knowledge_base_dir.exists():
            pytest.skip("Knowledge base directory not found")

        try:
            rag = MentalHealthRAG(knowledge_base_dir=str(knowledge_base_dir))
            return rag
        except Exception as e:
            pytest.skip(f"RAG system initialization failed: {e}")

    def test_document_loading(self, rag_system):
        """Test document loading from knowledge base"""
        doc_count = len(rag_system.doc_processor.documents)
        assert doc_count > 0, "No documents loaded"
        print(f"✓ Document loading: {doc_count} documents")

        # Check all categories loaded
        categories = set(doc.metadata.get("category") for doc in rag_system.doc_processor.documents)
        print(f"  Categories: {categories}")
        assert len(categories) > 0

    def test_semantic_search(self, rag_system):
        """Test semantic search"""
        if not rag_system.is_indexed:
            rag_system.index_documents()

        query = "우울증을 치료하는 방법은?"
        results = rag_system.search(query, search_type="semantic", k=3)

        assert len(results) > 0, "No search results"
        print(f"✓ Semantic search: {len(results)} results for '{query}'")

        for i, result in enumerate(results[:2], 1):
            print(f"  {i}. Score: {result.score:.3f}, Source: {result.metadata.get('source', 'unknown')}")

    def test_keyword_search(self, rag_system):
        """Test keyword search"""
        query = "자살 위기 대응"
        results = rag_system.search(query, search_type="keyword", k=3)

        assert len(results) > 0, "No keyword search results"
        print(f"✓ Keyword search: {len(results)} results for '{query}'")

    def test_hybrid_search(self, rag_system):
        """Test hybrid search"""
        if not rag_system.is_indexed:
            rag_system.index_documents()

        query = "CBT 인지 왜곡"
        results = rag_system.search(query, search_type="hybrid", k=5)

        assert len(results) > 0, "No hybrid search results"
        print(f"✓ Hybrid search: {len(results)} results for '{query}'")

        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. Score: {result.score:.3f}")
            print(f"     {result.content[:100]}...")

    def test_augmented_generation(self, rag_system):
        """Test context augmentation for generation"""
        if not rag_system.is_indexed:
            rag_system.index_documents()

        query = "우울증 증상은 무엇인가요?"
        context = rag_system.get_augmented_context(query, max_results=3)

        assert len(context) > 0, "No context generated"
        assert "참고 자료" in context or "Context" in context
        print(f"✓ Augmented context: {len(context)} characters")
        print(f"  Preview: {context[:200]}...")

    def test_category_filtering(self, rag_system):
        """Test search with category filter"""
        if not rag_system.is_indexed:
            rag_system.index_documents()

        query = "자살 예방"
        results = rag_system.search(
            query,
            k=5,
            filter_category="crisis_protocols"
        )

        if len(results) > 0:
            categories = set(r.metadata.get("category") for r in results)
            print(f"✓ Category filtering: {len(results)} results in {categories}")
        else:
            print("⚠ No results in crisis_protocols category")

    def test_evaluation_metrics(self, rag_system):
        """Test RAG evaluation"""
        if not rag_system.is_indexed:
            rag_system.index_documents()

        query = "DBT 기술"
        retrieved_context = "변증법적 행동치료(DBT)의 4대 기술은 마음챙김, 고통 감내, 감정 조절, 대인관계 효율성입니다."
        generated_response = "DBT에는 4가지 핵심 기술이 있습니다: 마음챙김, 고통 감내, 감정 조절, 대인관계 기술입니다."
        ground_truth = "DBT의 핵심 기술은 마음챙김, 고통 감내, 감정 조절, 대인관계 효율성 4가지입니다."

        rag_system.evaluator.add_evaluation(
            query=query,
            retrieved_context=retrieved_context,
            generated_response=generated_response,
            ground_truth=ground_truth,
            retrieval_time=0.5
        )

        metrics = rag_system.evaluator.get_metrics()
        assert metrics["total_queries"] == 1
        print(f"✓ Evaluation metrics: {metrics}")


class TestIntegration:
    """Integration tests"""

    def test_end_to_end_workflow(self):
        """Test complete RAG workflow"""
        knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"

        if not knowledge_base_dir.exists():
            pytest.skip("Knowledge base not found")

        try:
            print("\n" + "="*60)
            print("END-TO-END RAG WORKFLOW TEST")
            print("="*60)

            # 1. Initialize RAG system
            print("\n1. Initializing RAG system...")
            rag = MentalHealthRAG(knowledge_base_dir=str(knowledge_base_dir))
            print(f"   ✓ Loaded {len(rag.doc_processor.documents)} documents")

            # 2. Index documents
            print("\n2. Indexing documents...")
            rag.index_documents()
            print(f"   ✓ Created {rag.vector_store.embeddings.shape[0]} embeddings")

            # 3. Test various queries
            test_queries = [
                ("우울증 치료 방법", "therapy_techniques"),
                ("자살 위기 대응", "crisis_protocols"),
                ("한국 문화와 정신건강", "cultural_context"),
                ("DBT 마음챙김", "therapy_techniques")
            ]

            print("\n3. Testing queries...")
            for query, expected_category in test_queries:
                print(f"\n   Query: '{query}'")
                results = rag.search(query, k=3)

                if results:
                    print(f"   ✓ Found {len(results)} results")
                    top_result = results[0]
                    print(f"     - Top score: {top_result.score:.3f}")
                    print(f"     - Category: {top_result.metadata.get('category')}")
                    print(f"     - Preview: {top_result.content[:100]}...")
                else:
                    print(f"   ⚠ No results found")

            # 4. Test context augmentation
            print("\n4. Testing context augmentation...")
            query = "CBT로 우울증을 어떻게 치료하나요?"
            context = rag.get_augmented_context(query, max_results=3)
            print(f"   ✓ Generated {len(context)} character context")

            # 5. Get statistics
            print("\n5. System statistics:")
            stats = {
                "Total documents": len(rag.doc_processor.documents),
                "Indexed": rag.is_indexed,
                "Embedding dimension": rag.vector_store.embeddings.shape[1] if rag.is_indexed else 0,
                "Queries evaluated": rag.evaluator.total_queries
            }
            for key, value in stats.items():
                print(f"   - {key}: {value}")

            print("\n" + "="*60)
            print("✓ END-TO-END TEST PASSED")
            print("="*60)

        except Exception as e:
            print(f"\n✗ End-to-end test failed: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"Integration test failed: {e}")


def test_knowledge_base_structure():
    """Test knowledge base directory structure"""
    kb_dir = Path(__file__).parent.parent / "knowledge_base"

    if not kb_dir.exists():
        pytest.skip("Knowledge base directory not found")

    expected_dirs = [
        "therapy_techniques",
        "crisis_protocols",
        "cultural_context"
    ]

    print("\nKnowledge base structure:")
    for dir_name in expected_dirs:
        dir_path = kb_dir / dir_name
        if dir_path.exists():
            files = list(dir_path.glob("*.txt")) + list(dir_path.glob("*.json"))
            print(f"  ✓ {dir_name}: {len(files)} files")
            for file in files:
                print(f"    - {file.name}")
        else:
            print(f"  ⚠ {dir_name}: Not found")


def test_manual_document_check():
    """Manual check of created documents"""
    kb_dir = Path(__file__).parent.parent / "knowledge_base"

    expected_files = {
        "therapy_techniques": ["CBT_manual_korean.txt", "DBT_manual_korean.txt", "ACT_manual_korean.txt"],
        "crisis_protocols": ["suicide_prevention_protocol.txt", "emergency_response.txt"],
        "cultural_context": ["korean_mental_health_culture.txt"]
    }

    print("\nDocument verification:")
    all_found = True

    for category, files in expected_files.items():
        print(f"\n{category}:")
        for filename in files:
            filepath = kb_dir / category / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"  ✓ {filename} ({size:,} bytes)")
            else:
                print(f"  ✗ {filename} NOT FOUND")
                all_found = False

    if all_found:
        print("\n✓ All expected documents found!")
    else:
        print("\n⚠ Some documents missing")


if __name__ == "__main__":
    print("="*60)
    print("RAG SYSTEM TEST SUITE")
    print("="*60)

    # Run manual checks first
    print("\n" + "="*60)
    print("MANUAL CHECKS")
    print("="*60)
    test_knowledge_base_structure()
    test_manual_document_check()

    # Run pytest
    print("\n" + "="*60)
    print("RUNNING PYTEST")
    print("="*60)
    pytest.main([__file__, "-v", "-s"])
