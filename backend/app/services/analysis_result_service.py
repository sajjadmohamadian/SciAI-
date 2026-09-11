from pathlib import Path
import pandas as pd

from backend.app.models.analysis import Analysis


class AnalysisResultService:
    """Service for reading analysis results."""

    def read_records(self, analysis: Analysis) -> pd.DataFrame:
        if not analysis.result_path:
            raise ValueError(
                f"Analysis '{analysis.id}' has no result path."
            )

        path = Path(analysis.result_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Analysis result not found: {path}"
            )

        if path.suffix.lower() != ".csv":
            raise ValueError(
                f"Unsupported result format: {path.suffix}"
            )

        return pd.read_csv(path)

    def summary(self, analysis: Analysis) -> dict:
        data = self.read_records(analysis)

        return {
            "analysis_id": str(analysis.id),
            "status": analysis.status,
            "rows": int(data.shape[0]),
            "columns": int(data.shape[1]),
            "column_names": list(data.columns),
        }