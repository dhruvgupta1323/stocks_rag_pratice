from backend.app.guardrails.citations import CitationGuardrail


def test_validate_citations_accepts_known_sources():
    known = [
        {"id": "src-001", "url": "https://example.com/article1", "title": "Article 1"},
        {"id": "src-002", "url": "https://example.com/article2", "title": "Article 2"},
    ]
    citations = [
        {"source_id": "src-001", "url": "https://example.com/article1", "title": "Article 1"},
    ]
    valid, errors = CitationGuardrail.validate_citations(citations, known)
    assert len(valid) == 1
    assert len(errors) == 0


def test_validate_citations_rejects_hallucinations():
    known = [
        {"id": "src-001", "url": "https://example.com/article1", "title": "Article 1"},
    ]
    citations = [
        {"source_id": "fake-999", "url": "https://fake.com/fabricated", "title": "Fabricated News"},
    ]
    valid, errors = CitationGuardrail.validate_citations(citations, known)
    assert len(valid) == 0
    assert len(errors) == 1
    assert "Rejected unverified citation" in errors[0]

