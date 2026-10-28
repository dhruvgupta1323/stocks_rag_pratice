from typing import List, Dict, Any, Tuple


class CitationGuardrail:
    """Validates citations against stored source metadata to prevent hallucinations."""

    @staticmethod
    def validate_citations(
        citations: List[Dict[str, Any]],
        known_sources: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Verifies that every cited source exists and has genuine metadata."""
        valid_citations: List[Dict[str, Any]] = []
        errors: List[str] = []

        known_source_ids = {str(s.get("id") or s.get("source_id")) for s in known_sources}
        known_urls = {s.get("url") for s in known_sources if s.get("url")}

        for cit in citations:
            source_id = str(cit.get("source_id", ""))
            url = cit.get("url", "")
            title = cit.get("title", "")

            # Check if source_id or URL matches known sources
            if source_id in known_source_ids or url in known_urls:
                valid_citations.append(cit)
            else:
                errors.append(f"Rejected unverified citation: '{title}' (ID: {source_id}). Not in retrieved evidence.")

        return valid_citations, errors

