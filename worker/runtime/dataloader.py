"""Dataset format loaders: turn a downloaded object into a pandas DataFrame.

Scientific data arrives in many container formats. This module is the single
place in the worker that knows about file formats; workloads just ask for a
DataFrame. The scheduler, backend, and frontend never reference formats or
column names, so adding a format here is a worker-only concern.
"""
from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger("worker.dataloader")

SUPPORTED_FORMATS = ("parquet", "csv", "root")


def load_dataframe(path: str, fmt: str, *, tree: str = "Events") -> pd.DataFrame:
    """Load the object at ``path`` into a DataFrame.

    Args:
        path: local file path (already downloaded from object storage).
        fmt: dataset format as registered on the backend: parquet | csv | root.
        tree: TTree name for ROOT files (CMS convention is ``Events``).

    Raises:
        ValueError: if the format is not supported.
    """
    fmt = (fmt or "parquet").lower()
    if fmt == "parquet":
        df = pd.read_parquet(path)
    elif fmt == "csv":
        df = pd.read_csv(path)
    elif fmt == "root":
        # uproot is imported lazily so parquet/csv runs never pay for it.
        import uproot

        with uproot.open(path) as file:
            tree = file[tree]
            # library="np" returns {branch: numpy array} for flat branches;
            # building the DataFrame here avoids awkward-array conversion quirks
            # and guarantees a real pandas.DataFrame for downstream selection.
            arrays = tree.arrays(library="np")
        # uproot's numpy backend returns a structured array; turn it into a
        # clean pandas.DataFrame (avoids awkward-array conversion quirks).
        df = pd.DataFrame({name: arrays[name] for name in arrays.dtype.names})
    else:
        raise ValueError(
            f"Unsupported dataset format: {fmt!r} (supported: {', '.join(SUPPORTED_FORMATS)})"
        )
    logger.info("Loaded dataset format=%s tree=%s rows=%d cols=%d", fmt, tree, len(df), df.shape[1])
    return df
