from pathlib import Path
from src.wallbot.utils.version import read_version


class TestReadVersion:

    def test_version_file_exists(self):
        project_root = Path(__file__).resolve().parent.parent
        version_file = project_root / "VERSION"
        assert version_file.exists(), "El archivo VERSION debe existir en la raíz"

    def test_read_version_returns_correct_string(self):
        project_root = Path(__file__).resolve().parent.parent
        version_file = project_root / "VERSION"

        with open(version_file, "r", encoding="utf-8") as f:
            expected_version = f.readline().strip()

        version = read_version()
        assert version == expected_version, f"Se esperaba {expected_version}, pero se obtuvo {version}"
        assert version != "unknown", "La versión no debería ser 'unknown'"
