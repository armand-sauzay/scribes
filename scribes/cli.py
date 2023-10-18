import json
import subprocess

import click
from rich import print

from scribes.clone import clone_all_repositories
from scribes.commands import CommandRunner
from scribes.config import Config
from scribes.executor import execute_concurrently


@click.group()
@click.pass_context
def main(ctx):
    """Scribes CLI."""
    ctx.obj = Config()


@main.command()
@click.pass_obj
def clone(config):
    """."""
    clone_all_repositories(config, CommandRunner())


def update_single_repository_with_sed(repo_path, sed_operation, pattern, dry_run):
    """Update a single repository using sed."""
    try:
        # Using subprocess to chain the commands
        cmd1 = subprocess.Popen(
            ["git", "ls-files", "-z", pattern], cwd=repo_path, stdout=subprocess.PIPE
        )
        cmd2 = subprocess.Popen(
            ["xargs", "-0", "sed", "-i", sed_operation],
            cwd=repo_path,
            stdin=cmd1.stdout,
            stdout=subprocess.PIPE,
        )
        cmd2.communicate()

        if dry_run:
            result = subprocess.run(["git", "diff", "--exit-code"], cwd=repo_path)
            if result.returncode != 0:
                print(f"[yellow]Changes detected in {repo_path}[/yellow]")
            subprocess.run(["git", "restore", "."], cwd=repo_path)
        else:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            if status.stdout.strip():
                print(f"[green]Successfully updated {repo_path}[/green]")
            else:
                print(f"[blue]No changes to update in {repo_path}[/blue]")

    except Exception as e:
        print(f"[red]Error updating {repo_path}: {e}[/red]")


@main.command()
@click.argument("sed_operation", required=True)
@click.option(
    "--pattern",
    default="*",
    required=False,
    help='File pattern to target. Default is "*".',
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Run sed without actually changing files.",
)
@click.pass_obj
def sed(cli, sed_operation, pattern, dry_run):
    """Apply sed command to all repositories in parallel."""
    repo_dirs = cli.filtered_repo_dirs
    args_list = [(repo_dir, sed_operation, pattern, dry_run) for repo_dir in repo_dirs]
    execute_concurrently(update_single_repository_with_sed, args_list)


def restore_single_repository(repo_path):
    """Restore a single repository to its last committed state."""
    try:
        result = subprocess.run(
            ["git", "reset", "--hard"], cwd=repo_path, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"[green]Successfully restored {repo_path}[/green]")
        else:
            print(f"[red]Failed to restore {repo_path}[/red]\n{result.stderr}")
    except Exception as e:
        print(f"[red]Error restoring {repo_path}: {e}[/red]")


@main.command()
@click.pass_obj
def restore(cli):
    """Restore all repositories to their last committed state."""
    repo_dirs = cli.filtered_repo_dirs
    args_list = [(repo_dir,) for repo_dir in repo_dirs]
    execute_concurrently(restore_single_repository, args_list)


def commit_changes_in_repository(repo_path, branch_name, commit_message):
    """Commit changes in a single repository."""

    changes = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True
    )
    if not changes.stdout.strip():
        print(f"[blue]No changes to commit in {repo_path}[/blue]")
        return

    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        if status_result.stdout.strip():
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_path,
                capture_output=True,
            )

            subprocess.run(["git", "add", "-A"], cwd=repo_path)
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )

            if commit_result.returncode == 0:
                print(
                    f"[green]Successfully committed changes in {repo_path} on branch {branch_name}[/green]"  # noqa
                )
            else:
                print(
                    f"[red]Failed to commit in {repo_path}[/red]\n{commit_result.stderr}"  # noqa
                )
        else:
            print(f"[blue]No changes to commit in {repo_path}[/blue]")

    except Exception as e:
        print(f"[red]Error committing in {repo_path}: {e}[/red]")


def create_pr_in_repository(repo_path, title, body):
    """Create a pull request in a single repository using 'gh pr create'."""
    default_branch_response = subprocess.run(
        ["gh", "repo", "view", "--json", "defaultBranchRef"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    default_branch = json.loads(default_branch_response.stdout)["defaultBranchRef"][
        "name"
    ]
    current_branch_response = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    current_branch = current_branch_response.stdout.strip()
    if current_branch == default_branch:
        print(
            f"[blue]Skipping PR creation in {repo_path} because it is still on the default branch {default_branch}[/blue]"  # noqa
        )
        return

    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--head",
                current_branch,
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"[green]Successfully created PR in {repo_path}[/green]")
        else:
            print(f"[red]Failed to create PR in {repo_path}[/red]\n{result.stderr}")

    except Exception as e:
        print(f"[red]Error creating PR in {repo_path}: {e}[/red]")


@main.command()
@click.argument("branch_name", required=True)
@click.argument("commit_message", required=True)
@click.pass_obj
def commit(cli, branch_name, commit_message):
    """Commit all changes in the repositories."""
    args_list = [
        (repo_dir, branch_name, commit_message) for repo_dir in cli.filtered_repo_dirs
    ]
    execute_concurrently(commit_changes_in_repository, args_list)


@main.command()
@click.argument("title", required=True)
@click.option("--body", default="", help="Body of the pull request.")
@click.pass_obj
def pr(cli, title, body):
    """Create pull requests in all repositories using 'gh pr create'."""
    args_list = [(repo_dir, title, body) for repo_dir in cli.filtered_repo_dirs]
    execute_concurrently(create_pr_in_repository, args_list)


if __name__ == "__main__":
    main()
