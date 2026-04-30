import sys

from PySide6.QtWidgets import QApplication

from image_dataset_manager.config import APP_DIR, database_path_for_master
from image_dataset_manager.controllers.dataset_controller import DatasetController
from image_dataset_manager.models.database import DatasetRepository
from image_dataset_manager.services.image_service import ImageService
from image_dataset_manager.services.settings_service import SettingsService
from image_dataset_manager.services.storage_service import StorageService
from image_dataset_manager.views.main_window import MainWindow


def main() -> int:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    settings_service = SettingsService()
    settings_service.settings.current_master_directory.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Image Dataset Manager")

    repository = DatasetRepository(database_path_for_master(settings_service.settings.current_master_directory))
    image_service = ImageService()
    storage_service = StorageService(
        image_service=image_service,
        master_directory=settings_service.settings.current_master_directory,
    )
    controller = DatasetController(
        repository=repository,
        storage_service=storage_service,
        image_service=image_service,
        settings_service=settings_service,
    )

    window = MainWindow(controller)
    window.resize(1180, 780)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
