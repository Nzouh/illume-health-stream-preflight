"""Audit synthetic multi-source health observations before downstream analysis."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_UNITS = {
    "resting_hr": {"bpm"},
    "sleep_duration": {"hours"},
    "glucose": {"mg/dL", "mmol/L"},
    "steps": {"count"},
}


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def audit(payload: dict) -> dict:
    as_of = parse_time(payload["as_of"])
    max_age = float(payload.get("max_age_hours", 48))
    findings: list[dict] = []
    seen: set[tuple[str, str]] = set()
    observations = payload.get("observations", [])

    for index, obs in enumerate(observations):
        label = f"observations[{index}]"
        required = ("metric", "value", "unit", "observed_at", "source")
        missing = [field for field in required if obs.get(field) in (None, "")]
        if missing:
            findings.append({"code": "missing_fields", "at": label, "fields": missing})
            continue

        metric = obs["metric"]
        if metric not in ALLOWED_UNITS or obs["unit"] not in ALLOWED_UNITS[metric]:
            findings.append({"code": "unexpected_unit", "at": label, "metric": metric, "unit": obs["unit"]})

        observed = parse_time(obs["observed_at"])
        age_hours = (as_of - observed).total_seconds() / 3600
        if age_hours < 0:
            findings.append({"code": "future_timestamp", "at": label})
        elif age_hours > max_age:
            findings.append({"code": "stale_observation", "at": label, "age_hours": round(age_hours, 2)})

        identity = (metric, obs["observed_at"])
        if identity in seen:
            findings.append({"code": "duplicate_observation", "at": label, "metric": metric})
        seen.add(identity)

        if not obs.get("source_record_id"):
            findings.append({"code": "missing_source_record_id", "at": label})

    sources = {obs.get("source") for obs in observations if obs.get("source")}
    status = "ready" if not findings and len(sources) >= 2 else "review"
    if len(sources) < 2:
        findings.append({"code": "insufficient_source_diversity", "sources": sorted(sources)})
        status = "review"
    return {"status": status, "observation_count": len(observations), "source_count": len(sources), "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("report.json"))
    args = parser.parse_args()
    result = audit(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
