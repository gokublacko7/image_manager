from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from image_dataset_manager.controllers.dataset_controller import DatasetController
from image_dataset_manager.models.dataset import Dataset
from image_dataset_manager.views.dataset_view import DatasetView
from image_dataset_manager.views.dialogs import ImportDatasetDialog
from image_dataset_manager.views.image_grid import ImageGrid


class MainWindow(QMainWindow):
    def __init__(self, controller: DatasetController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Image Dataset Manager")

        self.stack = QStackedWidget()
        self.main_page = self._build_main_page()
        self.dataset_view = DatasetView(controller)
        self.dataset_view.back_requested.connect(self._show_main)
        self.dataset_view.tags_updated.connect(self._reload_everything)
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.dataset_view)
        self.setCentralWidget(self.stack)

        self._apply_styles()
        self._reload_everything()

    def _build_main_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(14, 12, 14, 12)

        title = QLabel("Datasets")
        title.setObjectName("appTitle")
        self.selection_label = QLabel("No datasets selected")
        self.selection_label.setObjectName("mutedLabel")
        import_button = QPushButton("Import Dataset")
        import_button.clicked.connect(self._import_dataset)
        export_button = QPushButton("Export Selected")
        export_button.clicked.connect(self._export_selected)

        top_layout.addWidget(title)
        top_layout.addWidget(self.selection_label, stretch=1)
        top_layout.addWidget(import_button)
        top_layout.addWidget(export_button)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        sidebar = self._build_sidebar()
        self.dataset_grid = ImageGrid(self.controller.image_service, selectable=True)
        self.dataset_grid.item_clicked.connect(self._open_dataset)
        self.dataset_grid.selection_changed.connect(self._update_selection_label)
        splitter.addWidget(sidebar)
        splitter.addWidget(self.dataset_grid)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 920])

        outer.addWidget(top_bar)
        outer.addWidget(splitter, stretch=1)
        return page

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label = QLabel("Filter by Tags")
        label.setObjectName("sectionLabel")
        self.clear_filters_button = QPushButton("Clear")
        self.clear_filters_button.clicked.connect(self._clear_filters)
        self.tag_list = QListWidget()
        self.tag_list.itemChanged.connect(self._reload_datasets)

        layout.addWidget(label)
        layout.addWidget(self.tag_list, stretch=1)
        layout.addWidget(self.clear_filters_button)
        return sidebar

    def _reload_everything(self) -> None:
        selected_tags = self._selected_tags()
        self.tag_list.blockSignals(True)
        self.tag_list.clear()
        for tag in self.controller.all_tags():
            item = QListWidgetItem(tag)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if tag in selected_tags else Qt.CheckState.Unchecked)
            self.tag_list.addItem(item)
        self.tag_list.blockSignals(False)
        self._reload_datasets()

    def _reload_datasets(self) -> None:
        selected_tags = self._selected_tags()
        datasets = self.controller.datasets(selected_tags)
        self.dataset_grid.set_items(
            datasets,
            image_path_for=lambda dataset: self.controller.image_service.representative_image(dataset.folder_path),
            title_for=lambda dataset: dataset.display_name,
        )
        self._update_selection_label()

    def _selected_tags(self) -> list[str]:
        if not hasattr(self, "tag_list"):
            return []
        tags: list[str] = []
        for index in range(self.tag_list.count()):
            item = self.tag_list.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                tags.append(item.text())
        return tags

    def _clear_filters(self) -> None:
        self.tag_list.blockSignals(True)
        for index in range(self.tag_list.count()):
            self.tag_list.item(index).setCheckState(Qt.CheckState.Unchecked)
        self.tag_list.blockSignals(False)
        self._reload_datasets()

    def _import_dataset(self) -> None:
        dialog = ImportDatasetDialog(self)
        if not dialog.exec():
            return
        try:
            self.controller.import_dataset(dialog.source_folder, dialog.dataset_name, dialog.tags)
        except Exception as error:
            QMessageBox.critical(self, "Import Failed", str(error))
            return
        self._reload_everything()

    def _open_dataset(self, dataset: Dataset) -> None:
        self.dataset_view.set_dataset(dataset)
        self.stack.setCurrentWidget(self.dataset_view)

    def _show_main(self) -> None:
        self.stack.setCurrentWidget(self.main_page)
        self._reload_everything()

    def _export_selected(self) -> None:
        selected = self.dataset_grid.selected_items()
        if not selected:
            QMessageBox.information(self, "Export Datasets", "Select one or more datasets first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Selected Datasets",
            str(Path.home() / "datasets.zip"),
            "ZIP files (*.zip)",
        )
        if not path:
            return
        zip_path = Path(path)
        if zip_path.suffix.lower() != ".zip":
            zip_path = zip_path.with_suffix(".zip")
        try:
            self.controller.export_datasets([dataset.id for dataset in selected], zip_path)
        except Exception as error:
            QMessageBox.critical(self, "Export Failed", str(error))
            return
        QMessageBox.information(self, "Export Complete", f"Exported {len(selected)} dataset(s).")

    def _update_selection_label(self) -> None:
        if not hasattr(self, "selection_label"):
            return
        count = len(self.dataset_grid.selected_items())
        self.selection_label.setText(f"{count} selected" if count else "No datasets selected")

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f6f7f9;
                color: #17202a;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10pt;
            }
            QPushButton {
                background: #2f6fed;
                border: 0;
                border-radius: 6px;
                color: white;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: #255ecf;
            }
            #topBar {
                background: white;
                border-bottom: 1px solid #d8dde6;
            }
            #sidebar {
                background: #eef2f6;
                border-right: 1px solid #d8dde6;
            }
            #appTitle, #detailTitle {
                font-size: 18pt;
                font-weight: 650;
            }
            #sectionLabel {
                font-weight: 650;
            }
            #mutedLabel, #detailTags {
                color: #5d6878;
            }
            #imageCard {
                background: white;
                border: 1px solid #d8dde6;
                border-radius: 8px;
            }
            #imageCard:hover {
                border-color: #2f6fed;
            }
            #thumbnail {
                background: #edf0f4;
                border-radius: 6px;
                color: #697487;
            }
            #cardTitle {
                font-weight: 600;
            }
            #errorLabel {
                color: #ba1a1a;
            }
            QListWidget {
                background: white;
                border: 1px solid #d8dde6;
                border-radius: 6px;
                padding: 4px;
            }
            QLineEdit {
                background: white;
                border: 1px solid #c9d1dc;
                border-radius: 5px;
                padding: 7px;
            }
            """
        )
