from pathlib import Path

from image_dataset_manager.models.database import DatasetRepository, normalize_tags
from image_dataset_manager.models.dataset import Dataset
from image_dataset_manager.services.image_service import ImageService
from image_dataset_manager.services.storage_service import StorageService


class DatasetController:
    def __init__(
        self,
        repository: DatasetRepository,
        storage_service: StorageService,
        image_service: ImageService,
    ) -> None:
        self.repository = repository
        self.storage_service = storage_service
        self.image_service = image_service

    def import_dataset(self, source_folder: Path, name: str | None, tags: list[str]) -> Dataset:
        clean_tags = normalize_tags(tags)
        if not clean_tags:
            raise ValueError("At least one tag is required.")
        destination = self.storage_service.import_dataset(source_folder)
        return self.repository.add_dataset(destination, name, clean_tags)

    def datasets(self, selected_tags: list[str] | None = None) -> list[Dataset]:
        return self.repository.list_datasets(selected_tags)

    def dataset(self, dataset_id: int) -> Dataset | None:
        return self.repository.get_dataset(dataset_id)

    def all_tags(self) -> list[str]:
        return self.repository.all_tags()

    def images_for_dataset(self, dataset: Dataset) -> list[Path]:
        return self.image_service.list_images(dataset.folder_path)

    def thumbnail_for_dataset(self, dataset: Dataset):
        representative = self.image_service.representative_image(dataset.folder_path)
        if representative is None:
            return None
        return self.image_service.pixmap_for_image(representative)

    def thumbnail_for_image(self, image_path: Path):
        return self.image_service.pixmap_for_image(image_path)

    def update_tags(self, dataset_id: int, tags: list[str]) -> Dataset:
        clean_tags = normalize_tags(tags)
        if not clean_tags:
            raise ValueError("At least one tag is required.")
        self.repository.update_dataset_tags(dataset_id, clean_tags)
        dataset = self.repository.get_dataset(dataset_id)
        if dataset is None:
            raise ValueError("Dataset no longer exists.")
        return dataset

    def export_datasets(self, dataset_ids: list[int], zip_path: Path) -> None:
        datasets = [dataset for dataset_id in dataset_ids if (dataset := self.repository.get_dataset(dataset_id))]
        self.storage_service.export_datasets(datasets, zip_path)
