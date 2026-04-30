from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

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
