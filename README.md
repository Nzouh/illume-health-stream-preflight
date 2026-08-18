# Illume health-stream preflight

A dependency-free audit for synthetic multi-source health observations before trend analysis. It checks timestamp freshness, expected units, source-record lineage, duplicates, and whether at least two sources are represented. It does not provide medical advice or process real patient data.

## Run

```bash
python illume_preflight.py example.json --output report.json
python -m unittest -v
```

The ready example exits `0`. `example_review.json` intentionally exits `2` and writes inspectable findings.

## Limits and next step

The allowed metric/unit table is deliberately small and the inputs are synthetic. A useful next step would be source-specific adapters plus explicit conversion rules, while retaining the original source record identifier.
