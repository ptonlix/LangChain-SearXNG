from pathlib import Path

from langchain_searxng.constants import PROJECT_ROOT_PATH


def _absolute_or_from_project_root(path: str) -> Path:
    if path.startswith("/"):
        return Path(path)
    return PROJECT_ROOT_PATH / path


docs_path: Path = PROJECT_ROOT_PATH / "docs"
