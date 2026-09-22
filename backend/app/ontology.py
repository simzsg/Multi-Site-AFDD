import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any

from .schemas import RuleConfig


class OntologyGraph:
    def __init__(
        self,
        entities: Iterable[Mapping[str, Any]],
        edges: Iterable[Mapping[str, Any]],
    ):
        self.entities = {e["id"]: dict(e) for e in entities}
        self.edges = [dict(edge) for edge in edges]
        self._outgoing = defaultdict(list)
        self._incoming = defaultdict(list)
        for edge in self.edges:
            self._outgoing[(edge["source"], edge["relation"])].append(edge["target"])
            self._incoming[(edge["target"], edge["relation"])].append(edge["source"])

    def related(self, source, relation):
        return [
            self.entities[target]
            for target in self._outgoing[(source, relation)]
            if target in self.entities
        ]

    def parents(self, target, kind):
        return [
            self.entities[source]
            for source in self._incoming[(target, "hasPart")]
            if self.entities.get(source, {}).get("kind") == kind
        ]

    def spaces(self, equipment_id):
        zones = [z for z in self.related(equipment_id, "feeds") if z["kind"] == "HVAC_Zone"]
        rooms = {
            r["id"]: r
            for z in zones
            for r in self.related(z["id"], "hasPart")
            if r["kind"] == "Room"
        }
        return {
            "zones": zones,
            "rooms": list(rooms.values()),
            "label": "Potentially affected",
            "installation": self.related(equipment_id, "hasLocation"),
        }

    def preview(self, config: RuleConfig):
        target = config.target
        required = {config.logic.operating_point, config.logic.left, config.logic.right}
        matches, exclusions = [], []
        for eq in self.entities.values():
            if eq["kind"] != target.equipment_type:
                continue
            spaces = self.spaces(eq["id"])
            paths = []
            for zone in spaces["zones"]:
                for floor in self.parents(zone["id"], "Floor"):
                    for building in self.parents(floor["id"], "Building"):
                        rooms = [
                            r for r in self.related(zone["id"], "hasPart") if r["kind"] == "Room"
                        ]
                        if building["data"].get("property_type") != target.property_type:
                            continue
                        if target.building_ids and building["id"] not in target.building_ids:
                            continue
                        if target.floor_ids and floor["id"] not in target.floor_ids:
                            continue
                        if target.zone_ids and zone["id"] not in target.zone_ids:
                            continue
                        if not any(
                            (
                                zone["data"].get("space_use") == target.space_use
                                or r["data"].get("space_use") == target.space_use
                            )
                            and (not target.room_ids or r["id"] in target.room_ids)
                            for r in rooms
                        ):
                            continue
                        paths.append(
                            {
                                "equipment": eq["id"],
                                "building": building["id"],
                                "floor": floor["id"],
                                "zone": zone["id"],
                                "rooms": [r["id"] for r in rooms],
                            }
                        )
            if not paths:
                exclusions.append(
                    {"equipment_id": eq["id"], "reason": "Outside selected served-space scope"}
                )
                continue
            points = self.related(eq["id"], "hasPoint")
            by_kind = {kind: [p for p in points if p["kind"] == kind] for kind in required}
            missing = [kind for kind, ps in by_kind.items() if len(ps) != 1]
            if eq["id"] in target.exclude_equipment_ids or missing:
                exclusions.append(
                    {
                        "equipment_id": eq["id"],
                        "reason": "Explicit exclusion"
                        if not missing
                        else "Missing or ambiguous required points",
                        "missing_points": missing,
                    }
                )
                continue
            if len({p["building"] for p in paths}) != 1:
                exclusions.append(
                    {"equipment_id": eq["id"], "reason": "Ambiguous property ownership"}
                )
                continue
            point_map = {k: ps[0]["id"] for k, ps in by_kind.items()}
            if any(
                self.entities[point_map[k]]["data"].get("unit") != config.logic.unit
                for k in [config.logic.left, config.logic.right]
            ):
                exclusions.append({"equipment_id": eq["id"], "reason": "Comparison unit mismatch"})
                continue
            building_id = paths[0]["building"]
            override = config.overrides.get(building_id)
            effective = config.logic.model_dump()
            if override:
                effective.update(override.model_dump(exclude_none=True))
            matches.append(
                {
                    "equipment_id": eq["id"],
                    "label": eq["label"],
                    "paths": paths,
                    "points": point_map,
                    "global": config.logic.model_dump(),
                    "override": override.model_dump(exclude_none=True) if override else {},
                    "effective": effective,
                    "affected": spaces,
                }
            )
        result = {"matches": matches, "exclusions": exclusions}
        result["digest"] = hashlib.sha256(
            json.dumps({"config": config.model_dump(), "preview": result}, sort_keys=True).encode()
        ).hexdigest()
        return result

    def validate(self, config):
        errors = []
        selectors = {
            "building_ids": "Building",
            "floor_ids": "Floor",
            "zone_ids": "HVAC_Zone",
            "room_ids": "Room",
            "exclude_equipment_ids": "AHU",
        }
        for field, kind in selectors.items():
            for identity in getattr(config.target, field):
                if self.entities.get(identity, {}).get("kind") != kind:
                    errors.append(f"Unknown {kind}: {identity}")
        for identity in config.overrides:
            if self.entities.get(identity, {}).get("kind") != "Building":
                errors.append(f"Unknown override building: {identity}")
        known = {e["kind"] for e in self.entities.values()}
        for kind in [config.logic.left, config.logic.right, config.logic.operating_point]:
            if kind not in known:
                errors.append(f"Unknown point class: {kind}")
        if config.logic.operating_point != "Run_Status":
            errors.append("Operating point must be Run_Status")
        if config.logic.left == config.logic.right:
            errors.append("Comparison must use distinct point classes")
        return {"valid": not errors, "errors": errors}
