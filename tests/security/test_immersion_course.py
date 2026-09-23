"""Course orchestration and evaluation contracts without a Docker daemon or model."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COURSE = ROOT / "05-security/immersive-12-stage"


def module(name):
    spec = importlib.util.spec_from_file_location(name, COURSE / "scripts" / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


labctl = module("labctl")
practice = module("practice")
dvwa = module("dvwa_sqli")


def test_compose_boundaries():
    config = json.loads((COURSE / "compose.json").read_text())
    assert set(config["services"]) == {"db", "dvwa", "juice"}
    assert "ports" not in config["services"]["db"]
    assert config["services"]["dvwa"]["ports"] == ["127.0.0.1:4280:80"]
    assert config["services"]["juice"]["ports"] == ["127.0.0.1:4300:3000"]
    for service in config["services"].values():
        assert service["platform"] == "linux/amd64"
        assert "privileged" not in service and "network_mode" not in service
        assert "mem_limit" in service and "cpus" in service
        assert all("/var/run/docker.sock" not in volume for volume in service.get("volumes", []))
    assert all(net["internal"] for net in config["networks"].values())


@pytest.mark.parametrize(
    "ref", ["mariadb:10.11", "evil.test/mariadb@sha256:" + "a" * 64, "mariadb@sha256:abc"]
)
def test_lock_rejects_floating_or_foreign_images(ref):
    with pytest.raises(ValueError):
        labctl.validated_image("DB_IMAGE", ref)


def test_accept_official_digest():
    value = "docker.io/library/mariadb@sha256:" + "b" * 64
    assert labctl.validated_image("DB_IMAGE", value) == value


def test_existing_lock_is_never_refreshed(tmp_path, monkeypatch):
    (tmp_path / "images.lock.json").write_text("keep")
    monkeypatch.setattr(labctl, "runtime_check", lambda: pytest.fail("must not call Docker"))
    with pytest.raises(ValueError, match="already exists"):
        labctl.lock_images(tmp_path)
    assert (tmp_path / "images.lock.json").read_text() == "keep"


def test_lock_uses_inspected_digests(tmp_path, monkeypatch):
    monkeypatch.setattr(labctl, "runtime_check", lambda: {})
    monkeypatch.setattr(labctl.subprocess, "run", lambda *args, **kwargs: None)

    def fake_docker(*args, **kwargs):
        key = next(k for k, seed in labctl.SEEDS.items() if seed == args[-1])
        return json.dumps(
            [
                {
                    "Os": "linux",
                    "Architecture": "amd64",
                    "Id": "sha256:" + "b" * 64,
                    "RepoDigests": [labctl.REPOS[key] + "@sha256:" + "a" * 64],
                }
            ]
        )

    monkeypatch.setattr(labctl, "docker", fake_docker)
    labctl.lock_images(tmp_path)
    env = labctl.locked_env(tmp_path)
    assert env["DVWA_IMAGE"] == "ghcr.io/digininja/dvwa@sha256:" + "a" * 64
    assert env["LAB_STATE"] == str(tmp_path)


def test_foreign_project_cannot_be_modified(tmp_path, monkeypatch):
    def fake_docker(*args, **kwargs):
        return (
            "abc"
            if args[0] == "ps"
            else json.dumps([{"Config": {"Labels": {"org.llm-hands-on.state": "/different"}}}])
        )

    monkeypatch.setattr(labctl, "docker", fake_docker)
    with pytest.raises(ValueError, match="another state"):
        labctl.check_ownership(tmp_path)


def test_down_never_removes_volumes(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(labctl, "compose", lambda *args: calls.append(args))
    assert labctl.main(["down", "--state", str(tmp_path)]) == 0
    assert calls == [(tmp_path, "both", "down")]


@pytest.mark.parametrize("mode,stopped", [("normal", False), ("loop", True), ("unknown", True)])
def test_agent_stop_conditions(tmp_path, mode, stopped):
    target = tmp_path / "trace.json"
    assert practice.main(["loop", "--mode", mode, "--budget", "3", "--output", str(target)]) == 0
    trace = json.loads(target.read_text())
    assert trace["source"] == "scripted-fixture"
    assert trace["result"]["stopped"] is stopped
    assert len(trace["result"]["trace"]) <= 3
    assert len(trace["events"]) >= 5
    if mode == "unknown":
        assert all(not row["result"]["ok"] for row in trace["result"]["trace"])


def test_fixture_confusion_matrix():
    result = practice.evaluate("v1", False, "demo-v1")
    assert result["source"] == "scripted-fixture" and result["model"] == "none"
    assert {k: result["metrics"][k] for k in ("tp", "tn", "fp", "fn", "errors")} == {
        "tp": 1,
        "tn": 1,
        "fp": 2,
        "fn": 1,
        "errors": 0,
    }
    cases = json.loads((COURSE / "data/regression.json").read_text())
    result["records"][0]["prediction"] = None
    stats = practice.score(cases, result["records"])
    assert stats["errors"] == 1 and stats["accuracy_including_errors"] == 0.2


@pytest.mark.parametrize(
    "text", ['{"supported":"true","reason":"x"}', '{"supported":true}', "```json\n{}\n```"]
)
def test_invalid_model_output_is_not_passed(text):
    with pytest.raises(ValueError):
        practice.parse_prediction(text)


def test_cannot_compare_fixture_and_model():
    a = practice.evaluate("v1", False, "demo-v1")
    b = practice.evaluate("v2", False, "demo-v2")
    b["source"] = "live-model"
    with pytest.raises(ValueError, match="source"):
        practice.compare(a, b)


def test_dvwa_token_parser_and_evidence_minimization():
    parser = dvwa.TokenParser()
    parser.feed('<input type="hidden" name="user_token" value="synthetic-token">')
    assert parser.token == "synthetic-token"
    result = dvwa.summarize(200, "<pre>First name: Alice</pre><pre>First name: Bob</pre>")
    assert result["first_name_rows"] == 2
    assert set(result) == {"status", "first_name_rows", "body_sha256"}


def test_dvwa_redirect_stays_in_lab():
    handler = dvwa.LocalRedirect()
    with pytest.raises(ValueError, match="outside"):
        handler.redirect_request(None, None, 302, "", {}, "https://example.test/")


def test_poc_gate_rejects_edits_and_wrong_hash(tmp_path):
    import hashlib

    gate = module("poc_gate")
    path = tmp_path / "poc.py"
    assert gate.main(["prepare", "--file", str(path)]) == 0
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert gate.validate(path, digest) == digest
    with pytest.raises(ValueError):
        gate.validate(path, "0" * 64)
    path.write_text(path.read_text() + "\nprint('changed')\n")
    with pytest.raises(ValueError):
        gate.validate(path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_poc_prepare_cannot_overwrite_or_execute(tmp_path, monkeypatch):
    gate = module("poc_gate")
    monkeypatch.setattr(
        gate.subprocess, "call", lambda *a, **k: pytest.fail("prepare must not execute")
    )
    path = tmp_path / "poc.py"
    assert gate.main(["prepare", "--file", str(path)]) == 0
    assert gate.main(["prepare", "--file", str(path)]) == 2
    assert gate.main(["execute", "--file", str(path)]) == 2


def test_remote_context_cannot_hide_behind_local_docker_host(monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "unix:///var/run/docker.sock")
    monkeypatch.setattr(
        labctl,
        "docker",
        lambda *a: json.dumps(
            [{"Name": "remote", "Endpoints": {"docker": {"Host": "ssh://other-host"}}}]
        ),
    )
    with pytest.raises(ValueError, match="local Unix"):
        labctl.runtime_check()
