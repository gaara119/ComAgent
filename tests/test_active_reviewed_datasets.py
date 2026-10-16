from hashlib import sha256
import json

import pytest

from eval.active_datasets import active_dataset_path


def setup_pointer(root, split="dev"):
    target=root/"eval/datasets/revised/sql-dev.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({"id":"sql-one","split":split})+"\n","utf-8")
    pointer=root/"eval/datasets/current.json"
    pointer.write_text(json.dumps({"format_version":1,"dev_only":True,
                                  "suites":{"nl2sql":{"path":"eval/datasets/revised/sql-dev.jsonl",
                                  "sha256":sha256(target.read_bytes()).hexdigest()}}}),"utf-8")
    return target,pointer


def test_activated_revision_used_and_legacy_fallback_retained(tmp_path):
    fallback=tmp_path/"old.jsonl"
    assert active_dataset_path("nl2sql",fallback,root=tmp_path)==fallback
    target,_=setup_pointer(tmp_path)
    assert active_dataset_path("nl2sql",fallback,root=tmp_path)==target
    assert active_dataset_path("unknown",fallback,root=tmp_path)==fallback


def test_modified_labels_cannot_reuse_activation_hash(tmp_path):
    target,_=setup_pointer(tmp_path)
    target.write_text('{"split":"dev","modified":true}\n',"utf-8")
    with pytest.raises(ValueError,match="更改"):
        active_dataset_path("nl2sql",target,root=tmp_path)


def test_holdout_cannot_become_implicit_development_evaluation(tmp_path):
    target,_=setup_pointer(tmp_path,"holdout")
    with pytest.raises(ValueError,match="保留集"):
        active_dataset_path("nl2sql",target,root=tmp_path)
