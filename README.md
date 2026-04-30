# Image Dataset Manager

A PySide6 desktop app for importing, tagging, filtering, viewing, and exporting image datasets. Each dataset is stored as a folder under a master storage directory, while metadata lives in SQLite.

## Project Structure

```text
image_dataset_manager/
  main.py                  # Application entry point
  config.py                # App paths and supported image formats
  models/
    database.py            # SQLite setup and repository operations
    dataset.py             # Dataset dataclass
  services/
    image_service.py       # Image discovery and RGB thumbnails
    storage_service.py     # Import and ZIP export logic
  controllers/
    dataset_controller.py  # MVC controller used by the UI
  views/
    dialogs.py             # Import/tag dialogs
    image_grid.py          # Reusable lazy thumbnail grid
    main_window.py         # Main dataset browser
    dataset_view.py        # Per-dataset image browser
```

Runtime data is created under:

```text
%USERPROFILE%\.image_dataset_manager\
  datasets\               # Master dataset storage
  datasets.sqlite3        # Metadata database
```

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m image_dataset_manager.main
```

## Features

- Import a folder of images into managed storage.
- Require tags on import and allow an optional custom dataset name.
- Browse datasets as a thumbnail grid without showing tags on the main grid.
- Filter datasets by tags.
- Open a dataset to view all images, filenames, tags, and edit tags.
- Select one or more datasets and export them as a ZIP preserving one folder per dataset.
- Uses RGB thumbnails for previews and loads thumbnails incrementally through a shared grid component.
