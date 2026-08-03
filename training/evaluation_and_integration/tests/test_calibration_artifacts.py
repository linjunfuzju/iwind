from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from iwind.evaluation_and_integration.artifacts import atomic_write_json, atomic_write_jsonl, build_manifest, verify_manifest
from iwind.evaluation_and_integration.build_calibration import allocate, build, stable_hash
from iwind.evaluation_and_integration.quantize_gptq import validate_contract


class CalibrationArtifactTests(unittest.TestCase):
    def test_allocation_is_exact_and_deterministic(self) -> None:
        self.assertEqual(allocate(5, [1, 1, 1]), [2, 2, 1])

    def test_leakage_is_checked_during_redistribution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            primary = root / "primary.jsonl"
            overflow = root / "overflow.jsonl"
            leak = "benchmark cable fault repeated content"
            safe = "independent turbine gearbox maintenance narrative"
            atomic_write_jsonl(primary, [{"text": leak}])
            atomic_write_jsonl(overflow, [{"text": leak}, {"text": safe}])
            exclusions = root / "exclude.json"
            atomic_write_json(exclusions, [leak])
            config = {
                "seed": 3, "min_chars": 1, "total_samples": 1, "evaluation_files": ["exclude.json"],
                "near_duplicate_jaccard": 0.8, "require_full_sample": True,
                "sources": [
                    {"name": "primary", "path": "primary.jsonl", "format": "text", "ratio": 1},
                    {"name": "overflow", "path": "overflow.jsonl", "format": "text", "ratio": 0},
                ],
            }
            records, manifest = build(config, root)
            self.assertEqual([record["text"] for record in records], [safe])
            self.assertNotEqual(records[0]["sha256"], stable_hash(leak))
            self.assertGreaterEqual(manifest["rejected_for_leakage"], 1)

    def test_manifest_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "data.json"
            atomic_write_json(path, {"value": 1})
            manifest = build_manifest("test", [path], {})
            self.assertEqual(verify_manifest(manifest), [])
            path.write_text("tampered", encoding="utf-8")
            self.assertTrue(verify_manifest(manifest))

    def test_quantization_contract_is_runtime_free_and_rejects_nesting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "model"
            source.mkdir()
            calibration = root / "calibration.jsonl"
            calibration.write_text(json.dumps({"text": "valid calibration sample"}) + "\n", encoding="utf-8")
            config = {"source_model": "model", "calibration_file": "calibration.jsonl", "output_dir": "model/export", "bits": 4, "group_size": 128, "damp_percent": 0.01}
            with self.assertRaisesRegex(ValueError, "non-nested"):
                validate_contract(config, root)


if __name__ == "__main__":
    unittest.main()
