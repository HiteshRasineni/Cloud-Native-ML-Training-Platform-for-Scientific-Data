"""Generate a deterministic synthetic "HEP-like" dataset in CMS ROOT format.

Same distributions as generate_sample.py (~5000 events; pt/eta/phi/energy/label
in an `Events` TTree), fixed seed => fully reproducible bytes. Uses uproot to
write the TTree so the sample can be produced anywhere uproot is installed.

Usage:
    python generate_sample_root.py [--out cms-run2015_v1.root] [--rows 5000] [--tree Events]
"""
import argparse
from pathlib import Path

import numpy as np
import uproot

SEED = 20150712  # CMS Run 2015 start date, used as a stable seed


def generate(rows: int = 5000) -> dict[str, np.ndarray]:
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

    order = rng.permutation(rows)  # shuffle rows for a fixed seed
    return {
        "event_id": np.arange(rows, dtype=np.int64)[order],
        "pt": pt[order].astype(np.float32),
        "eta": eta[order].astype(np.float32),
        "phi": phi[order].astype(np.float32),
        "energy": energy[order].astype(np.float32),
        "label": label[order],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(Path(__file__).parent / "cms-run2015_v1.root"))
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--tree", default="Events")
    args = parser.parse_args()

    branches = generate(args.rows)
    with uproot.recreate(args.out) as file:
        file[args.tree] = branches
    print(f"Wrote {len(branches['pt'])} rows -> {args.out} (tree={args.tree})")


if __name__ == "__main__":
    main()
