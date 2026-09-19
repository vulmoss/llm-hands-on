import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "gen_security_catalog", ROOT / "scripts/gen_security_catalog.py"
)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def data():
    return json.loads((ROOT / "data/security/labs.json").read_text())


def test_catalog_matches_generated_document():
    assert catalog.main(["--check"]) == 0


@pytest.mark.parametrize("path", ["missing.md", "../README.md", "/etc/passwd"])
def test_catalog_rejects_missing_or_external_paths(path):
    broken = data()
    broken["labs"][0]["entrypoint"] = path
    with pytest.raises(ValueError, match="仓库内"):
        catalog.validate_catalog(broken, ROOT)


def test_catalog_rejects_duplicate_ids_and_inconsistent_status():
    broken = data()
    broken["labs"].append(copy.deepcopy(broken["labs"][0]))
    with pytest.raises(ValueError, match="重复"):
        catalog.validate_catalog(broken, ROOT)
    broken = data()
    broken["labs"][0]["model_status"] = "not_applicable"
    with pytest.raises(ValueError, match="不一致"):
        catalog.validate_catalog(broken, ROOT)
