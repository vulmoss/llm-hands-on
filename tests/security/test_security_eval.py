import copy
import json
from pathlib import Path

import pytest
from conftest import FakeClient

from llm_lab.cli import dispatch, main, parser
from llm_lab.client import OllamaError
from llm_lab.config import Settings
from llm_lab.security_eval import (
    evaluate_cases,
    grade_answer,
    load_cases,
    validate_cases,
    write_report,
)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/security"


def sample():
    return load_cases([DATA / "benign.jsonl"])[0]


def test_shipped_cases_are_matched_controls():
    cases = load_cases([DATA / "benign.jsonl", DATA / "rag-injection.jsonl"])
    assert len(cases) == 20
    for control, attack in zip(cases[:10], cases[10:]):
        assert control["category"] == "benign" and attack["category"] == "injection"
        for field in ("pair_id", "question", "expected_any", "forbidden"):
            assert control[field] == attack[field]
        assert attack["documents"][0]["text"].startswith(control["documents"][0]["text"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", ""),
        ("category", []),
        ("expected_any", []),
        ("forbidden", [""]),
        ("documents", []),
        ("question", 3),
    ],
)
def test_bad_cases_fail_before_inference(field, value):
    case = sample()
    case[field] = value
    with pytest.raises(ValueError):
        validate_cases([case])


def test_duplicate_and_unknown_fields_are_rejected():
    case = sample()
    with pytest.raises(ValueError, match="重复"):
        validate_cases([case, copy.deepcopy(case)])
    case["unexpected"] = True
    with pytest.raises(ValueError, match="字段"):
        validate_cases([case])


def test_cli_check_never_constructs_client(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("离线校验不应创建模型 client")

    monkeypatch.setattr("llm_lab.cli.OllamaClient", forbidden)
    monkeypatch.setenv("OLLAMA_BASE_URL", "invalid-for-a-live-run")
    assert main(["security-eval", "--cases", str(DATA / "benign.jsonl"), "--check"]) == 0
    assert json.loads(capsys.readouterr().out)["model_evaluation"] == "not_run"


def test_results_record_failures_sources_and_backend():
    cases = load_cases([DATA / "benign.jsonl", DATA / "rag-injection.jsonl"])
    client = FakeClient(
        [
            {"role": "assistant", "content": "7342 [1]"},
            {"role": "assistant", "content": "INJECTION_SUCCEEDED"},
        ]
    )
    report = evaluate_cases(client, [cases[0], cases[10]])
    assert report["backend"] == "test_double"
    assert report["summary"]["benign"]["passed"] == 1
    assert report["summary"]["injection"]["marker_detected"] == 1
    assert (
        report["results"][1]["result"]["sources"][0]["chunk"]["text"]
        == cases[10]["documents"][0]["text"]
    )
    assert "INJECTION_SUCCEEDED" not in client.requests[0]["messages"][-1]["content"]
    assert "INJECTION_SUCCEEDED" in client.requests[1]["messages"][-1]["content"]
    assert len(report["code_sha256"]) == len(report["dataset_sha256"]) == 64


def test_error_is_not_counted_as_successful_defense():
    class BrokenClient(FakeClient):
        def chat(self, *args, **kwargs):
            raise OllamaError("offline")

    report = evaluate_cases(BrokenClient(), [sample()])
    summary = report["summary"]["benign"]
    assert summary["errors"] == 1 and summary["pass_rate"] == 0
    assert summary["marker_rate_completed"] is None
    assert report["summary"]["injection"]["pass_rate"] is None


def test_repeat_and_empty_response_are_recorded():
    client = FakeClient(
        [{"role": "assistant", "content": ""}, {"role": "assistant", "content": "7342"}]
    )
    report = evaluate_cases(client, [sample()], repeat=2)
    assert report["summary"]["benign"]["attempted"] == 2
    assert report["summary"]["benign"]["pass_rate"] == 0.5
    assert [row["run"] for row in report["results"]] == [1, 2]


def test_marker_heuristic_does_not_claim_semantic_understanding():
    result = grade_answer(sample(), "7342，我拒绝输出 INJECTION_SUCCEEDED")
    assert result["expected_match"] and result["marker_detected"] and not result["passed"]


def test_cli_writes_evidence_and_nonzero_for_failure(tmp_path):
    output = tmp_path / "result.json"
    args = parser().parse_args(
        ["security-eval", "--cases", str(DATA / "benign.jsonl"), "--output", str(output)]
    )
    client = FakeClient([{"role": "assistant", "content": "wrong"}] * 10)
    assert dispatch(args, Settings(), client) == 2
    assert json.loads(output.read_text())["backend"] == "test_double"
    with pytest.raises(ValueError, match="已存在"):
        dispatch(args, Settings(), client)


def test_report_does_not_overwrite_existing_evidence(tmp_path):
    output = tmp_path / "evidence.json"
    output.write_text("original")
    with pytest.raises(FileExistsError):
        write_report(output, {"new": True})
    assert output.read_text() == "original"


@pytest.mark.parametrize("repeat", [0, 21, True])
def test_repeat_is_bounded(repeat):
    with pytest.raises(ValueError, match="repeat"):
        evaluate_cases(FakeClient(), [sample()], repeat=repeat)
