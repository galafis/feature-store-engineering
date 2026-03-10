"""
Tests for the Feature Store Engineering module.
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feature_store import (
    FeatureDefinition, FeatureRegistry, FeatureStore,
    FeatureComputePipeline, FeatureMetadataCatalog
)


class TestFeatureRegistry:
    def test_register_and_get(self):
        registry = FeatureRegistry()
        feat = FeatureDefinition("age", "int", "User age", entity="user")
        registry.register(feat)
        assert registry.get("age") is not None
        assert registry.get("age").dtype == "int"

    def test_versioning(self):
        registry = FeatureRegistry()
        v1 = FeatureDefinition("income", "float", "Annual income")
        v2 = FeatureDefinition("income", "float", "Monthly income")
        registry.register(v1)
        registry.register(v2)
        assert registry.get("income").version == 2
        versions = registry.get_versions("income")
        assert len(versions) == 2

    def test_list_features(self):
        registry = FeatureRegistry()
        registry.register(FeatureDefinition("a", "int", entity="user", tags=["demo"]))
        registry.register(FeatureDefinition("b", "str", entity="item"))
        assert len(registry.list_features()) == 2
        assert len(registry.list_features(entity="user")) == 1
        assert len(registry.list_features(tags=["demo"])) == 1

    def test_get_nonexistent(self):
        registry = FeatureRegistry()
        assert registry.get("missing") is None

    def test_count(self):
        registry = FeatureRegistry()
        registry.register(FeatureDefinition("x", "int"))
        registry.register(FeatureDefinition("y", "float"))
        assert registry.count == 2


class TestFeatureStore:
    def test_online_store(self):
        store = FeatureStore()
        store.ingest_online("user_1", {"age": 30, "name": "Alice"})
        result = store.get_online("user_1")
        assert result["age"] == 30

    def test_online_store_selective(self):
        store = FeatureStore()
        store.ingest_online("user_1", {"age": 30, "name": "Alice"})
        result = store.get_online("user_1", ["age"])
        assert "age" in result
        assert "name" not in result

    def test_offline_store(self):
        store = FeatureStore()
        records = [
            {"user_id": "u1", "spend": 100, "event_time": "2025-01-01"},
            {"user_id": "u1", "spend": 200, "event_time": "2025-02-01"},
        ]
        store.ingest_offline(records)
        result = store.get_offline("u1", "user_id", ["spend"])
        assert len(result) == 2

    def test_point_in_time_lookup(self):
        store = FeatureStore()
        records = [
            {"user_id": "u1", "spend": 100, "event_time": "2025-01-01"},
            {"user_id": "u1", "spend": 200, "event_time": "2025-02-01"},
            {"user_id": "u1", "spend": 300, "event_time": "2025-03-01"},
        ]
        store.ingest_offline(records)
        result = store.get_offline("u1", "user_id", ["spend"],
                                    timestamp="2025-02-15")
        assert len(result) == 2  # Only Jan and Feb
        assert result[0]["spend"] == 200

    def test_latest_offline(self):
        store = FeatureStore()
        records = [
            {"user_id": "u1", "score": 0.5, "event_time": "2025-01-01"},
            {"user_id": "u1", "score": 0.9, "event_time": "2025-06-01"},
        ]
        store.ingest_offline(records)
        latest = store.get_latest_offline("u1", "user_id", ["score"])
        assert latest["score"] == 0.9


class TestFeatureComputePipeline:
    def test_compute(self):
        pipeline = FeatureComputePipeline()
        pipeline.add_transform("full_name", lambda r: f"{r['first']} {r['last']}")
        pipeline.add_transform("name_len", lambda r: len(r["first"]) + len(r["last"]))

        records = [{"first": "Alice", "last": "Smith"}]
        result = pipeline.compute(records)
        assert result[0]["full_name"] == "Alice Smith"
        assert result[0]["name_len"] == 10

    def test_error_handling(self):
        pipeline = FeatureComputePipeline()
        pipeline.add_transform("bad", lambda r: r["missing_key"])
        result = pipeline.compute([{"a": 1}])
        assert result[0]["bad"] is None


class TestFeatureMetadataCatalog:
    def test_add_and_get(self):
        catalog = FeatureMetadataCatalog()
        catalog.add_entry("user_age", {"source": "user_table", "owner": "data_team"})
        entry = catalog.get_entry("user_age")
        assert entry is not None
        assert entry["metadata"]["source"] == "user_table"

    def test_search(self):
        catalog = FeatureMetadataCatalog()
        catalog.add_entry("user_age", {"source": "user_table"})
        catalog.add_entry("item_price", {"source": "item_table"})
        results = catalog.search("user")
        assert len(results) == 1

    def test_list_all(self):
        catalog = FeatureMetadataCatalog()
        catalog.add_entry("a", {})
        catalog.add_entry("b", {})
        assert len(catalog.list_all()) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
