import logging
from pathlib import Path


def read_version():
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent  # src/wallbot/utils/version.py -> raíz
        version_file = project_root / "VERSION"

        if version_file.exists():
            with open(version_file, "r") as file:
                version = file.readline().strip()
                logging.info("Version %s", version)
                return version
        else:
            logging.warning("VERSION file not found at %s", version_file)
            return "unknown"

    except Exception as e:
        logging.error("Error reading version: %s", str(e))
        return "unknown"
