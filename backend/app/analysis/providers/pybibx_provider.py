from pathlib import Path
from typing import Any

import pybibx

from backend.app.analysis.parsers.wos_parser import parse_wos_tagged_text


class PyBibXProvider:
    capability = 'citation.author_h_index'
    package = 'PyBibX'
    version = '5.9.5'

    def calculate(
        self,
        file_path: str | Path,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        parameters = parameters or {}
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f'Dataset file not found: {path}')

        suffix = path.suffix.lower()

        if suffix not in {'.csv', '.bib', '.txt', '.ciw'}:
            raise ValueError(f'Unsupported dataset file format: {suffix}')

        if suffix in {'.txt', '.ciw'}:
            df = parse_wos_tagged_text(path)

            pbx = pybibx.bibliometrix.from_dataframe(
                df,
                db='wos',
                del_duplicated=True,
            )
        else:
            pbx = pybibx.pbx_probe(
                file_bib=str(path),
                db='scopus',
                del_duplicated=True,
            )

        h_indices = pbx.h_index()
        authors = list(pbx.u_aut)

        if len(authors) != len(h_indices):
            raise RuntimeError(
                'PyBibX returned inconsistent author and H-index lengths.'
            )

        records = [
            {'author': author, 'h_index': int(h_index)}
            for author, h_index in zip(authors, h_indices)
        ]

        limit = parameters.get('limit')
        if limit:
            records = records[:int(limit)]

        return {
            'status': 'completed',
            'capability': self.capability,
            'provider': 'PyBibX',
            'package': self.package,
            'package_version': self.version,
            'parameters': parameters,
            'records': records,
            'count': len(records),
        }