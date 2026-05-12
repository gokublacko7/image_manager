import sqlite3
from contextlib import closing
from pathlib import Path

from image_dataset_manager.config import DATABASE_PATH
from image_dataset_manager.models.dataset import Dataset


class DatasetRepository:
    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def switch_database(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS datasets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder_path TEXT NOT NULL UNIQUE,
                        name TEXT
                    );

                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE COLLATE NOCASE
                    );

                    CREATE TABLE IF NOT EXISTS dataset_tags (
                        dataset_id INTEGER NOT NULL,
                        tag_id INTEGER NOT NULL,
                        PRIMARY KEY (dataset_id, tag_id),
                        FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
                        FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
                    );
                    """
                )

    def add_dataset(self, folder_path: Path, name: str | None, tags: list[str]) -> Dataset:
        clean_tags = normalize_tags(tags)
        with closing(self._connect()) as connection:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO datasets (folder_path, name) VALUES (?, ?)",
                    (str(folder_path), clean_text(name)),
                )
                dataset_id = int(cursor.lastrowid)
                self._replace_tags(connection, dataset_id, clean_tags)
        return Dataset(dataset_id, folder_path, clean_text(name), clean_tags)

    def list_datasets(self, selected_tags: list[str] | None = None) -> list[Dataset]:
        selected_tags = normalize_tags(selected_tags or [])
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT id, folder_path, name FROM datasets ORDER BY COALESCE(NULLIF(name, ''), folder_path)"
            ).fetchall()
            datasets = [self._dataset_from_row(connection, row) for row in rows]

        if not selected_tags:
            return datasets

        wanted = {tag.casefold() for tag in selected_tags}
        return [
            dataset
            for dataset in datasets
            if wanted.issubset({tag.casefold() for tag in dataset.tags})
        ]

    def get_dataset(self, dataset_id: int) -> Dataset | None:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT id, folder_path, name FROM datasets WHERE id = ?",
                (dataset_id,),
            ).fetchone()
            return self._dataset_from_row(connection, row) if row else None

    def update_dataset_tags(self, dataset_id: int, tags: list[str]) -> None:
        with closing(self._connect()) as connection:
            with connection:
                self._replace_tags(connection, dataset_id, normalize_tags(tags))

    def delete_dataset(self, dataset_id: int) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
                connection.execute("DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM dataset_tags)")

    def all_tags(self) -> list[str]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT name FROM tags ORDER BY name COLLATE NOCASE").fetchall()
            return [str(row["name"]) for row in rows]

    def _dataset_from_row(self, connection: sqlite3.Connection, row: sqlite3.Row) -> Dataset:
        tag_rows = connection.execute(
            """
            SELECT tags.name
            FROM tags
            INNER JOIN dataset_tags ON dataset_tags.tag_id = tags.id
            WHERE dataset_tags.dataset_id = ?
            ORDER BY tags.name COLLATE NOCASE
            """,
            (row["id"],),
        ).fetchall()
        return Dataset(
            id=int(row["id"]),
            folder_path=Path(str(row["folder_path"])),
            name=str(row["name"]) if row["name"] else None,
            tags=[str(tag_row["name"]) for tag_row in tag_rows],
        )

    def _replace_tags(
        self,
        connection: sqlite3.Connection,
        dataset_id: int,
        tags: list[str],
    ) -> None:
        connection.execute("DELETE FROM dataset_tags WHERE dataset_id = ?", (dataset_id,))
        for tag in tags:
            connection.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
            tag_id = connection.execute("SELECT id FROM tags WHERE name = ? COLLATE NOCASE", (tag,)).fetchone()[
                "id"
            ]
            connection.execute(
                "INSERT OR IGNORE INTO dataset_tags (dataset_id, tag_id) VALUES (?, ?)",
                (dataset_id, tag_id),
            )
        connection.execute("DELETE FROM tags WHERE id NOT IN (SELECT tag_id FROM dataset_tags)")


def normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    clean_tags: list[str] = []
    for tag in tags:
        clean = tag.strip()
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            clean_tags.append(clean)
    return clean_tags


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
