import sys

from PySide6.QtWidgets import QApplication

from image_dataset_manager.config import APP_DIR, MASTER_DATASET_DIR
from image_dataset_manager.controllers.dataset_controller import DatasetController
from image_dataset_manager.models.database import DatasetRepository
from image_dataset_manager.services.image_service import ImageService
from image_dataset_manager.services.storage_service import StorageService
from image_dataset_manager.views.main_window import MainWindow


def main() -> int:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    MASTER_DATASET_DIR.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Image Dataset Manager")

    repository = DatasetRepository()
    image_service = ImageService()
    storage_service = StorageService(image_service=image_service)
    controller = DatasetController(
        repository=repository,
        storage_service=storage_service,
        image_service=image_service,
    )

    window = MainWindow(controller)
    window.resize(1180, 780)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
