import os
import sys
from pathlib import Path

from src.wallbot.utils.version import read_version

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestReadVersion:

    def test_read_version_from_root(self):
        project_root = Path(__file__).parent.parent
        version_file = project_root / "VERSION"

        assert version_file.exists(), "El archivo VERSION debe existir en la raíz"

        with open(version_file, 'r') as f:
            expected_version = f.readline().strip()

        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)
            version = read_version()
            assert version == expected_version, f"Expected {expected_version}, got {version}"
        finally:
            os.chdir(original_cwd)

    def test_read_version_with_different_working_directory(self):
        project_root = Path(__file__).parent.parent
        src_dir = project_root / "src"

        original_cwd = os.getcwd()
        try:
            os.chdir(src_dir)
            version = read_version()

            version_file = project_root / "VERSION"
            with open(version_file, 'r') as f:
                expected_version = f.readline().strip()

            assert version == expected_version
        finally:
            os.chdir(original_cwd)
