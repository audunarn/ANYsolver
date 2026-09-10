"""Confirmation infrastructure tests, separate from the G1 mechanics inventory."""
from copy import deepcopy
from hashlib import sha256
import json
from unittest.mock import patch
import pytest
from scripts import confirm_ge_beam3_g1 as c


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1}'])
def test_strict_rejects_malformed(raw):
    with pytest.raises(ValueError): c.strict(raw)


def good_results():
    return dict(collected=["one"], exitcode=0,
                reports=[dict(node="one", phase=p, outcome="passed") for p in ("setup", "call", "teardown")])


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "skipped", "failed", "inventory", "exit", "extra"])
def test_inventory_phase_mutations(mutation):
    body = good_results()
    if mutation == "missing": body["reports"].pop()
    elif mutation == "duplicate": body["reports"].append(body["reports"][0])
    elif mutation in ("skipped", "failed"): body["reports"][1]["outcome"] = mutation
    elif mutation == "inventory": body["collected"] = []
    elif mutation == "exit": body["exitcode"] = 1
    else: body["extra"] = True
    with pytest.raises(ValueError): c.validate_results(body, ["one"])


def test_complete_results_and_canonical_bytes():
    body = good_results(); c.validate_results(body, ["one"])
    assert c.strict(c.canonical(body)) == body


@pytest.mark.parametrize("mutation", ["hash", "commit", "tree", "findings", "decision", "independence", "schema"])
def test_review_rejection(tmp_path, mutation):
    body = dict(decision=c.ACCEPTED, findings=[], subject_commit="candidate",
                scope=dict(subject_tree="tree"), reviewer=dict(independent=True))
    if mutation == "commit": body["subject_commit"] = "other"
    elif mutation == "tree": body["scope"]["subject_tree"] = "other"
    elif mutation == "findings": body["findings"] = ["state-safety"]
    elif mutation == "decision": body["decision"] = "BLOCKED"
    elif mutation == "independence": body["reviewer"]["independent"] = False
    elif mutation == "schema": body["extra"] = True
    path = tmp_path/"review.json"; c.write(path, body)
    digest = "0"*64 if mutation == "hash" else sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError): c.review_input(path, digest, "candidate", "tree")


def test_publication_failure_and_exclusivity(tmp_path):
    path = tmp_path/"aggregate.json"; body = dict(result="scoped")
    with patch.object(c.os, "link", side_effect=OSError("injected")):
        with pytest.raises(OSError): c.publish(path, body)
    assert not path.exists() and path.with_name("aggregate.json.pending").exists()
    other = tmp_path/"accepted.json"; c.publish(other, body); before = other.read_bytes()
    with pytest.raises(FileExistsError): c.publish(other, dict(result="overwrite"))
    assert other.read_bytes() == before


def test_identity_rejects_dirty_candidate():
    with patch.object(c, "git", side_effect=["candidate", " M dirty.py"]):
        with pytest.raises(ValueError, match="dirty"): c.identity("candidate")


def test_registered_inventory_is_complete_and_unique():
    body = json.loads(c.INVENTORY.read_bytes())
    assert len(body) == len(set(body)) == 49
    assert all(n.split("::")[0] in c.TESTS for n in body)
