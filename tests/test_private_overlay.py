from types import SimpleNamespace

import roberta


def test_editable_private_core_extends_roberta_package_path(monkeypatch, tmp_path):
    private_src = tmp_path / "private-core" / "src"
    private_roberta = private_src / "roberta"
    private_core_package = private_src / "roberta_core"
    private_roberta.mkdir(parents=True)
    private_core_package.mkdir(parents=True)
    private_init = private_core_package / "__init__.py"
    private_init.write_text("", encoding="utf-8")

    candidate = str(private_roberta.resolve())
    original_path = list(roberta.__path__)

    monkeypatch.setattr(
        roberta,
        "_find_spec",
        lambda name: SimpleNamespace(origin=str(private_init))
        if name == "roberta_core"
        else None,
    )

    try:
        roberta._extend_private_overlay_path()
        assert candidate in roberta.__path__
    finally:
        roberta.__path__[:] = original_path


def test_private_overlay_is_noop_when_private_core_is_absent(monkeypatch):
    original_path = list(roberta.__path__)
    monkeypatch.setattr(roberta, "_find_spec", lambda name: None)

    roberta._extend_private_overlay_path()

    assert list(roberta.__path__) == original_path
