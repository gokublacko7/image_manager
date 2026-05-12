from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from image_dataset_manager.controllers.dataset_controller import DatasetController
from image_dataset_manager.models.dataset import Dataset
from image_dataset_manager.views.dialogs import EditTagsDialog, ImageViewerDialog
from image_dataset_manager.views.image_grid import ImageGrid


class DatasetView(QWidget):
    back_requested = Signal()
    tags_updated = Signal()

    def __init__(self, controller: DatasetController) -> None:
        super().__init__()
        self.controller = controller
        self.dataset: Dataset | None = None

        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.back_requested.emit)
        self.title_label = QLabel()
        self.title_label.setObjectName("detailTitle")
        self.tags_label = QLabel()
        self.tags_label.setObjectName("detailTags")
        self.tags_label.setWordWrap(True)
        self.edit_tags_button = QPushButton("Edit Tags")
        self.edit_tags_button.clicked.connect(self._edit_tags)
        self.delete_images_button = QPushButton("Delete Selected Images")
        self.delete_images_button.clicked.connect(self._delete_selected_images)

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(14, 12, 14, 12)
        top_layout.addWidget(self.back_button)
        top_layout.addWidget(self.title_label, stretch=1)
        top_layout.addWidget(self.tags_label, stretch=2)
        top_layout.addWidget(self.delete_images_button)
        top_layout.addWidget(self.edit_tags_button)

        self.grid = ImageGrid(controller.image_service, selectable=True)
        self.grid.item_clicked.connect(self._open_image_viewer)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(top_bar)
        layout.addWidget(self.grid, stretch=1)

    def set_dataset(self, dataset: Dataset) -> None:
        refreshed = self.controller.dataset(dataset.id)
        if refreshed is None:
            return
        self.dataset = refreshed
        self.title_label.setText(refreshed.display_name)
        self.tags_label.setText("Tags: " + ", ".join(refreshed.tags))
        images = self.controller.images_for_dataset(refreshed)
        self.images = images
        self.grid.set_items(
            images,
            image_path_for=lambda path: path,
            title_for=lambda path: path.name,
        )

    def _edit_tags(self) -> None:
        if self.dataset is None:
            return
        dialog = EditTagsDialog(self.dataset.tags, self)
        if dialog.exec():
            self.dataset = self.controller.update_tags(self.dataset.id, dialog.tags)
            self.tags_label.setText("Tags: " + ", ".join(self.dataset.tags))
            self.tags_updated.emit()

    def _open_image_viewer(self, image_path) -> None:
        if not getattr(self, "images", None):
            return
        try:
            start_index = self.images.index(image_path)
        except ValueError:
            start_index = 0
        ImageViewerDialog(self.images, start_index, self.controller, self).exec()

    def _delete_selected_images(self) -> None:
        selected_images = self.grid.selected_items()
        if not selected_images:
            QMessageBox.information(self, "Delete Images", "Select one or more images first.")
            return
        count = len(selected_images)
        answer = QMessageBox.question(
            self,
            "Delete Images",
            f"Delete {count} selected image(s)? This removes them from disk.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.controller.delete_images(selected_images)
        if self.dataset is not None:
            self.set_dataset(self.dataset)
