import pytest

from scripts.apply_manual_review_ledger import merge_decisions


def material(choice="证据不足"):
    original = {"rows": [{"review_key": "alias:one", "content_sha256": "material-hash",
                          "original_ids": ["one"], "group": "alias", "title": "old",
                          "decision_objects": [{"object": "别名关系"}], "system_versions": []}]}
    submitted = {"rows": [{"key": "alias:one", "hash": "material-hash",
                           "fields": {"question": "new", "label": "disabled", "notes": "evidence limited"},
                           "decisions": [{"attrs": {"data-object": "别名关系"}, "choice": choice,
                                          "explicit_selected": True}]}]}
    return original, submitted, {"explicit_application_requested": True}


def test_insufficient_relationship_is_resolved_without_becoming_accepted():
    out = merge_decisions(*material())
    assert out["summary"]["unprocessed_decisions"] == 0
    assert out["rows"][0]["decisions"][0]["resolution"] == "insufficient_evidence"
    assert out["rows"][0]["human_signatures"] is None


def test_stale_content_cannot_inherit_human_acceptance():
    old, new, auth = material("通过")
    new["rows"][0]["hash"] = "different"
    with pytest.raises(ValueError, match="Stale"):
        merge_decisions(old, new, auth)


def test_missing_decision_and_missing_authorization_are_rejected():
    old, new, auth = material()
    new["rows"][0]["decisions"] = []
    with pytest.raises(ValueError, match="Missing decision slots"):
        merge_decisions(old, new, auth)
    with pytest.raises(ValueError, match="authorization"):
        merge_decisions(old, new, {})


def test_actual_response_dimension_requires_that_exact_version():
    old, new, auth = material()
    new["rows"][0]["decisions"] = [{"attrs": {"data-version": "unseen"},
                                   "choice": "通过", "explicit_selected": True}]
    with pytest.raises(ValueError, match="Unknown actual response version"):
        merge_decisions(old, new, auth)
