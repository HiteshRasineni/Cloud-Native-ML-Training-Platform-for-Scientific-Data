"""Generate a deterministic synthetic "HEP-like" dataset in Parquet format.

~5000 events with realistic per-particle kinematic columns (pt, eta, phi,
energy, label). Fixed random seed => fully reproducible bytes for a given run.

Usage:
    python generate_sample.py [--out cms-run2015_v1.parquet] [--rows 5000]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20150712  # CMS Run 2015 start date, used as a stable seed


def generate(rows: int = 5000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    # Two loosely-separated populations (signal/background) so a classifier or
    # density model has real structure to learn.
    n_sig = rows // 3
    pt_bkg = rng.exponential(scale=40.0, size=rows - n_sig) + 5.0
    pt_sig = rng.exponential(scale=60.0, size=n_sig) + 10.0
    pt = np.concatenate([pt_bkg, pt_sig])

    eta = rng.uniform(-2.5, 2.5, size=rows)
    phi = rng.uniform(-np.pi, np.pi, size=rows)
    energy = pt * np.cosh(eta)  # massless approximation
    label = np.concatenate([np.zeros(rows - n_sig, dtype=np.int64), np.ones(n_sig, dtype=np.int64)])

    df = pd.DataFrame(
        {
            "event_id": np.arange(rows, dtype=np.int64),
            "pt": pt.astype(np.float32),
            "eta": eta.astype(np.float32),
            "phi": phi.astype(np.float32),
            "energy": energy.astype(np.float32),
            "label": label,
        }
    )
    return df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)  # shuffle rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).parent / "cms-run2015_v1.parquet"))
    parser.add_argument("--rows", type=int, default=5000)
    args = parser.parse_args()

    df = generate(args.rows)
    df.to_parquet(args.out, index=False)
    print(f"Wrote {len(df)} rows -> {args.out}")


if __name__ == "__main__":
    main()
