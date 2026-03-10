"""
Feature Store Module
Feature registry, versioning, point-in-time lookups, computation pipelines,
online/offline store simulation, and metadata catalog.
"""

import copy
import hashlib
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple


class FeatureDefinition:
    """Defines a feature with metadata."""

    def __init__(self, name: str, dtype: str, description: str = "",
                 entity: str = "", tags: Optional[List[str]] = None,
                 transform_fn: Optional[Callable] = None):
        self.name = name
        self.dtype = dtype
        self.description = description
        self.entity = entity
        self.tags = tags or []
        self.transform_fn = transform_fn
        self.created_at = datetime.now().isoformat()
        self.version = 1

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "description": self.description,
            "entity": self.entity,
            "tags": self.tags,
            "version": self.version,
            "created_at": self.created_at,
        }


class FeatureRegistry:
    """Central registry for feature definitions."""

    def __init__(self):
        self._features: Dict[str, FeatureDefinition] = {}
        self._versions: Dict[str, List[FeatureDefinition]] = {}

    def register(self, feature: FeatureDefinition) -> str:
        """Register a new feature or create a new version."""
        key = feature.name
        if key in self._features:
            feature.version = self._features[key].version + 1
            if key not in self._versions:
                self._versions[key] = [self._features[key]]
            self._versions[key].append(feature)
        else:
            self._versions[key] = [feature]

        self._features[key] = feature
        return key

    def get(self, name: str, version: Optional[int] = None) -> Optional[FeatureDefinition]:
        """Get a feature definition, optionally by version."""
        if version is not None:
            versions = self._versions.get(name, [])
            for v in versions:
                if v.version == version:
                    return v
            return None
        return self._features.get(name)

    def list_features(self, entity: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> List[Dict]:
        """List all registered features, optionally filtered."""
        features = list(self._features.values())
        if entity:
            features = [f for f in features if f.entity == entity]
        if tags:
            tag_set = set(tags)
            features = [f for f in features if tag_set & set(f.tags)]
        return [f.to_dict() for f in features]

    def get_versions(self, name: str) -> List[Dict]:
        """Get all versions of a feature."""
        return [v.to_dict() for v in self._versions.get(name, [])]

    @property
    def count(self) -> int:
        return len(self._features)


class FeatureStore:
    """Online and offline feature store with point-in-time lookups."""

    def __init__(self):
        self.registry = FeatureRegistry()
        self._online_store: Dict[str, Dict[str, Any]] = {}
        self._offline_store: List[Dict] = []

    def register_feature(self, feature: FeatureDefinition) -> str:
        return self.registry.register(feature)

    def ingest_online(self, entity_id: str, features: Dict[str, Any]):
        """Write features to online store (latest values)."""
        if entity_id not in self._online_store:
            self._online_store[entity_id] = {}
        self._online_store[entity_id].update(features)
        self._online_store[entity_id]["_updated_at"] = datetime.now().isoformat()

    def get_online(self, entity_id: str, feature_names: Optional[List[str]] = None) -> Dict:
        """Read features from online store."""
        record = self._online_store.get(entity_id, {})
        if feature_names:
            return {k: record.get(k) for k in feature_names}
        return dict(record)

    def ingest_offline(self, records: List[Dict], timestamp_col: str = "event_time"):
        """Write historical records to offline store."""
        for record in records:
            entry = dict(record)
            if timestamp_col not in entry:
                entry[timestamp_col] = datetime.now().isoformat()
            self._offline_store.append(entry)

    def get_offline(self, entity_id: str, entity_col: str,
                    feature_names: List[str],
                    timestamp: Optional[str] = None,
                    timestamp_col: str = "event_time") -> List[Dict]:
        """
        Point-in-time lookup from offline store.
        Returns records for entity_id up to the given timestamp.
        """
        records = [r for r in self._offline_store if r.get(entity_col) == entity_id]

        if timestamp:
            records = [r for r in records if r.get(timestamp_col, "") <= timestamp]

        records.sort(key=lambda r: r.get(timestamp_col, ""), reverse=True)

        result = []
        for r in records:
            entry = {k: r.get(k) for k in feature_names if k in r}
            entry[timestamp_col] = r.get(timestamp_col)
            result.append(entry)

        return result

    def get_latest_offline(self, entity_id: str, entity_col: str,
                           feature_names: List[str],
                           timestamp_col: str = "event_time") -> Dict:
        """Get the most recent feature values from offline store."""
        records = self.get_offline(entity_id, entity_col, feature_names,
                                   timestamp_col=timestamp_col)
        if records:
            return records[0]
        return {}


class FeatureComputePipeline:
    """Pipeline for computing features from raw data."""

    def __init__(self):
        self._transforms: List[Tuple[str, Callable]] = []

    def add_transform(self, name: str, fn: Callable[[Dict], Any]):
        """Add a feature computation transform."""
        self._transforms.append((name, fn))
        return self

    def compute(self, records: List[Dict]) -> List[Dict]:
        """Apply all transforms to compute features."""
        results = []
        for record in records:
            computed = dict(record)
            for name, fn in self._transforms:
                try:
                    computed[name] = fn(record)
                except Exception:
                    computed[name] = None
            results.append(computed)
        return results


class FeatureMetadataCatalog:
    """Catalog for feature metadata and lineage."""

    def __init__(self):
        self._catalog: Dict[str, Dict] = {}

    def add_entry(self, feature_name: str, metadata: Dict):
        """Add metadata entry for a feature."""
        self._catalog[feature_name] = {
            "feature_name": feature_name,
            "metadata": metadata,
            "updated_at": datetime.now().isoformat(),
        }

    def get_entry(self, feature_name: str) -> Optional[Dict]:
        return self._catalog.get(feature_name)

    def search(self, query: str) -> List[Dict]:
        """Search catalog by keyword."""
        results = []
        query_lower = query.lower()
        for name, entry in self._catalog.items():
            if (query_lower in name.lower() or
                query_lower in str(entry.get("metadata", "")).lower()):
                results.append(entry)
        return results

    def list_all(self) -> List[Dict]:
        return list(self._catalog.values())
