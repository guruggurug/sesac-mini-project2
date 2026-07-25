import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import (
    BASE_DIR,
    CORS_ALLOWED_ORIGINS,
    SESSION_SECRET_KEY,
    load_project_environment,
    parse_origin_allowlist,
    resolve_project_path,
)


def test_project_environment_loads_dotenv_file(tmp_path, monkeypatch):
    variable_name = "CHIP_BUDDY_TEST_DOTENV_VALUE"
    monkeypatch.delenv(variable_name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(f"{variable_name}=loaded-from-file\n", encoding="utf-8")

    assert load_project_environment(str(env_file)) is True
    assert os.environ[variable_name] == "loaded-from-file"


def test_process_environment_takes_precedence_over_dotenv(tmp_path, monkeypatch):
    variable_name = "CHIP_BUDDY_TEST_DOTENV_PRIORITY"
    monkeypatch.setenv(variable_name, "deployment-secret")
    env_file = tmp_path / ".env"
    env_file.write_text(f"{variable_name}=local-secret\n", encoding="utf-8")

    assert load_project_environment(str(env_file)) is True
    assert os.environ[variable_name] == "deployment-secret"


def test_relative_runtime_paths_are_resolved_from_project_root():
    assert resolve_project_path("data/runtime/state.db") == os.path.join(
        BASE_DIR, "data/runtime/state.db"
    )


def test_origin_allowlist_is_trimmed_deduplicated_and_never_wildcarded():
    origins = parse_origin_allowlist(
        " https://app.example.com/,http://localhost:5173,"
        "https://app.example.com "
    )

    assert origins == [
        "https://app.example.com",
        "http://localhost:5173",
    ]
    assert "*" not in CORS_ALLOWED_ORIGINS


def test_session_secret_is_not_the_removed_public_mvp_value():
    assert len(SESSION_SECRET_KEY) >= 32
    assert SESSION_SECRET_KEY != "chip-buddy-secret-key-super-secure-mvp-12345"
