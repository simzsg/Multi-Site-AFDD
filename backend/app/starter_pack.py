import csv
import heapq
from itertools import groupby
from pathlib import Path

DEFAULT_PACK = Path(__file__).resolve().parents[2] / "data" / "candidate-starter-pack"
if not DEFAULT_PACK.exists():
    DEFAULT_PACK = Path(__file__).resolve().parents[1] / "data" / "candidate-starter-pack"

POINT_MAPPING = {
    "RUN": ("Run_Status", "run_status", "bool"),
    "ALARM": ("Alarm", "alarm_status", "bool"),
    "SAT": ("Supply_Air_Temperature_Sensor", "supply_air_temperature_c", "C"),
    "RAT": ("Return_Air_Temperature_Sensor", "return_air_temperature_c", "C"),
    "SAT_SP": ("Supply_Air_Temperature_Setpoint", "supply_air_temperature_setpoint_c", "C"),
    "ROOM_TEMP": ("Zone_Air_Temperature_Sensor", "room_temperature_c", "C"),
    "RH": ("Humidity_Sensor", "relative_humidity_pct", "%"),
    "CO2": ("CO2_Sensor", "co2_ppm", "ppm"),
    "POWER_KW": ("Electrical_Power_Sensor", "active_power_kw", "kW"),
    "ENERGY_KWH": ("Electrical_Energy_Sensor", "cumulative_energy_kwh", "kWh"),
}


def csv_rows(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


def inventory(pack=DEFAULT_PACK):
    pack = Path(pack)
    entities, edges = [], []

    def edge(source, relation, target):
        if target:
            edges.append({"source": source, "relation": relation, "target": target})

    for row in csv_rows(pack / "building-and-equipment/spaces.csv"):
        data = {
            "source": "candidate-starter-pack",
            "source_register": row,
            "space_use": row["usage_type"].lower().replace(" ", "_"),
        }
        if row["property_type"]:
            data["property_type"] = row["property_type"].lower()
        if row["usage_type"] in {"Office Room", "Guest Room"}:
            data["occupied"] = True
        entities.append(
            {
                "id": row["space_id"],
                "kind": row["space_type"].replace(" ", "_"),
                "label": row["name"],
                "data": data,
            }
        )
        edge(row["parent_space_id"], "hasPart", row["space_id"]) if row["parent_space_id"] else None
    for row in csv_rows(pack / "building-and-equipment/equipment.csv"):
        kind = {"AHU": "AHU", "IAQ Sensor": "IAQ_Device", "Electricity Meter": "Electrical_Meter"}[
            row["equipment_type"]
        ]
        entities.append(
            {
                "id": row["equipment_id"],
                "kind": kind,
                "label": row["name"],
                "data": {
                    "source": "candidate-starter-pack",
                    "source_register": row,
                    "property_id": row["property_id"],
                },
            }
        )
        edge(row["equipment_id"], "hasLocation", row["installed_space_id"])
        edge(row["equipment_id"], "feeds", row["served_space_id"])
        edge(row["equipment_id"], "measuresSpace", row["measurement_scope_id"])
    for row in csv_rows(pack / "building-and-equipment/datapoint-reference.csv"):
        kind, field, unit = POINT_MAPPING[row["source_name"]]
        entities.append(
            {
                "id": row["source_point_id"],
                "kind": kind,
                "label": row["description"],
                "data": {
                    "source": "candidate-starter-pack",
                    "source_register": row,
                    "source_name": row["source_name"],
                    "source_field": field,
                    "unit": unit,
                    "source_unit": row["unit"],
                    "value_kind": "binary" if unit == "bool" else "number",
                    "expected_interval_seconds": int(row["expected_interval_seconds"]),
                },
            }
        )
        edge(row["equipment_id"], "hasPoint", row["source_point_id"])
    return {"source": "candidate-starter-pack", "entities": entities, "edges": edges}


def source_schedule(pack=DEFAULT_PACK):

    def scheduled(filename, identity_field):
        delivery_at = ""
        for index, row in enumerate(csv_rows(Path(pack) / "sample-telemetry" / filename)):
            delivery_at = max(delivery_at, row["observed_at"])
            yield delivery_at, filename, index, identity_field, row

    streams = [
        scheduled("ahu_readings.csv", "equipment_id"),
        scheduled("iaq_readings.csv", "device_id"),
        scheduled("power_readings.csv", "meter_id"),
    ]
    return heapq.merge(*streams, key=lambda item: (item[0], item[1], item[2]))


def point_events(registry, filename, identity_field, row):
    identity = row[identity_field]
    provenance = {
        "file": filename,
        "source_record_id": row["source_record_id"],
        "equipment_id": identity,
        "observed_at": row["observed_at"],
    }
    if identity not in registry.entities:
        yield {
            "source_error": "Unknown equipment identity",
            "source": provenance,
            "event_id": f"{filename}:{row['source_record_id']}",
        }
        return
    for point in registry.related(identity, "hasPoint"):
        field = point["data"]["source_field"]
        raw = row.get(field, "")
        source = {
            **provenance,
            "source_name": point["data"]["source_name"],
            "raw_value": raw,
            "unit": point["data"]["source_unit"],
        }
        value, quality = None, "MISSING"
        if raw != "":
            try:
                if field == "run_status":
                    value = {"ON": 1, "OFF": 0}[raw]
                elif field == "alarm_status":
                    value = {"NORMAL": 0, "ALARM": 1}[raw]
                else:
                    value = float(raw)
                quality = "GOOD"
            except (ValueError, KeyError):
                yield {
                    "source_error": "Invalid source measurement",
                    "source": source,
                    "event_id": f"{filename}:{row['source_record_id']}:{point['id']}",
                }
                continue
        yield {
            "event_id": f"{filename}:{row['source_record_id']}:{point['id']}",
            "point_id": point["id"],
            "device_timestamp": row["observed_at"],
            "value": value,
            "unit": point["data"]["unit"],
            "quality": quality,
            "source": source,
        }


def batches(registry, pack=DEFAULT_PACK, buildings=None, max_frames=None):
    for frame_index, (delivery_at, group) in enumerate(
        groupby(source_schedule(pack), key=lambda item: item[0])
    ):
        if max_frames is not None and frame_index >= max_frames:
            break
        events = []
        for _, filename, _, identity_field, row in group:
            eq = registry.entities.get(row[identity_field])
            if buildings and eq and eq["data"].get("property_id") not in buildings:
                continue
            events.extend(point_events(registry, filename, identity_field, row))
        yield delivery_at, events
