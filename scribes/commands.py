import json
import os
import re
import subprocess
from typing import Any, Dict

from rich import print


class CommandRunner:
    def directory_exists(self, path: str) -> bool:
        return os.path.exists(path) and os.path.isdir(path)

    def checkout_default_branch(self, cwd: str) -> None:
        default_branch = self.get_default_branch("/".join(cwd.split("/")[-2:]))
        self.checkout_branch(cwd, default_branch)

    def get_default_branch(self, repository_name_with_owner: str) -> str:
        result = self._run(
            [
                "gh",
                "repo",
                "view",
                repository_name_with_owner,
                "--json",
                "defaultBranchRef",
            ]
        )
        return json.loads(result.stdout)["defaultBranchRef"]["name"]

    def checkout_branch(self, cwd: str, branch_name: str) -> None:
        result = self._run(["git", "checkout", branch_name], cwd=cwd)
        if result.returncode == 0:
            print(
                f"[green]Successfully checked out and pulled branch {branch_name} in {cwd}[/green]"  # noqa
            )
        else:
            print(
                f"[red]Failed to check out branch {branch_name} in {cwd}[/red]\n{result.stderr}"  # noqa
            )

    def pull(self, cwd: str) -> None:
        result = self._run(["git", "pull"], cwd=cwd)
        if result.returncode == 0:
            print(f"[green]Successfully pulled changes in {cwd}[/green]")
        else:
            print(f"[red]Failed to pull changes in {cwd}[/red]\n{result.stderr}")

    def remove_non_default_branches(
        self, cwd: str, repository_name_with_owner: str
    ) -> None:
        result = self._run(["git", "branch", "--format=%(refname:short)"], cwd=cwd)
        branches = result.stdout.splitlines()
        default_branch = self.get_default_branch(repository_name_with_owner)
        branches_to_delete = [
            branch for branch in branches if branch.strip() != default_branch
        ]
        for branch in branches_to_delete:
            self.delete_branch(cwd, branch)
        if result.returncode == 0:
            print(f"[green]Successfully removed non-default branches in {cwd}[/green]")
        else:
            print(
                f"[red]Failed to remove non-default branches in {cwd}[/red]\n{result.stderr}"  # noqa
            )

    def delete_branch(self, cwd: str, branch_name: str) -> None:
        result = self._run(["git", "branch", "-D", branch_name], cwd=cwd)
        if result.returncode == 0:
            print(f"[green]Successfully deleted branch {branch_name} in {cwd}[/green]")
        else:
            print(
                f"[red]Failed to delete branch {branch_name} in {cwd}[/red]\n{result.stderr}"  # noqa
            )

    def clone_repository(self, repo_path: str, target_directory: str) -> None:
        result = self._run(["gh", "repo", "clone", repo_path, target_directory])
        if result.returncode == 0:
            print(f"[green]Successfully cloned {repo_path}[/green]")
        else:
            print(f"[red]Failed to clone {repo_path}[/red]\n{result.stderr}")

    def list_all_repositories(self, orgaization_name: str) -> Any:
        """List repositories based on configuration."""
        cmd = [
            "gh",
            "repo",
            "list",
            orgaization_name,
            "--limit",
            "100",
            "--json",
            "nameWithOwner,visibility,isFork,isEmpty,isArchived",
        ]
        result = self._run(cmd)
        all_repos = json.loads(result.stdout)
        return all_repos

    def list_repositories(self, config: str) -> Dict[str, Any]:
        """List repositories based on configuration."""
        all_repos = self.list_all_repositories(config.organization_name)
        filtered_repos = self._filter_repositories(all_repos, config)
        return filtered_repos

    def _filter_repositories(
        self, all_repos: list[str], config: Dict[str, Any]
    ) -> list[str]:
        """Filter repositories based on configuration."""
        filtered = [
            repo
            for repo in all_repos
            if (config.include_forks or not repo["isFork"])
            and (config.include_private or repo["visibility"] != "private")
            and (config.include_archived or not repo["isArchived"])
            and not repo["isEmpty"]
        ]
        if config.include:
            filtered = [
                repo
                for repo in filtered
                if re.search(config.include, repo["nameWithOwner"])
            ]
        if config.exclude:
            filtered = [
                repo
                for repo in filtered
                if not re.search(config.exclude, repo["nameWithOwner"])
            ]
        return filtered

    def has_changes(self, repo_path: str) -> bool:
        """Check if the repository has any changes."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())

    def _run(self, cmd: list[str], cwd: str = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return result
