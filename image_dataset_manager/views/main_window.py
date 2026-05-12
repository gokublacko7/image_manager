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
from image_dataset_manager.views.dialogs import ImportDatasetDialog, SettingsDialog
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
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self._delete_selected_datasets)
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self._open_settings)

        top_layout.addWidget(title)
        top_layout.addWidget(self.selection_label, stretch=1)
        top_layout.addWidget(import_button)
        top_layout.addWidget(export_button)
        top_layout.addWidget(delete_button)
        top_layout.addWidget(settings_button)

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

        export_directory = self.controller.export_directory()
        suggested_path = (
            export_directory / "datasets.zip"
            if export_directory
            else Path.home() / "datasets.zip"
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Selected Datasets",
            str(suggested_path),
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
        self.controller.set_export_directory(zip_path.parent)
        QMessageBox.information(self, "Export Complete", f"Exported {len(selected)} dataset(s).")

    def _delete_selected_datasets(self) -> None:
        selected = self.dataset_grid.selected_items()
        if not selected:
            QMessageBox.information(self, "Delete Datasets", "Select one or more datasets first.")
            return
        count = len(selected)
        answer = QMessageBox.question(
            self,
            "Delete Datasets",
            f"Delete {count} selected dataset(s)? This removes their folders and images from disk.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.controller.delete_datasets([dataset.id for dataset in selected])
        except Exception as error:
            QMessageBox.critical(self, "Delete Failed", str(error))
            return
        self._reload_everything()

    def _update_selection_label(self) -> None:
        if not hasattr(self, "selection_label"):
            return
        count = len(self.dataset_grid.selected_items())
        self.selection_label.setText(f"{count} selected" if count else "No datasets selected")

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.controller, self)
        if not dialog.exec():
            return
        self._apply_styles()
        self.stack.setCurrentWidget(self.main_page)
        self._reload_everything()

    def _apply_styles(self) -> None:
        if self.controller.dark_theme():
            self.setStyleSheet(
                """
            QMainWindow, QWidget {
                background: #0f141b;
                color: #edf2f7;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10pt;
            }
            QPushButton {
                background: #4f8cff;
                border: 1px solid #6ea0ff;
                border-radius: 6px;
                color: white;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #3f7bef;
            }
            QPushButton:pressed {
                background: #3169d2;
            }
            #topBar {
                background: #161d27;
                border-bottom: 1px solid #2b3544;
            }
            #sidebar {
                background: #111923;
                border-right: 1px solid #2b3544;
            }
            #appTitle, #detailTitle {
                font-size: 19pt;
                font-weight: 700;
                background: transparent;
            }
            #sectionLabel {
                color: #d8e2ef;
                font-size: 10pt;
                font-weight: 700;
                padding-top: 4px;
                background: transparent;
            }
            #mutedLabel, #detailTags {
                color: #aab6c6;
                background: transparent;
            }
            #imageCard {
                background: #18212d;
                border: 1px solid #2f3b4d;
                border-radius: 8px;
            }
            #imageCard:hover {
                background: #1d2938;
                border-color: #6ea0ff;
            }
            #thumbnail {
                background: #0d1218;
                border-radius: 6px;
                color: #9ca8b8;
            }
            #cardTitle {
                font-weight: 600;
                background: transparent;
            }
            #errorLabel {
                color: #fca5a5;
                background: transparent;
            }
            QLabel {
                background: transparent;
            }
            QListWidget, QLineEdit, QComboBox {
                background: #0d1218;
                border: 1px solid #303b4c;
                border-radius: 6px;
                padding: 7px;
                color: #edf2f7;
                selection-background-color: #355f9f;
            }
            QProgressBar {
                background: #0d1218;
                border: 1px solid #303b4c;
                border-radius: 6px;
                height: 18px;
                text-align: center;
                color: #edf2f7;
            }
            QProgressBar::chunk {
                background: #40c4aa;
                border-radius: 5px;
            }
            QCheckBox {
                spacing: 8px;
                background: transparent;
            }
            QSplitter::handle {
                background: #202a38;
            }
            """
            )
            return

        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f4f6f8;
                color: #1b2633;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10pt;
            }
            QPushButton {
                background: #2364d2;
                border: 1px solid #1f5abb;
                border-radius: 6px;
                color: white;
                padding: 8px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1d57bb;
            }
            QPushButton:pressed {
                background: #17489e;
            }
            #topBar {
                background: #ffffff;
                border-bottom: 1px solid #dde4ed;
            }
            #sidebar {
                background: #e9eef5;
                border-right: 1px solid #d5dde8;
            }
            #appTitle, #detailTitle {
                font-size: 19pt;
                font-weight: 700;
                background: transparent;
            }
            #sectionLabel {
                color: #2c3a4b;
                font-size: 10pt;
                font-weight: 700;
                padding-top: 4px;
                background: transparent;
            }
            #mutedLabel, #detailTags {
                color: #657386;
                background: transparent;
            }
            #imageCard {
                background: #ffffff;
                border: 1px solid #d9e1eb;
                border-radius: 8px;
            }
            #imageCard:hover {
                background: #fbfdff;
                border-color: #2364d2;
            }
            #thumbnail {
                background: #eef3f8;
                border-radius: 6px;
                color: #6b7789;
            }
            #cardTitle {
                font-weight: 600;
                background: transparent;
            }
            #errorLabel {
                color: #ba1a1a;
                background: transparent;
            }
            QLabel {
                background: transparent;
            }
            QListWidget {
                background: #ffffff;
                border: 1px solid #d3dce8;
                border-radius: 6px;
                padding: 4px;
                selection-background-color: #dce9ff;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #c9d4e2;
                border-radius: 6px;
                padding: 7px;
            }
            QComboBox {
                background: #ffffff;
                border: 1px solid #c9d4e2;
                border-radius: 6px;
                padding: 6px;
            }
            QProgressBar {
                background: #ffffff;
                border: 1px solid #c9d4e2;
                border-radius: 6px;
                height: 18px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #1aa38a;
                border-radius: 5px;
            }
            QCheckBox {
                spacing: 8px;
                background: transparent;
            }
            QSplitter::handle {
                background: #dbe3ed;
            }
            """
        )
