"""The shared API must not accept a page number the PDF viewer cannot open."""
import pytest
from pydantic import ValidationError

from qa_agent.schemas import Evidence


def test_evidence_page_uses_one_based_pdf_physical_pages():
    fields = dict(evidence_id="E1", doc_id="doc", doc_title="Title", text="source")
    assert Evidence(**fields, page=1).page == 1
    assert Evidence(**fields, page=None).page is None
    with pytest.raises(ValidationError):
        Evidence(**fields, page=0)
