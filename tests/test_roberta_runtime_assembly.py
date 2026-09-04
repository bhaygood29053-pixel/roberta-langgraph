from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_builder_installs_public_and_private_into_same_runtime_venv() -> None:
    script = (ROOT / "scripts" / "build_roberta_runtime.sh").read_text(encoding="utf-8")

    assert ".venv-runtime" in script
    assert '"\${REPO_ROOT}[deepseek]"' in script
    assert '"$PRIVATE_CORE_PATH"' in script
    assert "import roberta.graph" in script
    assert "import roberta.recommendation_policy" in script
    assert "import roberta.opinion_contract" in script
    assert "env -u PYTHONPATH" in script


def test_systemd_installer_requires_assembled_runtime_and_does_not_shadow_private_core() -> None:
    script = (
        ROOT / "scripts" / "install_roberta_bridge_systemd.sh"
    ).read_text(encoding="utf-8")

    assert ".venv-runtime/bin/python" in script
    assert "build_roberta_runtime.sh" in script
    assert "import roberta.recommendation_policy" in script
    assert "import roberta.opinion_contract" in script
    assert "Environment=PYTHONPATH=" not in script
    assert "PYTHONPATH=$REPO_ROOT/src" not in script
