import json
from pathlib import Path


ROOT = Path(__file__).parents[3]


def test_multistage_image_builds_css_and_runs_python_only():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM node:24-alpine AS frontend-build" in dockerfile
    assert "RUN npm ci" in dockerfile
    assert "RUN npm run css:build" in dockerfile
    assert "FROM python:3.11-slim AS runtime" in dockerfile
    assert "COPY --from=frontend-build" in dockerfile
    assert "USER chipbuddy" in dockerfile
    assert "uvicorn app.main:app" in dockerfile
    assert "--proxy-headers" in dockerfile
    assert "--forwarded-allow-ips='*'" in dockerfile
    assert "os.environ.get('PORT', '8000')" in dockerfile


def test_procfile_trusts_platform_forwarded_https_headers():
    procfile = (ROOT / "Procfile").read_text(encoding="utf-8")

    assert "--proxy-headers" in procfile
    assert "--forwarded-allow-ips='*'" in procfile


def test_docker_context_excludes_secrets_and_local_dependencies():
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")

    for excluded in (".env", ".venv", "node_modules", ".tools", "data/runtime"):
        assert excluded in dockerignore


def test_node_lts_contract_matches_package_lock():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))

    assert (ROOT / ".nvmrc").read_text(encoding="utf-8").strip() == "24"
    assert package["engines"] == {"node": ">=24 <25", "npm": ">=11"}
    assert lock["packages"][""]["engines"] == package["engines"]
    assert package["scripts"]["build"] == "npm run css:build"


def test_generated_css_contains_current_dynamic_state_classes():
    css = (ROOT / "src/frontend/static/css/index.css").read_text(encoding="utf-8")

    assert ".animate-spin" in css
    assert ".opacity-80" in css
    assert ".z-\\[60\\]" in css
