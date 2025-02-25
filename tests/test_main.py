import json
from pathlib import Path

import pytest
from external_resources_io.config import EnvVar

from er_aws_msk.__main__ import get_ai_input  # noqa: PLC2701
from er_aws_msk.app_interface_input import AppInterfaceInput


@pytest.fixture(autouse=True)
def prepare_test_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    raw_input_data: dict,
) -> None:
    """Prepare the test environment."""
    input_json = tmp_path / "input.json"
    input_json.write_text(json.dumps(raw_input_data))
    monkeypatch.setenv(EnvVar.INPUT_FILE, str(input_json.absolute()))


def test_main_get_ai_input(ai_input: AppInterfaceInput) -> None:
    """Test get_ai_input"""
    main_ai_input = get_ai_input()
    assert isinstance(main_ai_input, AppInterfaceInput)
    assert main_ai_input == ai_input
