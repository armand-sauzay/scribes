from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from scribes.cli import (
    ScribesConfig,
    check_file_exists,
    cli,
    clone_repository,
    get_repositories,
    run_command_on_repo,
)


@patch("subprocess.run")
def test_get_repositories(mock_run):
    mock_run.return_value = MagicMock(
        stdout='[{"name": "repo1", "isFork": false}, {"name": "repo2", "isFork": false}]',
        check=True,
    )
    repos = get_repositories("test-org")
    assert repos == ["test-org/repo1", "test-org/repo2"]


@patch("subprocess.run")
def test_check_file_exists(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    result = check_file_exists("test-org/repo1", ".pre-commit-config.yaml")
    assert result == ("test-org/repo1", True, "")


@patch("subprocess.run")
def test_clone_repository(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="Cloned successfully")
    repo, stdout, stderr = clone_repository("test-org/repo1")
    assert repo == "test-org/repo1"
    assert stdout == "Cloned successfully"
    assert stderr == ""


@patch("subprocess.run")
def test_run_command_on_repo(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0, stdout="Command executed successfully"
    )
    repo, stdout, stderr = run_command_on_repo("test-org/repo1", "ls")
    assert repo == "test-org/repo1"
    assert stdout == "Command executed successfully"
    assert stderr == ""


@patch("scribes.cli.load_config")
@patch("scribes.cli.save_config")
@patch("scribes.cli.get_repositories")
def test_search_command(mock_get_repositories, mock_save_config, mock_load_config):
    mock_load_config.return_value = ScribesConfig(
        org="test-org", repos=[], filtered_repos=[], cloned_repos=[], modified_repos=[]
    )
    mock_get_repositories.return_value = ["test-org/repo1", "test-org/repo2"]
    runner = CliRunner()
    result = runner.invoke(cli, ["search"])
    assert result.exit_code == 0
    assert "Repositories found: ['test-org/repo1', 'test-org/repo2']" in result.output


@patch("scribes.cli.load_config")
@patch("scribes.cli.save_config")
@patch("scribes.cli.run_in_parallel")
def test_filter_command(mock_run_in_parallel, mock_save_config, mock_load_config):
    mock_load_config.return_value = ScribesConfig(
        org="test-org",
        repos=["test-org/repo1", "test-org/repo2"],
        filtered_repos=[],
        cloned_repos=[],
        modified_repos=[],
    )
    mock_run_in_parallel.return_value = ["test-org/repo1"]
    runner = CliRunner()
    result = runner.invoke(
        cli, ["filter", "--contains-file", ".pre-commit-config.yaml"]
    )
    assert result.exit_code == 0
    assert "Repositories filtered: ['test-org/repo1']" in result.output


@patch("scribes.cli.load_config")
@patch("scribes.cli.save_config")
@patch("scribes.cli.run_command")
def test_clone_command(mock_run_command, mock_save_config, mock_load_config):
    mock_load_config.return_value = ScribesConfig(
        org="test-org",
        repos=["test-org/repo1", "test-org/repo2"],
        filtered_repos=[],
        cloned_repos=[],
        modified_repos=[],
    )
    mock_run_command.return_value = ["test-org/repo1"]
    runner = CliRunner()
    result = runner.invoke(cli, ["clone", "--limit", "1"])
    assert result.exit_code == 0
    assert "Repositories cloned: ['test-org/repo1']" in result.output


@patch("scribes.cli.load_config")
def test_get_modified_repos_command(mock_load_config):
    mock_load_config.return_value = ScribesConfig(
        org="test-org",
        repos=[],
        filtered_repos=[],
        cloned_repos=[],
        modified_repos=["test-org/repo1"],
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["get-modified-repos"])
    assert result.exit_code == 0
    assert "Modified repositories: ['test-org/repo1']" in result.output


@patch("scribes.cli.load_config")
@patch("scribes.cli.run_command")
def test_run_command(mock_run_command, mock_load_config):
    mock_load_config.return_value = ScribesConfig(
        org="test-org",
        repos=[],
        filtered_repos=[],
        cloned_repos=["test-org/repo1"],
        modified_repos=[],
    )
    mock_run_command.return_value = ["test-org/repo1"]
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "ls"])
    assert result.exit_code == 0
    assert 'Running "ls" across cloned repositories' in result.output


@patch("scribes.cli.load_config")
@patch("scribes.cli.save_config")
def test_add_repo_command(mock_save_config, mock_load_config):
    mock_load_config.return_value = ScribesConfig(
        org="test-org", repos=[], filtered_repos=[], cloned_repos=[], modified_repos=[]
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["add-repo", "test-org/repo1"])
    assert result.exit_code == 0
    assert "Repository test-org/repo1 added to cloned list." in result.output


@patch("scribes.cli.load_config")
@patch("scribes.cli.save_config")
def test_remove_repo_command(mock_save_config, mock_load_config):
    mock_load_config.return_value = ScribesConfig(
        org="test-org",
        repos=[],
        filtered_repos=[],
        cloned_repos=["test-org/repo1"],
        modified_repos=[],
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["remove-repo", "test-org/repo1"])
    assert result.exit_code == 0
    assert "Repository test-org/repo1 removed from cloned list." in result.output
