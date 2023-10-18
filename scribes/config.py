import json
import os

import yaml


class Config:
    def __init__(self, config_path: str = "configuration.yaml"):
        self.load(config_path)

    def load(self, config_path: str) -> None:
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        clone_config = data.get("clone", {})
        self.organization_name = clone_config.get("organization_name")
        self.include = clone_config.get("include")
        self.exclude = clone_config.get("exclude")
        self.output_directory = clone_config.get("output_directory")
        self.include_forks = clone_config.get("include_forks", False)
        self.include_private = clone_config.get("include_private", True)
        self.include_archived = clone_config.get("include_archived", False)

    @property
    def filtered_repo_dirs(self) -> set[str]:
        """Load the list of filtered repository directories from the saved JSON file."""
        with open(
            os.path.join(self.output_directory, "filtered_repositories.json"), "r"
        ) as f:
            filtered_repos = json.load(f)
        return {
            os.path.join(self.output_directory, repo["nameWithOwner"])
            for repo in filtered_repos
        }
