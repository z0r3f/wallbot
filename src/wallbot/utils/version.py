import logging
from pathlib import Path


def read_version() -> str:
    try:
        current_file = Path(__file__).resolve()
        # src/wallbot/utils/version.py -> utils -> wallbot -> src -> raíz del proyecto
        project_root = current_file.parent.parent.parent.parent
        version_file = project_root / "VERSION"

        if version_file.exists():
            with open(version_file, "r", encoding="utf-8") as file:
                version = file.readline().strip()
                return version
        else:
            logging.warning("VERSION file not found at %s", version_file)
            return "unknown"

    except Exception as e:
        logging.error("Error reading version: %s", e)
        return "unknown"
