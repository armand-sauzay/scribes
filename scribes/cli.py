import json
import multiprocessing
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional

import click
from pydantic import BaseModel, ValidationError

CONFIG_FILE = os.path.join(os.getcwd(), "scribes.json")
REPO_DIR = os.path.join(os.getcwd(), "scribes_repos")


class ScribesConfig(BaseModel):
    org: str
    repos: List[str]
    filtered_repos: List[str] = []
    cloned_repos: List[str] = []
    modified_repos: List[str] = []


def load_config() -> ScribesConfig:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return ScribesConfig(**json.load(f))
        except ValidationError as e:
            print(f"Configuration error: {e}")
            exit(1)
    else:
        org = click.prompt("Enter GitHub organization name")
        config_data = {
            "org": org,
            "repos": [],
            "filtered_repos": [],
            "cloned_repos": [],
            "modified_repos": [],
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f)
        return ScribesConfig(**config_data)


def save_config(config: ScribesConfig) -> None:
    with open(CONFIG_FILE, "w") as f:
        json.dump(config.model_dump(), f)


def get_repositories(org: str) -> List[str]:
    result = subprocess.run(
        ["gh", "repo", "list", org, "--json", "name,isFork"],
        capture_output=True,
        text=True,
        check=True,
    )
    repos = json.loads(result.stdout)
    return [f"{org}/{repo['name']}" for repo in repos if not repo["isFork"]]


def check_file_exists(repo: str, file_path: str) -> tuple:
    result = subprocess.run(
        ["gh", "api", f"/repos/{repo}/contents/{file_path}"],
        capture_output=True,
        text=True,
    )
    return (
        repo,
        result.returncode == 0,
        result.stderr.strip() if result.returncode != 0 else "",
    )


def clone_repository(repo: str) -> tuple:
    repo_path = os.path.join(REPO_DIR, repo.split("/")[-1])
    try:
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        result = subprocess.run(
            ["gh", "repo", "clone", repo, repo_path], capture_output=True, text=True
        )
        if result.returncode == 0:
            return repo, result.stdout.strip(), ""
        else:
            return repo, "", result.stderr.strip()
    except Exception as e:
        return repo, "", str(e)


def run_command_on_repo(repo: str, command: str) -> tuple:
    repo_path = os.path.join(REPO_DIR, repo.split("/")[-1])
    try:
        result = subprocess.run(
            command, cwd=repo_path, shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            return repo, result.stdout.strip(), ""
        else:
            return repo, "", result.stderr.strip()
    except Exception as e:
        return repo, "", str(e)


def run_in_parallel(repos: List[str], func: Callable, *args) -> List[str]:
    def log_and_append_result(future, results):
        repo, stdout, stderr = future.result()
        click.echo(f'Running "{func.__name__}" on {repo}')
        if stdout:
            click.echo(f"Output for {repo}:\n{stdout}\n")
        if stderr:
            click.echo(f"Error for {repo}:\n{stderr}\n")
        results.append(repo)

    results = []
    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = {executor.submit(func, repo, *args): repo for repo in repos}

        for future in as_completed(futures):
            log_and_append_result(future, results)

    return results


def run_command(repos: List[str], func: Callable, parallel: bool, *args) -> List[str]:
    results = []
    if parallel:
        results = run_in_parallel(repos, func, *args)
    else:
        for repo in repos:
            result = func(repo, *args)
            repo, stdout, stderr = result
            click.echo(f'Running "{func.__name__}" on {repo}')
            if stdout:
                click.echo(f"Output for {repo}:\n{stdout}\n")
            if stderr:
                click.echo(f"Error for {repo}:\n{stderr}\n")
            results.append(repo)
    return results


@click.group()
def cli() -> None:
    pass


@click.command()
def search() -> None:
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    config = load_config()
    org = config.org
    repos = get_repositories(org)
    config.repos = repos
    save_config(config)
    click.echo(f"Repositories found: {repos}")


@click.command()
@click.option(
    "--contains-file", help="Filter repositories that contain the specified file"
)
def filter(contains_file: Optional[str]) -> None:
    config = load_config()
    repos = config.repos
    filtered_repos = repos

    if contains_file:
        filtered_repos = run_in_parallel(repos, check_file_exists, contains_file)

    config.filtered_repos = filtered_repos
    save_config(config)
    click.echo(f"Repositories filtered: {filtered_repos}")


@click.command()
@click.option(
    "--limit", default=None, type=int, help="Limit the number of repositories to clone"
)
@click.option(
    "--parallel", is_flag=True, default=True, help="Clone repositories in parallel"
)
def clone(limit: Optional[int], parallel: bool) -> None:
    config = load_config()
    repos = config.filtered_repos if config.filtered_repos else config.repos

    if limit:
        repos = repos[:limit]

    os.makedirs(REPO_DIR, exist_ok=True)

    cloned_repos = run_command(repos, clone_repository, parallel)
    config.cloned_repos = cloned_repos
    save_config(config)
    click.echo(f"Repositories cloned: {cloned_repos}")


@click.command()
def get_modified_repos() -> None:
    config = load_config()
    click.echo(f"Modified repositories: {config.modified_repos}")


@click.command()
@click.argument("command")
@click.option("--parallel", is_flag=True, default=True, help="Run command in parallel")
@click.option(
    "--modified-only",
    is_flag=True,
    default=False,
    help="Run command only on modified repositories",
)
def run(command: str, parallel: bool, modified_only: bool) -> None:
    config = load_config()
    repos = config.modified_repos if modified_only else config.cloned_repos
    click.echo(
        f'Running "{command}" across {"modified" if modified_only else "cloned"} repositories'
    )
    run_command(repos, run_command_on_repo, parallel, command)


@click.command()
@click.argument("repo")
def add_repo(repo: str) -> None:
    config = load_config()
    if repo not in config.cloned_repos:
        config.cloned_repos.append(repo)
        save_config(config)
        click.echo(f"Repository {repo} added to cloned list.")
    else:
        click.echo(f"Repository {repo} is already in the cloned list.")


@click.command()
@click.argument("repo")
def remove_repo(repo: str) -> None:
    config = load_config()
    if repo in config.cloned_repos:
        config.cloned_repos.remove(repo)
        save_config(config)
        click.echo(f"Repository {repo} removed from cloned list.")
    else:
        click.echo(f"Repository {repo} is not in the cloned list.")


cli.add_command(search)
cli.add_command(filter)
cli.add_command(clone)
cli.add_command(get_modified_repos)
cli.add_command(run)
cli.add_command(add_repo)
cli.add_command(remove_repo)

if __name__ == "__main__":
    cli()
