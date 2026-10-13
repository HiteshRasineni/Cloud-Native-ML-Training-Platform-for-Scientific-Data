"""Tests for the format-aware dataset loader (parquet / csv / root)."""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.dataloader import SUPPORTED_FORMATS, load_dataframe


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": [0, 1, 2, 3],
            "pt": [12.0, 30.0, 5.0, 88.0],
            "eta": [0.1, -1.2, 2.4, -0.3],
            "phi": [0.0, 1.5, -2.0, 3.1],
            "energy": [40.0, 60.0, 15.0, 120.0],
            "label": [0, 1, 0, 1],
        }
    )


def test_load_parquet_roundtrip(tmp_path):
    df = _sample_df()
    p = tmp_path / "data.parquet"
    df.to_parquet(p, index=False)
    out = load_dataframe(str(p), "parquet")
    assert list(out["pt"]) == list(df["pt"])
    assert len(out) == 4


def test_load_csv_roundtrip(tmp_path):
    df = _sample_df()
    p = tmp_path / "data.csv"
    df.to_csv(p, index=False)
    out = load_dataframe(str(p), "csv")
    assert len(out) == 4
    assert out.columns.tolist() == df.columns.tolist()


def test_load_root_roundtrip(tmp_path):
    uproot = pytest.importorskip("uproot")
    df = _sample_df()
    p = tmp_path / "data.root"
    with uproot.recreate(str(p)) as file:
        file["Events"] = {c: df[c].to_numpy() for c in df.columns}
    out = load_dataframe(str(p), "root", tree="Events")
    assert list(out["pt"]) == list(df["pt"])
    assert len(out) == 4


def test_load_root_default_tree_is_events(tmp_path):
    uproot = pytest.importorskip("uproot")
    df = _sample_df()
    p = tmp_path / "data.root"
    with uproot.recreate(str(p)) as file:
        file["Events"] = {c: df[c].to_numpy() for c in df.columns}
    # No explicit tree => default "Events" is used.
    out = load_dataframe(str(p), "root")
    assert len(out) == 4


def test_unsupported_format_rejected(tmp_path):
    p = tmp_path / "data.bin"
    p.write_bytes(b"\x00\x01")
    with pytest.raises(ValueError, match="Unsupported dataset format"):
        load_dataframe(str(p), "avro")


def test_supported_formats_include_root():
    assert set(SUPPORTED_FORMATS) == {"parquet", "csv", "root"}
