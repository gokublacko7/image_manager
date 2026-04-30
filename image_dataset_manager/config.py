from pathlib import Path


APP_DIR = Path.home() / ".image_dataset_manager"
MASTER_DATASET_DIR = APP_DIR / "datasets"
DATABASE_PATH = APP_DIR / "datasets.sqlite3"
SETTINGS_PATH = APP_DIR / "settings.json"
CUSTOM_DATABASE_NAME = ".image_manager.sqlite3"


def database_path_for_master(master_directory: Path) -> Path:
    if master_directory.resolve() == MASTER_DATASET_DIR.resolve():
        return DATABASE_PATH
    return master_directory / CUSTOM_DATABASE_NAME

SUPPORTED_IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}

THUMBNAIL_SIZE = 180
GRID_CELL_WIDTH = 220
GRID_CELL_HEIGHT = 245
