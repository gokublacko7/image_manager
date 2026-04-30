from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Dataset:
    id: int
    folder_path: Path
    name: str | None = None
    tags: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.name.strip() if self.name and self.name.strip() else self.folder_path.name
