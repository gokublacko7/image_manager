import json
from dataclasses import dataclass
from pathlib import Path

from image_dataset_manager.config import MASTER_DATASET_DIR, SETTINGS_PATH


@dataclass
class AppSettings:
    current_master_directory: Path
    master_directories: list[Path]
    export_directory: Path | None
    dark_theme: bool = False


class SettingsService:
    def __init__(self, settings_path: Path = SETTINGS_PATH) -> None:
        self.settings_path = settings_path
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings = self._load()
        self.save()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def set_current_master_directory(self, directory: Path) -> None:
        directory = directory.expanduser().resolve()
        directory.mkdir(parents=True, exist_ok=True)
        self._settings.current_master_directory = directory
        self._settings.master_directories = _dedupe_paths([directory, *self._settings.master_directories])
        self.save()

    def set_export_directory(self, directory: Path | None) -> None:
        if directory is not None:
            directory = directory.expanduser().resolve()
            directory.mkdir(parents=True, exist_ok=True)
        self._settings.export_directory = directory
        self.save()

    def set_dark_theme(self, enabled: bool) -> None:
        self._settings.dark_theme = enabled
        self.save()

    def save(self) -> None:
        payload = {
            "current_master_directory": str(self._settings.current_master_directory),
            "master_directories": [str(path) for path in self._settings.master_directories],
            "export_directory": str(self._settings.export_directory) if self._settings.export_directory else "",
            "dark_theme": self._settings.dark_theme,
        }
        self.settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load(self) -> AppSettings:
        default = AppSettings(
            current_master_directory=MASTER_DATASET_DIR,
            master_directories=[MASTER_DATASET_DIR],
            export_directory=None,
            dark_theme=False,
        )
        if not self.settings_path.exists():
            return default

        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

        master_directories = [
            Path(path).expanduser()
            for path in payload.get("master_directories", [])
            if str(path).strip()
        ]
        current = Path(payload.get("current_master_directory") or MASTER_DATASET_DIR).expanduser()
        export_value = str(payload.get("export_directory", "")).strip()
        export_directory = Path(export_value).expanduser() if export_value else None

        return AppSettings(
            current_master_directory=current,
            master_directories=_dedupe_paths([current, *master_directories, MASTER_DATASET_DIR]),
            export_directory=export_directory,
            dark_theme=bool(payload.get("dark_theme", False)),
        )


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    clean_paths: list[Path] = []
    for path in paths:
        key = str(path.expanduser().resolve()).casefold()
        if key not in seen:
            seen.add(key)
            clean_paths.append(path.expanduser().resolve())
    return clean_paths
