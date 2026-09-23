"""Real loopback HTTP, permission matrices and non-model evidence checks."""

import json
from urllib.parse import quote

import pytest

from llm_lab.web_security.__main__ import main, review_prompt
from llm_lab.web_security.cases import BY_ID, CASES
from llm_lab.web_security.runner import request, run_cases
from llm_lab.web_security.server import FRONTEND, running


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_vulnerable_fixed_and_normal_controls(case):
    evidence = run_cases([case])
    assert evidence["passed"], evidence
    assert len(evidence["cases"][0]["modes"]) == 2


@pytest.fixture
def fixed_app():
    with running(True) as info:
        yield info


@pytest.mark.parametrize(
    "sid,order,status",
    [
        (None, "1", 401),
        (None, "2", 401),
        ("alice-lab", "1", 200),
        ("alice-lab", "2", 403),
        ("bob-lab", "1", 403),
        ("bob-lab", "2", 200),
        ("forged", "1", 401),
        ("alice-lab", "999", 404),
    ],
)
def test_ownership_matrix(fixed_app, sid, order, status):
    base, _ = fixed_app
    headers = {} if sid is None else {"Cookie": f"sid={sid}"}
    assert request(base, "GET", f"/orders?id={order}", headers)["status"] == status


def test_oauth_state_is_session_bound_and_single_use(fixed_app):
    base, _ = fixed_app
    alice = {"Cookie": "sid=alice-lab"}
    bob = {"Cookie": "sid=bob-lab"}
    assert request(base, "GET", "/oauth/start")["status"] == 401
    state = json.loads(request(base, "GET", "/oauth/start", alice)["body"])["state"]
    bob_state = json.loads(request(base, "GET", "/oauth/start", bob)["body"])["state"]
    assert state != bob_state
    callback = "/oauth/callback?code=lab-code&state=" + quote(state)
    assert request(base, "GET", callback, bob)["status"] == 403
    assert request(base, "GET", callback, alice)["status"] == 200
    assert request(base, "GET", callback, alice)["status"] == 403
    assert (
        request(base, "GET", "/oauth/callback?code=lab-code&state=" + bob_state, bob)["status"]
        == 200
    )


def test_upload_boundary_and_reset():
    for fixed, expected in [(False, 201), (True, 400)]:
        with running(fixed) as (base, _):
            response = request(
                base, "POST", "/upload", body={"name": "../note.html", "content": "LAB"}
            )
            assert response["status"] == expected
            assert (
                request(base, "POST", "/upload", body={"name": "note.txt", "content": "OK"})[
                    "status"
                ]
                == 201
            )
    with running(False) as (base, _):
        assert request(base, "GET", "/download?name=note.txt")["status"] == 404


@pytest.mark.parametrize("quantity", [-1, 0, 11, True, "2", 1.5])
def test_quantity_invalid_types_and_bounds(fixed_app, quantity):
    base, _ = fixed_app
    assert request(base, "POST", "/checkout", body={"quantity": quantity})["status"] == 400


def test_server_price_and_normal_results(fixed_app):
    base, app = fixed_app
    response = request(base, "POST", "/checkout", body={"quantity": 2, "unit_price": 1})
    assert json.loads(response["body"])["total"] == 200
    assert json.loads(request(base, "GET", "/search?q=public")["body"]) == {"titles": ["public"]}
    assert json.loads(request(base, "GET", "/search?q=missing")["body"]) == {"titles": []}
    assert request(base, "GET", "/fetch?service=http%3A%2F%2Fexample.test")["status"] == 400
    request(base, "POST", "/profile", {"Cookie": "sid=alice-lab"}, {"role": "admin"})
    assert app.profile["role"] == "reader"


def test_csrf_denial_does_not_change_state(fixed_app):
    base, app = fixed_app
    response = request(
        base, "POST", "/email", {"Cookie": "sid=alice-lab", "Origin": base}, {"email": "wrong"}
    )
    assert response["status"] == 403
    assert app.email == "alice@example.test"
    response = request(
        base,
        "POST",
        "/email",
        {"Cookie": "sid=alice-lab", "Origin": base, "X-CSRF-Token": "lab-csrf-alice"},
        {"email": "new@example.test"},
    )
    assert response["status"] == 200
    assert app.email == "new@example.test"


def test_storage_principals_and_cors_allowlist(fixed_app):
    base, _ = fixed_app
    for sid, expected in [("alice-lab", 200), ("bob-lab", 403)]:
        assert (
            request(base, "GET", "/objects?key=private.txt", {"Cookie": f"sid={sid}"})["status"]
            == expected
        )
    response = request(base, "GET", "/cors", {"Origin": "https://dashboard.example.test"})
    assert response["headers"]["Access-Control-Allow-Origin"] == "https://dashboard.example.test"
    assert response["headers"]["Vary"] == "Origin"
    response = request(base, "GET", "/cors", {"Origin": "https://dashboard.example.test.evil.test"})
    assert "Access-Control-Allow-Origin" not in response["headers"]


def test_frontend_allowlist_and_sourcemap(fixed_app):
    base, _ = fixed_app
    for name in ["index.html", "app.js", "app.js.map", "lazy.js"]:
        assert request(base, "GET", "/frontend/" + name)["status"] == 200
    assert request(base, "GET", "/frontend/../server.py")["status"] == 404
    mapping = json.loads((FRONTEND / "app.js.map").read_text())
    assert mapping["sourcesContent"] == [(FRONTEND / "app.js").read_text()]


def test_prompt_is_data_and_cli_defaults_offline(tmp_path, monkeypatch, capsys):
    evidence = run_cases([BY_ID["idor"]])
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence))

    def forbidden(*args, **kwargs):
        raise AssertionError("offline review must not call model")

    monkeypatch.setattr("llm_lab.web_security.__main__.OllamaClient", forbidden)
    assert main(["review", "--evidence", str(path)]) == 0
    assert "sid=alice-lab" in capsys.readouterr().out
    messages = review_prompt(evidence)
    assert messages[0]["role"] == "system"
    assert "B-book" in messages[1]["content"]
    path.write_text("[]")
    assert main(["review", "--evidence", str(path)]) == 2
