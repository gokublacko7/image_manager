from pathlib import Path


APP_DIR = Path.home() / ".image_dataset_manager"
MASTER_DATASET_DIR = APP_DIR / "datasets"
DATABASE_PATH = APP_DIR / "datasets.sqlite3"

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
