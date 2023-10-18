from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_config():
    return MagicMock(output_directory="/test_dir", organization_name="org")


@pytest.fixture
def mock_os_and_shutil(mocker):
    def mock_listdir(path):
        if path == "/test_dir":
            return ["org1", "org2"]
        elif path == "/test_dir/org1":
            return ["repo1"]
        elif path == "/test_dir/org2":
            return ["repo2"]
        return []

    mocker.patch("os.listdir", side_effect=mock_listdir)
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("shutil.rmtree")


@pytest.fixture
def mock_command_runner():
    command_runner = MagicMock()
    command_runner.list_all_repositories.return_value = [{"nameWithOwner": "org/repo1"}]
    command_runner.list_repositories.return_value = [{"nameWithOwner": "org/repo1"}]
    return command_runner


@pytest.fixture
def future_mock(mocker):
    future = mocker.MagicMock()
    future.result.return_value = None
    return future
