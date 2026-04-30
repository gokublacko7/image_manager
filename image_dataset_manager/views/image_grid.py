from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QLabel,
    QSizePolicy,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from image_dataset_manager.config import GRID_CELL_HEIGHT, GRID_CELL_WIDTH, THUMBNAIL_SIZE
from image_dataset_manager.services.image_service import ImageService


class ImageCard(QFrame):
    clicked = Signal(object)
    selection_changed = Signal(object, bool)

    def __init__(self, item: Any, title: str, selectable: bool) -> None:
        super().__init__()
        self.item = item
        self.setObjectName("imageCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(GRID_CELL_WIDTH, GRID_CELL_HEIGHT)

        self.checkbox = QCheckBox()
        self.checkbox.setVisible(selectable)
        self.checkbox.stateChanged.connect(self._emit_selection)

        self.image_label = QLabel("Loading")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        self.image_label.setObjectName("thumbnail")

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("cardTitle")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.addWidget(self.checkbox, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:
        if self.checkbox.geometry().contains(event.position().toPoint()):
            super().mousePressEvent(event)
            return
        self.clicked.emit(self.item)
        super().mousePressEvent(event)

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap and not pixmap.isNull():
            self.image_label.setPixmap(pixmap)
            self.image_label.setText("")
        else:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("No preview")

    def is_selected(self) -> bool:
        return self.checkbox.isChecked()

    def _emit_selection(self) -> None:
        self.selection_changed.emit(self.item, self.checkbox.isChecked())


class ImageGrid(QScrollArea):
    item_clicked = Signal(object)
    selection_changed = Signal()

    def __init__(self, image_service: ImageService, selectable: bool = False) -> None:
        super().__init__()
        self.image_service = image_service
        self.selectable = selectable
        self.cards: list[ImageCard] = []
        self._items: list[Any] = []
        self._image_path_for: Callable[[Any], Path | None] | None = None
        self._title_for: Callable[[Any], str] | None = None
        self._load_index = 0

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(18, 18, 18, 18)
        self.grid.setSpacing(16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.setWidget(self.container)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._load_next_batch)

    def set_items(
        self,
        items: Sequence[Any],
        image_path_for: Callable[[Any], Path | None],
        title_for: Callable[[Any], str],
    ) -> None:
        self.clear()
        self._items = list(items)
        self._image_path_for = image_path_for
        self._title_for = title_for
        self._load_index = 0

        for index, item in enumerate(self._items):
            card = ImageCard(item, title_for(item), self.selectable)
            card.clicked.connect(self.item_clicked.emit)
            card.selection_changed.connect(lambda *_: self.selection_changed.emit())
            row, column = divmod(index, self._column_count())
            self.grid.addWidget(card, row, column)
            self.cards.append(card)

        if self._items:
            self._timer.start(1)

    def selected_items(self) -> list[Any]:
        return [card.item for card in self.cards if card.is_selected()]

    def clear(self) -> None:
        self._timer.stop()
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.cards.clear()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.cards:
            self._reflow()

    def _load_next_batch(self) -> None:
        if self._image_path_for is None:
            self._timer.stop()
            return

        batch_size = 8
        end = min(self._load_index + batch_size, len(self.cards))
        for index in range(self._load_index, end):
            image_path = self._image_path_for(self.cards[index].item)
            pixmap = self.image_service.pixmap_for_image(image_path) if image_path else None
            self.cards[index].set_pixmap(pixmap)

        self._load_index = end
        if self._load_index >= len(self.cards):
            self._timer.stop()

    def _column_count(self) -> int:
        available_width = max(1, self.viewport().width() - 40)
        return max(1, available_width // (GRID_CELL_WIDTH + self.grid.spacing()))

    def _reflow(self) -> None:
        for index, card in enumerate(self.cards):
            self.grid.removeWidget(card)
            row, column = divmod(index, self._column_count())
            self.grid.addWidget(card, row, column)
