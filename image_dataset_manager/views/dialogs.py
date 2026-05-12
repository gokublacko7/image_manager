from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from image_dataset_manager.controllers.dataset_controller import DatasetController
from image_dataset_manager.models.database import normalize_tags


class ImportDatasetDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import Dataset")
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse)

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(browse_button)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("required, comma separated")
        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Folder", folder_layout)
        form.addRow("Name", self.name_edit)
        form.addRow("Tags", self.tags_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)
        self.setMinimumWidth(560)

    @property
    def source_folder(self) -> Path:
        return Path(self.folder_edit.text())

    @property
    def dataset_name(self) -> str | None:
        name = self.name_edit.text().strip()
        return name or None

    @property
    def tags(self) -> list[str]:
        return normalize_tags(self.tags_edit.text().split(","))

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.folder_edit.setText(folder)

    def _validate(self) -> None:
        if not self.folder_edit.text().strip():
            self.error_label.setText("Choose a folder to import.")
            return
        if not self.tags:
            self.error_label.setText("Add at least one tag.")
            return
        self.accept()


class EditTagsDialog(QDialog):
    def __init__(self, tags: list[str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Tags")
        self.tags_edit = QLineEdit(", ".join(tags))
        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.error_label.setObjectName("errorLabel")

        form = QFormLayout()
        form.addRow("Tags", self.tags_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)
        self.setMinimumWidth(460)

    @property
    def tags(self) -> list[str]:
        return normalize_tags(self.tags_edit.text().split(","))

    def _validate(self) -> None:
        if not self.tags:
            self.error_label.setText("Add at least one tag.")
            return
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self, controller: DatasetController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Settings")

        self.master_combo = QComboBox()
        self.master_combo.setEditable(True)
        for directory in self.controller.master_directories():
            self.master_combo.addItem(str(directory))
        self.master_combo.setCurrentText(str(self.controller.current_master_directory()))
        self.master_combo.currentTextChanged.connect(self._update_space_bar)

        browse_master_button = QPushButton("Browse")
        browse_master_button.clicked.connect(self._browse_master)
        master_layout = QHBoxLayout()
        master_layout.addWidget(self.master_combo)
        master_layout.addWidget(browse_master_button)

        self.space_bar = QProgressBar()
        self.space_bar.setRange(0, 100)
        self.space_label = QLabel()
        self.space_label.setObjectName("mutedLabel")
        self.space_label.setWordWrap(True)

        self.export_edit = QLineEdit()
        export_directory = self.controller.export_directory()
        self.export_edit.setText(str(export_directory) if export_directory else "")
        self.export_edit.setPlaceholderText("Ask where to save on export")
        browse_export_button = QPushButton("Browse")
        browse_export_button.clicked.connect(self._browse_export)
        clear_export_button = QPushButton("Clear")
        clear_export_button.clicked.connect(self.export_edit.clear)
        export_layout = QHBoxLayout()
        export_layout.addWidget(self.export_edit)
        export_layout.addWidget(browse_export_button)
        export_layout.addWidget(clear_export_button)

        self.dark_theme_check = QCheckBox("Use dark theme")
        self.dark_theme_check.setChecked(self.controller.dark_theme())

        self.error_label = QLabel()
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)

        form = QFormLayout()
        form.addRow("Master folder", master_layout)
        form.addRow("", self.space_bar)
        form.addRow("", self.space_label)
        form.addRow("Export folder", export_layout)
        form.addRow("", self.dark_theme_check)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)
        self.setMinimumWidth(700)
        self._update_space_bar()

    def _browse_master(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Master Dataset Folder",
            self.master_combo.currentText().strip() or str(self.controller.current_master_directory()),
        )
        if folder:
            self.master_combo.setCurrentText(folder)

    def _browse_export(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Export Folder",
            self.export_edit.text().strip() or str(Path.home()),
        )
        if folder:
            self.export_edit.setText(folder)

    def _apply(self) -> None:
        master_value = self.master_combo.currentText().strip()
        if not master_value:
            self.error_label.setText("Choose a master folder.")
            return

        try:
            self.controller.set_master_directory(Path(master_value))
            export_value = self.export_edit.text().strip()
            self.controller.set_export_directory(Path(export_value) if export_value else None)
            self.controller.set_dark_theme(self.dark_theme_check.isChecked())
        except Exception as error:
            self.error_label.setText(str(error))
            return
        self.accept()

    def _update_space_bar(self) -> None:
        path_text = self.master_combo.currentText().strip()
        if not path_text:
            self.space_bar.setValue(0)
            self.space_label.setText("Choose a master folder")
            return

        try:
            usage = self.controller.storage_service.disk_usage_for(Path(path_text))
        except OSError:
            self.space_bar.setValue(0)
            self.space_label.setText("Space unavailable")
            return

        used_percent = int((usage.used / usage.total) * 100) if usage.total else 0
        self.space_bar.setValue(used_percent)
        self.space_bar.setFormat(f"{used_percent}% used")
        self.space_label.setText(f"{_format_bytes(usage.free)} free of {_format_bytes(usage.total)}")


def _format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024


class ImageViewerDialog(QDialog):
    def __init__(
        self,
        image_paths: list[Path],
        start_index: int,
        controller: DatasetController,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.image_paths = image_paths
        self.index = start_index
        self.controller = controller
        self.setWindowTitle("Image Viewer")

        self.title_label = QLabel()
        self.title_label.setObjectName("detailTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setObjectName("fullImage")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_container = QWidget()
        scroll_layout = QVBoxLayout(scroll_container)
        scroll_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(scroll_container)

        self.previous_button = QPushButton("Previous")
        self.previous_button.clicked.connect(self._previous)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self._next)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        controls = QHBoxLayout()
        controls.addWidget(self.previous_button)
        controls.addWidget(self.next_button)
        controls.addStretch(1)
        controls.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_label)
        layout.addWidget(scroll, stretch=1)
        layout.addLayout(controls)
        self.resize(1100, 760)
        self._load_current()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Left:
            self._previous()
            return
        if event.key() == Qt.Key.Key_Right:
            self._next()
            return
        super().keyPressEvent(event)

    def _previous(self) -> None:
        if self.index > 0:
            self.index -= 1
            self._load_current()

    def _next(self) -> None:
        if self.index < len(self.image_paths) - 1:
            self.index += 1
            self._load_current()

    def _load_current(self) -> None:
        image_path = self.image_paths[self.index]
        pixmap = self.controller.full_size_pixmap_for_image(image_path)
        self.image_label.setPixmap(pixmap)
        self.title_label.setText(f"{image_path.name} ({self.index + 1} of {len(self.image_paths)})")
        self.previous_button.setEnabled(self.index > 0)
        self.next_button.setEnabled(self.index < len(self.image_paths) - 1)
