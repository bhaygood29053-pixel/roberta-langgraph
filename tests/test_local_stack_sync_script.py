from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "sync_local_stack.sh").read_text(encoding="utf-8")


def test_sync_script_updates_all_four_repositories_safely():
    for name in ("cmis", "cmis-core", "roberta-langgraph", "roberta-core"):
        assert f'$STACK_ROOT/{name}' in SCRIPT
    assert "git fetch --prune origin" in SCRIPT
    assert "git status --porcelain" in SCRIPT
    assert "Refusing to overwrite uncommitted work" in SCRIPT
    assert "git switch main" in SCRIPT
    assert "git pull --ff-only origin main" in SCRIPT
    assert 'git rev-parse origin/main' in SCRIPT


def test_sync_script_refreshes_private_and_assembled_runtimes():
    assert "pip install --upgrade --force-reinstall --no-deps" in SCRIPT
    assert "cmis-private-core/v1" in SCRIPT
    assert "scripts/build_roberta_runtime.sh" in SCRIPT
    assert "ROBERTA_PRIVATE_CORE_PATH" in SCRIPT
    assert "sudo systemctl restart cmis-gateway.service" in SCRIPT
    assert "sudo systemctl restart roberta-bridge.service" in SCRIPT


def test_sync_script_verifies_health_and_live_website():
    assert "http://127.0.0.1:8765/healthz" in SCRIPT
    assert "http://127.0.0.1:8766/healthz" in SCRIPT
    assert "ROBERTA — Verified On-Chain Intelligence" in SCRIPT
    assert "View evidence &amp; details" in SCRIPT
    assert "ROBERTA judgment" in SCRIPT
    assert "website_runtime=PASS" in SCRIPT
    assert "LOCAL_STACK_SYNC=PASS" in SCRIPT


def test_sync_script_cleans_only_known_generated_packaging_artifacts():
    assert "cleanup_generated_artifacts" in SCRIPT
    assert "build/|build/*|dist/|dist/*|*.egg-info/|*.egg-info/*" in SCRIPT
    assert "git status --porcelain --untracked-files=all" in SCRIPT
    assert "rm -rf -- \"$path\"" in SCRIPT

    # The general dirty-worktree guard must remain after cleanup.
    cleanup_index = SCRIPT.index("cleanup_generated_artifacts \"$repo\"")
    dirty_guard_index = SCRIPT.index("git status --porcelain", cleanup_index)
    assert cleanup_index < dirty_guard_index
