from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from PySide6.QtGui import QImage, QPixmap

from image_dataset_manager.config import SUPPORTED_IMAGE_EXTENSIONS, THUMBNAIL_SIZE


class ImageService:
    def list_images(self, folder_path: Path) -> list[Path]:
        if not folder_path.exists():
            return []
        return sorted(
            [
                path
                for path in folder_path.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
            ],
            key=lambda path: str(path.relative_to(folder_path)).casefold(),
        )

    def representative_image(self, folder_path: Path) -> Path | None:
        images = self.list_images(folder_path)
        return images[0] if images else None

    def pixmap_for_image(self, image_path: Path, size: int | None = THUMBNAIL_SIZE) -> QPixmap:
        try:
            with Image.open(image_path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                if size is not None:
                    image.thumbnail((size, size), Image.Resampling.LANCZOS)
                qimage = QImage(
                    image.tobytes("raw", "RGB"),
                    image.width,
                    image.height,
                    image.width * 3,
                    QImage.Format.Format_RGB888,
                )
                return QPixmap.fromImage(qimage.copy())
        except (OSError, UnidentifiedImageError):
            return QPixmap()
