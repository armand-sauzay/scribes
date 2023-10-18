import concurrent.futures
import os
import shutil
from typing import Callable

from rich import print

from scribes.utils import save_to_json_file


def clean_extra_directories(config, repositories):
    current_directories = {
        os.path.join(config.output_directory, organization_name, repository_name)
        for organization_name in os.listdir(config.output_directory)
        if os.path.isdir(os.path.join(config.output_directory, organization_name))
        for repository_name in os.listdir(
            os.path.join(config.output_directory, organization_name)
        )
    }
    target_directories = {
        os.path.join(config.output_directory, repo["nameWithOwner"])
        for repo in repositories
    }
    extra_directories = current_directories - target_directories
    for path_to_remove in extra_directories:
        shutil.rmtree(path_to_remove)
        print(f"[bold red]Removed extra directory {path_to_remove}[/bold red]")
    return extra_directories


def clone_single_repository(repo_name_with_owner, output_directory, command_runner):
    """Clone or pull a single repository."""
    target_directory = os.path.join(output_directory, repo_name_with_owner)

    if command_runner.directory_exists(target_directory):
        print(
            f"[yellow]Repository {repo_name_with_owner} already exists. Deleting non-default branches and pulling changes...[/yellow]"  # noqa
        )
        command_runner.checkout_default_branch(target_directory)
        command_runner.remove_non_default_branches(
            target_directory, repo_name_with_owner
        )
    else:
        print(
            f"[yellow]Repository {repo_name_with_owner} does not exist. Cloning into {target_directory}...[/yellow]"  # noqa
        )
        command_runner.clone_repository(repo_name_with_owner, target_directory)


def clone_all_repositories(config, command_runner: Callable):
    print(
        f"[bold cyan]Listing repositories for {config.organization_name}...[/bold cyan]"
    )
    repositories = command_runner.list_all_repositories(config.organization_name)
    save_to_json_file(repositories, config.output_directory, "repositories.json")

    filtered_repositories = command_runner.list_repositories(config)
    save_to_json_file(
        filtered_repositories, config.output_directory, "filtered_repositories.json"
    )

    clean_extra_directories(config, filtered_repositories)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                clone_single_repository,
                repo["nameWithOwner"],
                config.output_directory,
                command_runner,
            )
            for repo in filtered_repositories
        ]
        concurrent.futures.wait(futures)
    print("[bold cyan]Done![/bold cyan]")
