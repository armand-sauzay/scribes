# Scribes

Scribes enables you to clone repositories and apply sweeping changes.

## Getting started

### Pre-requisites

Scribes relies on git and the [GitHub cli](https://github.com/cli/cli) (gh). You
can follow install instructions for gh [here](https://github.com/cli/cli). You
can then authenticate using `gh auth login`.

### Usage

Let's say you want to clone all repos in an organization and apply a sed command
to all repos, replacing `bar` by `foo`, commit and create PRs.

1. `pip install scribes`

2. Create a configuration file called configuration.yaml, such as the following:

   ```yaml
   clone:
     organization_name: "my-organization"
     include: "^my-organization/tf-"
     exclude: "^my-organization/tf-bar-.*"
     output_directory: "output"
     include_forks: false
     include_archived: false
     include_private: false
   ```

3. Run the following commands
   ```bash
   scribes clone
   scribes sed `s/bar/foo/g`
   scribes commit "branch" "commit message"
   scribes pr "title" --body "body"
   ```

🎉 There it is, you have created PRs in all repos that contain `bar` in their
content and created PRs in all repos with the changes
