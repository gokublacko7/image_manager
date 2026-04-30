import shutil
import zipfile
from pathlib import Path

from image_dataset_manager.config import MASTER_DATASET_DIR
from image_dataset_manager.models.dataset import Dataset
from image_dataset_manager.services.image_service import ImageService


class StorageService:
    def __init__(
        self,
        image_service: ImageService,
        master_directory: Path = MASTER_DATASET_DIR,
    ) -> None:
        self.image_service = image_service
        self.master_directory = master_directory
        self.master_directory.mkdir(parents=True, exist_ok=True)

    def import_dataset(self, source_folder: Path) -> Path:
        if not source_folder.exists() or not source_folder.is_dir():
            raise ValueError("Selected path is not a folder.")
        if not self.image_service.list_images(source_folder):
            raise ValueError("The selected folder does not contain supported image files.")

        destination = self._unique_destination(source_folder.name)
        shutil.copytree(source_folder, destination)
        return destination

    def export_datasets(self, datasets: list[Dataset], zip_path: Path) -> None:
        if not datasets:
            raise ValueError("Select at least one dataset to export.")

        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for dataset in datasets:
                root_name = dataset.folder_path.name
                for file_path in self.image_service.list_images(dataset.folder_path):
                    relative_path = Path(root_name) / file_path.relative_to(dataset.folder_path)
                    archive.write(file_path, relative_path.as_posix())

    def _unique_destination(self, folder_name: str) -> Path:
        safe_name = "".join(char if char.isalnum() or char in (" ", "-", "_", ".") else "_" for char in folder_name)
        safe_name = safe_name.strip(" .") or "dataset"
        candidate = self.master_directory / safe_name
        suffix = 1
        while candidate.exists():
            suffix += 1
            candidate = self.master_directory / f"{safe_name}_{suffix}"
        return candidate
