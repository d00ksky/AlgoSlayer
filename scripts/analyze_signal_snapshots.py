#!/usr/bin/env python3
"""Inspect aggregated signal telemetry to tune weights and thresholds."""
import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

DEFAULT_DB = Path("data") / "options_performance.db"


def load_snapshots(db_path: Path, limit: int | None = None):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT timestamp, final_direction, final_confidence,
               buy_strength, sell_strength, total_strength,
               strength_diff, aligned_count, aligned_weight,
               signals_json
        FROM signal_snapshots
        ORDER BY id DESC
        """
        + (f" LIMIT {int(limit)}" if limit else "")
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def summarize(rows):
    if not rows:
        print("No telemetry rows found yet. Let the scheduler run during market hours first.")
        return

    direction_counts = defaultdict(int)
    signal_stats = defaultdict(lambda: defaultdict(float))

    for ts, direction, confidence, buy_strength, sell_strength, total_strength, strength_diff, aligned_count, aligned_weight, signals_json in rows:
        direction_counts[direction] += 1
        signals = json.loads(signals_json)
        for sig in signals:
            entry = signal_stats[sig["name"]]
            entry["count"] += 1
            entry["confidence_sum"] += sig.get("confidence", 0.0)
            entry["weight_sum"] += sig.get("weight", 0.0)
            match sig.get("direction"):
                case "BUY":
                    entry["buy"] += 1
                case "SELL":
                    entry["sell"] += 1

    total = sum(direction_counts.values())
    print("Final direction distribution:")
    for key in ("BUY", "SELL", "HOLD"):
        pct = 100 * direction_counts[key] / total if total else 0
        print(f"  {key:4s}: {direction_counts[key]:5d} ({pct:5.1f}%)")

    print("\nSignal directional tendencies:")
    print(f"{'signal':24s} {'count':>6s} {'buy%':>7s} {'sell%':>7s} {'avg_conf':>9s} {'avg_weight':>11s}")
    for name, stats in sorted(signal_stats.items()):
        count = stats["count"] or 1
        buy_pct = stats["buy"] / count * 100
        sell_pct = stats["sell"] / count * 100
        avg_conf = stats["confidence_sum"] / count
        avg_weight = stats["weight_sum"] / count
        print(f"{name:24s} {int(count):6d} {buy_pct:7.1f} {sell_pct:7.1f} {avg_conf:9.3f} {avg_weight:11.3f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to options_performance.db")
    parser.add_argument("--limit", type=int, default=None, help="Only include the latest N rows")
    args = parser.parse_args()

    rows = load_snapshots(args.db, args.limit)
    summarize(rows)


if __name__ == "__main__":
    main()
