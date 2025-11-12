"""
Simple RAG System Test (no pytest required)
Quick verification of document processing and search functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from rag_system import MentalHealthRAG
except ImportError as e:
    print(f"❌ Failed to import RAG system: {e}")
    sys.exit(1)


def test_knowledge_base_structure():
    """Test knowledge base directory structure"""
    print("\n" + "="*60)
    print("KNOWLEDGE BASE STRUCTURE CHECK")
    print("="*60)

    kb_dir = Path(__file__).parent.parent / "knowledge_base"

    if not kb_dir.exists():
        print("❌ Knowledge base directory not found")
        return False

    expected_files = {
        "therapy_techniques": ["CBT_manual_korean.txt", "DBT_manual_korean.txt", "ACT_manual_korean.txt"],
        "crisis_protocols": ["suicide_prevention_protocol.txt", "emergency_response.txt"],
        "cultural_context": ["korean_mental_health_culture.txt"]
    }

    all_found = True
    total_size = 0

    for category, files in expected_files.items():
        print(f"\n📁 {category}/")
        for filename in files:
            filepath = kb_dir / category / filename
            if filepath.exists():
                size = filepath.stat().st_size
                total_size += size
                print(f"  ✓ {filename} ({size:,} bytes)")
            else:
                print(f"  ❌ {filename} NOT FOUND")
                all_found = False

    print(f"\n📊 Total knowledge base size: {total_size:,} bytes ({total_size/1024:.1f} KB)")

    if all_found:
        print("\n✅ All expected documents found!")
    else:
        print("\n⚠️  Some documents missing")

    return all_found


def test_document_loading():
    """Test document loading"""
    print("\n" + "="*60)
    print("DOCUMENT LOADING TEST")
    print("="*60)

    kb_dir = Path(__file__).parent.parent / "knowledge_base"

    if not kb_dir.exists():
        print("❌ Knowledge base not found")
        return False

    try:
        print("\n📚 Initializing RAG system...")
        rag = MentalHealthRAG(knowledge_base_dir=str(kb_dir))

        doc_count = len(rag.doc_processor.documents)
        print(f"✓ Loaded {doc_count} documents")

        if doc_count == 0:
            print("❌ No documents loaded!")
            return False

        # Show document categories
        categories = {}
        for doc in rag.doc_processor.documents:
            cat = doc.metadata.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print("\n📊 Documents by category:")
        for cat, count in categories.items():
            print(f"  - {cat}: {count} chunks")

        print(f"\n✅ Document loading successful!")
        return True

    except Exception as e:
        print(f"❌ Document loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indexing():
    """Test document indexing"""
    print("\n" + "="*60)
    print("INDEXING TEST")
    print("="*60)

    kb_dir = Path(__file__).parent.parent / "knowledge_base"

    if not kb_dir.exists():
        print("❌ Knowledge base not found")
        return False

    try:
        print("\n🔧 Initializing RAG system...")
        rag = MentalHealthRAG(knowledge_base_dir=str(kb_dir))
        print(f"✓ Loaded {len(rag.doc_processor.documents)} documents")

        print("\n🔍 Creating embeddings...")
        rag.index_documents()

        if rag.is_indexed:
            print(f"✓ Indexed successfully!")
            print(f"  - Embedding shape: {rag.vector_store.embeddings.shape}")
            print(f"  - Vector dimension: {rag.vector_store.embeddings.shape[1]}")
            print(f"\n✅ Indexing successful!")
            return True
        else:
            print("❌ Indexing failed - is_indexed is False")
            return False

    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search():
    """Test search functionality"""
    print("\n" + "="*60)
    print("SEARCH TEST")
    print("="*60)

    kb_dir = Path(__file__).parent.parent / "knowledge_base"

    if not kb_dir.exists():
        print("❌ Knowledge base not found")
        return False

    try:
        print("\n🔧 Initializing and indexing...")
        rag = MentalHealthRAG(knowledge_base_dir=str(kb_dir))
        rag.index_documents()
        print(f"✓ Ready with {len(rag.doc_processor.documents)} documents")

        # Test queries
        test_queries = [
            "우울증 치료 방법",
            "자살 위기 대응",
            "한국 문화와 정신건강",
            "DBT 마음챙김 기술"
        ]

        print("\n🔍 Testing queries:")
        all_success = True

        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: '{query}'")

            results = rag.search(query, k=3, search_type="hybrid")

            if results:
                print(f"   ✓ Found {len(results)} results")
                top = results[0]
                print(f"   📄 Top result:")
                print(f"      - Score: {top.score:.3f}")
                print(f"      - Category: {top.metadata.get('category', 'unknown')}")
                print(f"      - Source: {top.metadata.get('source', 'unknown')}")
                print(f"      - Preview: {top.content[:100]}...")
            else:
                print(f"   ⚠️  No results found")
                all_success = False

        if all_success:
            print(f"\n✅ All searches returned results!")
        else:
            print(f"\n⚠️  Some searches had no results")

        return all_success

    except Exception as e:
        print(f"❌ Search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_augmentation():
    """Test context augmentation"""
    print("\n" + "="*60)
    print("CONTEXT AUGMENTATION TEST")
    print("="*60)

    kb_dir = Path(__file__).parent.parent / "knowledge_base"

    if not kb_dir.exists():
        print("❌ Knowledge base not found")
        return False

    try:
        print("\n🔧 Initializing and indexing...")
        rag = MentalHealthRAG(knowledge_base_dir=str(kb_dir))
        rag.index_documents()

        query = "CBT로 우울증을 어떻게 치료하나요?"
        print(f"\n📝 Query: '{query}'")

        print("\n🔍 Generating augmented context...")
        context = rag.get_augmented_context(query, max_results=3)

        if context:
            print(f"✓ Generated context: {len(context)} characters")
            print(f"\n📄 Context preview:")
            print("   " + "-"*56)
            lines = context.split('\n')[:10]
            for line in lines:
                print(f"   {line}")
            if len(context.split('\n')) > 10:
                print("   ...")
            print("   " + "-"*56)
            print(f"\n✅ Context augmentation successful!")
            return True
        else:
            print("❌ No context generated")
            return False

    except Exception as e:
        print(f"❌ Context augmentation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" "*20 + "RAG SYSTEM TEST SUITE")
    print("="*70)

    results = {}

    # Run tests
    results['structure'] = test_knowledge_base_structure()
    results['loading'] = test_document_loading()
    results['indexing'] = test_indexing()
    results['search'] = test_search()
    results['augmentation'] = test_context_augmentation()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper():.<50} {status}")

    print(f"\n{'TOTAL':.<50} {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! RAG system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
