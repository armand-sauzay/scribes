import json
import os
from typing import Any


def save_to_json_file(
    data: dict[str, Any], output_directory: str, filename: str
) -> None:
    os.makedirs(output_directory, exist_ok=True)
    with open(os.path.join(output_directory, filename), "w") as f:
        json.dump(data, f)
