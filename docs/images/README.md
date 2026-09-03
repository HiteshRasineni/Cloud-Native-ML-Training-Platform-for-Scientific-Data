# Screenshots placeholders

The root `README.md` references the following screenshots. They are not committed because they must be captured from a running instance -- do not fabricate them.

| Filename | What to capture | How |
| --- | --- | --- |
| `dashboard.png` | The frontend experiment-submission form | Start the stack, open http://localhost:3000, capture the form with a registered dataset selected (e.g. `cms-run2015:v1`). |
| `experiment-detail.png` | A per-experiment view once a run is in progress or complete | Submit an experiment, open its detail page, capture the lifecycle/worker/artifact view. |
| `grafana-overview.png` | The provisioned Grafana overview dashboard | After submitting experiments, open http://localhost:3001, select the `Cloud ML Platform / Platform Overview` dashboard, capture a window with a few completed runs. |

Capture into this directory (`docs/images/`) with the exact filenames above; the root README will pick them up automatically.