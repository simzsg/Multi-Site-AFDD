import json

from . import db

POINTS = {
    "AHU": [
        ("Run_Status", "bool"),
        ("Alarm", "bool"),
        ("Supply_Air_Temperature_Sensor", "C"),
        ("Return_Air_Temperature_Sensor", "C"),
        ("Supply_Air_Temperature_Setpoint", "C"),
    ],
    "IAQ_Device": [
        ("Zone_Air_Temperature_Sensor", "C"),
        ("Humidity_Sensor", "%"),
        ("CO2_Sensor", "ppm"),
    ],
    "Electrical_Meter": [("Electrical_Power_Sensor", "kW"), ("Electrical_Energy_Sensor", "kWh")],
}


def synthetic_inventory():
    entities, edges = [], []

    def entity(identity, kind, label, **data):
        entities.append(
            {"id": identity, "kind": kind, "label": label, "data": {"source": "synthetic", **data}}
        )
        return identity

    def edge(a, relation, b):
        edges.append({"source": a, "relation": relation, "target": b})

    def equipment(identity, kind, label, location):
        entity(identity, kind, label)
        edge(identity, "hasLocation", location)
        for point_kind, unit in POINTS[kind]:
            point = entity(
                f"{identity}-{point_kind}",
                point_kind,
                point_kind.replace("_", " "),
                unit=unit,
                value_kind="binary" if unit == "bool" else "number",
            )
            edge(identity, "hasPoint", point)
        return identity

    for code, label in [("a", "North Campus"), ("b", "Riverside Tower"), ("c", "Central Exchange")]:
        b = entity(f"demo-{code}", "Building", label, property_type="office")
        plant = entity(f"{b}-plant", "Room", f"{label} plant room", space_use="plant")
        lobby = entity(f"{b}-lobby", "Room", f"{label} lobby", space_use="lobby")
        edge(b, "hasPart", plant)
        edge(b, "hasPart", lobby)
        for f in range(1, 5):
            floor = entity(f"{b}-f{f}", "Floor", f"Floor {f}")
            edge(b, "hasPart", floor)
            equipment(f"{floor}-meter", "Electrical_Meter", f"{code.upper()} / F{f} meter", floor)
            for z in range(1, 3):
                zone = entity(f"{floor}-z{z}", "HVAC_Zone", f"{code.upper()} / F{f} zone {z}")
                edge(floor, "hasPart", zone)
                ahu = equipment(
                    f"{floor}-ahu{z}", "AHU", f"AHU {code.upper()}-{f:02}-{z:02}", plant
                )
                edge(ahu, "feeds", zone)
                for r in range(1, 3):
                    room = entity(
                        f"{zone}-r{r}",
                        "Room",
                        f"Room {f}{z}{r}",
                        space_use="tenant_area",
                        occupied=True,
                    )
                    edge(zone, "hasPart", room)
                    edge(floor, "hasPart", room)
                    equipment(f"{room}-iaq", "IAQ_Device", f"Room {f}{z}{r} IAQ", room)
    return {"entities": entities, "edges": edges, "source": "synthetic"}


def import_inventory(conn, payload):
    entities = payload["entities"]
    identities = {e["id"] for e in entities}
    if len(identities) != len(entities):
        raise ValueError("Duplicate entity IDs")
    for edge in payload["edges"]:
        if edge["source"] not in identities or edge["target"] not in identities:
            raise ValueError("Unresolved relationship identity")
        if edge["relation"] not in {"hasPart", "hasPoint", "hasLocation", "feeds", "measuresSpace"}:
            raise ValueError("Unsupported relationship")
    existing = {e["id"]: e for e in db.rows(conn, db.entities)}
    sources = {e["data"].get("source") for e in existing.values()}
    if sources and payload.get("source") not in sources:
        raise ValueError(
            "Use a fresh database: mixing synthetic and supplied inventory is prohibited"
        )
    for entity in entities:
        if entity["id"] in existing and existing[entity["id"]] != entity:
            raise ValueError(
                "Inventory changes require an explicit migration; refusing silent overwrite"
            )
        if entity["id"] not in existing:
            conn.execute(db.entities.insert().values(**entity))
    existing_edges = {(e["source"], e["relation"], e["target"]) for e in db.rows(conn, db.edges)}
    for edge in payload["edges"]:
        if (edge["source"], edge["relation"], edge["target"]) not in existing_edges:
            conn.execute(db.edges.insert().values(**edge))
    db.log(
        conn, "inventory_imported", source=payload.get("source", "supplied"), count=len(entities)
    )


def seed(engine, path=None):
    payload = json.load(open(path)) if path else synthetic_inventory()
    with db.transaction(engine) as conn:
        import_inventory(conn, payload)
