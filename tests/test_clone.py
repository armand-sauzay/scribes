from scribes.clone import clean_extra_directories, clone_single_repository


def test_clone_existing_repository(mock_command_runner):
    mock_command_runner.directory_exists.return_value = True

    clone_single_repository("org/repo", "/test_dir", mock_command_runner)

    mock_command_runner.checkout_default_branch.assert_called_once_with(
        "/test_dir/org/repo"
    )
    mock_command_runner.remove_non_default_branches.assert_called_once_with(
        "/test_dir/org/repo", "org/repo"
    )
    mock_command_runner.clone_repository.assert_not_called()


def test_clean_extra_directories(mock_config, mock_os_and_shutil):
    repos = [
        {"nameWithOwner": "org1/repo1"},
        {"nameWithOwner": "org2/repo2"},
    ]
    extra_dirs = clean_extra_directories(mock_config, repos)
    assert len(extra_dirs) == 0


def test_clone_new_repository(mock_command_runner):
    mock_command_runner.directory_exists.return_value = False

    clone_single_repository("org/repo", "/test_dir", mock_command_runner)

    mock_command_runner.clone_repository.assert_called_once_with(
        "org/repo", "/test_dir/org/repo"
    )
