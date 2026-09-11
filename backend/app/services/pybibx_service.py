from pathlib import Path

import pybibx

from backend.app.models.dataset_version import DatasetVersion


class PyBibXService:
    def run(self, dataset_version: DatasetVersion):
        if not dataset_version.storage_path:
            raise ValueError("Dataset version does not have a storage path.")

        file_path = Path(dataset_version.storage_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            db = "scopus"
        elif suffix in {".bib", ".txt"}:
            db = "scopus"
        else:
            raise ValueError(f"Unsupported dataset file format: {suffix}")

        return pybibx.pbx_probe(file_bib=str(file_path), db=db, del_duplicated=True)
