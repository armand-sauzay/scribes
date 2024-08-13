# Scribes

Scribes is a distributed refactoring tool that enables you to clone repositories and apply sweeping changes.

## Getting started

### Pre-requisites

Scribes relies on git and the [GitHub cli](https://github.com/cli/cli) (gh). You
can follow install instructions for gh [here](https://github.com/cli/cli). You
can then authenticate using `gh auth login`.

### Usage

Let's say you want to clone all repos in an organization and apply pre-commit autoupdate to all repos.

1. `pip install scribes`

2. Run the following commands
   ```bash
   scribes search
   scribes filter --contains-file .pre-commit-config.yaml
   scribes clone --limit 10
   scribes run "git branch"
   scribes run "git checkout -b pre-commit-autoupdate"
   scribes run "pre-commit autoupdate"
   scribes run "git add .pre-commit-config.yaml"
   scribes run "git commit -m 'chore: autoupdate pre-commit'"
   scribes run "git push origin pre-commit-autoupdate"
   scribes run "gh pr create --title 'chore: autoupdate pre-commit' --body 'Autoupdate pre-commit' --base main --head pre-commit-autoupdate"
   ```

🎉 There it is, you have created PRs to autoupdate pre-commit in all repos that contain a `.pre-commit-config.yaml` file.

### To be implemented

- [] Filter functionalities outside of --contains-file
- [] Add visualization
- [] Create documentation to apply commands to only modified repositories (like `gh pr create` commands)
- [] Encapsulate typical workflow commands (like the one above) in a single command
