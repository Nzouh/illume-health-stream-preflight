import unittest

from illume_preflight import audit


class AuditTests(unittest.TestCase):
    def test_ready_for_fresh_traced_multi_source_data(self):
        payload = {"as_of": "2026-08-17T12:00:00Z", "observations": [
            {"metric": "resting_hr", "value": 58, "unit": "bpm", "observed_at": "2026-08-17T07:00:00Z", "source": "wearable", "source_record_id": "a"},
            {"metric": "steps", "value": 6000, "unit": "count", "observed_at": "2026-08-17T08:00:00Z", "source": "phone", "source_record_id": "b"},
        ]}
        self.assertEqual(audit(payload)["status"], "ready")

    def test_review_reports_unit_freshness_lineage_and_duplicate(self):
        payload = {"as_of": "2026-08-17T12:00:00Z", "observations": [
            {"metric": "glucose", "value": 5.4, "unit": "mg/L", "observed_at": "2026-08-13T12:00:00Z", "source": "lab", "source_record_id": ""},
            {"metric": "glucose", "value": 5.4, "unit": "mg/L", "observed_at": "2026-08-13T12:00:00Z", "source": "lab", "source_record_id": "x"},
        ]}
        result = audit(payload)
        self.assertEqual(result["status"], "review")
        codes = {item["code"] for item in result["findings"]}
        self.assertTrue({"unexpected_unit", "stale_observation", "missing_source_record_id", "duplicate_observation"} <= codes)


if __name__ == "__main__":
    unittest.main()
