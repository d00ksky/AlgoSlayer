# Local Heavy Training Playbook

Use this guide when you want to run the phase‑2 "heavy" machine‑learning cycle on a local workstation (for example, your MacBook). The goal is to keep the cloud server fully autonomous for day‑to‑day trading while giving you a repeatable checklist for occasional high-cost retraining.

## 1. Requirements

- macOS 14+ (Apple Silicon) or Linux with Python 3.12.
- At least 16 GB RAM and ~30 GB free disk during training.
- Homebrew (macOS) or `apt` (Linux) for system packages.
- SSH access to the AlgoSlayer server with the same key configured in `HybridCoordinator` (`~/.ssh/id_ed25519` by default).

## 2. Environment Setup

```bash
# Clone the repo or pull latest changes
git clone git@github.com:your-username/AlgoSlayer.git
cd AlgoSlayer

# Create an isolated environment
python3 -m venv .venv
source .venv/bin/activate

# Install core requirements
pip install -r requirements.txt

# Install heavy ML extras (choose the option that matches your platform)
# Apple Silicon
pip install tensorflow-macos==2.15.0 tensorflow-metal==1.1.0 xgboost==2.1.1
# Intel macOS / Linux
pip install tensorflow-cpu==2.16.1 xgboost==2.1.1
```

If `pip` warns about PEP 668, add `--break-system-packages` or ensure you are inside the virtual environment.

## 3. Sync Latest Server Data

1. Export environment variables if your server configuration differs from the default in `enhanced_hybrid_coordinator.py`:
   ```bash
   export ALGO_SERVER_HOST=your.server.ip
   export ALGO_SERVER_USER=root
   export ALGO_SERVER_KEY=~/.ssh/your_key
   ```

2. Run the coordinator status check to confirm connectivity:
   ```bash
   python enhanced_hybrid_coordinator.py --status
   ```

3. Download the latest prediction database and metadata:
   ```bash
   python enhanced_hybrid_coordinator.py --analyze
   ```
   The script saves artifacts under `hybrid_work/` (e.g., `server_data_latest.db`, `data_export/`).

If you prefer manual sync, use `rsync`:

```bash
rsync -avz \
  root@your.server.ip:/opt/rtx-trading/ml_training_data/signal_performance.db \
  hybrid_work/server_data_latest.db
```

## 4. Run the Heavy Training Cycle

```bash
python enhanced_hybrid_coordinator.py --train
```

This command:
- Loads `hybrid_work/server_data_latest.db`.
- Engineers features and trains advanced models (LSTM, multitask, ensembles).
- Writes models to `trained_models/coord_*.{pkl,h5}` and a coordination report in `hybrid_work/`.

Monitor console logs for training statistics. Expect 10–30 minutes on Apple Silicon depending on data volume.

## 5. Review Results

- Inspect logs in `hybrid_work/coordination_report_*.json`.
- Validate accuracy metrics and sample predictions before deployment.
- Optionally load the saved models in a notebook to spot-check outputs.

## 6. Deploy Back to the Server

When satisfied, push artifacts back:

```bash
python enhanced_hybrid_coordinator.py --deploy
```

The coordinator uploads everything under `trained_models/coord_*` and the latest report to `/opt/rtx-trading/trained_models/` on the server.

If you need manual control:

```bash
rsync -avz trained_models/coord_* root@your.server.ip:/opt/rtx-trading/trained_models/
```

## 7. Housekeeping Checklist

- Deactivate the virtual environment when finished: `deactivate`.
- Archive or delete large intermediate files in `hybrid_work/` to reclaim disk space.
- Update `README.md` or status notes if the training materially changes system performance.

## 8. Troubleshooting

- **Missing dependencies**: Re-run the `pip install` commands above. TensorFlow wheels for Apple Silicon require Xcode command line tools (`xcode-select --install`).
- **SSH failures**: Ensure your local key is whitelisted on the server and matches the path configured in `HybridCoordinator.server_config`.
- **Out-of-memory errors**: Reduce batch sizes in `enhanced_hybrid_coordinator.py` or close other ML workloads.
- **Model skips**: If TensorFlow or XGBoost is absent, the coordinator logs a skip and trains only the available models. Install the extras to enable the full pipeline.

With this workflow the server keeps running light, autonomous tasks, while you drop in occasionally to refresh the heavyweight models with reproducible steps.
