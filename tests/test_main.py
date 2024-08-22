import json
import os
from pathlib import Path

import pytest
from cdktf import App

from er_aws_msk.__main__ import get_ai_input, init_cdktf_app  # noqa: PLC2701
from er_aws_msk.app_interface_input import AppInterfaceInput


@pytest.fixture(autouse=True)
def _prepare_test_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    raw_input_data: dict,
) -> None:
    """Prepare the test environment."""
    input_json = tmp_path / "input.json"
    input_json.write_text(json.dumps(raw_input_data))
    outdir = tmp_path / "outdir"
    monkeypatch.setenv("ER_INPUT_FILE", str(input_json.absolute()))
    monkeypatch.setenv("ER_OUTDIR", str(outdir.absolute()))


def test_main_get_ai_input(ai_input: AppInterfaceInput) -> None:
    """Test get_ai_input"""
    main_ai_input = get_ai_input()
    assert isinstance(main_ai_input, AppInterfaceInput)
    assert main_ai_input == ai_input


def test_main_app(ai_input: AppInterfaceInput) -> None:
    """Test init_cdktf_app"""
    app_id = "shiny-app-id"
    app = init_cdktf_app(ai_input, app_id)
    assert isinstance(app, App)
    app.synth()

    outdir = os.environ.get("ER_OUTDIR")
    assert outdir
    assert (Path(outdir) / "stacks" / app_id / "cdk.tf.json").exists()
