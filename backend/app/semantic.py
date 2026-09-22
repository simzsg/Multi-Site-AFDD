BRICK_VERSION = "1.4.4"
BRICK_NAMESPACE = "https://brickschema.org/schema/Brick#"
QUDT_UNIT_NAMESPACE = "http://qudt.org/vocab/unit/"
APPLICATION_NAMESPACE = "urn:alto:afdd:"

ENTITY_TYPES = {
    "Building": BRICK_NAMESPACE + "Building",
    "Floor": BRICK_NAMESPACE + "Floor",
    "Room": BRICK_NAMESPACE + "Room",
    "HVAC_Zone": BRICK_NAMESPACE + "HVAC_Zone",
    "AHU": BRICK_NAMESPACE + "AHU",
    "Electrical_Meter": BRICK_NAMESPACE + "Electrical_Meter",
    "IAQ_Device": APPLICATION_NAMESPACE + "IAQ_Device",
    "Run_Status": BRICK_NAMESPACE + "Run_Status",
    "Alarm": BRICK_NAMESPACE + "Alarm",
    "Supply_Air_Temperature_Sensor": BRICK_NAMESPACE + "Supply_Air_Temperature_Sensor",
    "Return_Air_Temperature_Sensor": BRICK_NAMESPACE + "Return_Air_Temperature_Sensor",
    "Supply_Air_Temperature_Setpoint": BRICK_NAMESPACE + "Supply_Air_Temperature_Setpoint",
    "Electrical_Power_Sensor": BRICK_NAMESPACE + "Electrical_Power_Sensor",
    "Electrical_Energy_Sensor": BRICK_NAMESPACE + "Electrical_Energy_Sensor",
    "Zone_Air_Temperature_Sensor": BRICK_NAMESPACE + "Zone_Air_Temperature_Sensor",
    "Humidity_Sensor": BRICK_NAMESPACE + "Humidity_Sensor",
    "CO2_Sensor": BRICK_NAMESPACE + "CO2_Sensor",
}

RELATIONSHIPS = {
    "hasPart": BRICK_NAMESPACE + "hasPart",
    "hasPoint": BRICK_NAMESPACE + "hasPoint",
    "hasLocation": BRICK_NAMESPACE + "hasLocation",
    "feeds": BRICK_NAMESPACE + "feeds",
    "measuresSpace": BRICK_NAMESPACE + "meters",
}

UNITS = {
    "bool": QUDT_UNIT_NAMESPACE + "UNITLESS",
    "C": QUDT_UNIT_NAMESPACE + "DEG_C",
    "%": QUDT_UNIT_NAMESPACE + "PERCENT",
    "ppm": QUDT_UNIT_NAMESPACE + "PPM",
    "kW": QUDT_UNIT_NAMESPACE + "KiloW",
    "kWh": QUDT_UNIT_NAMESPACE + "KiloW-HR",
}


def entity(record):
    result = {**record, "semantic_type": ENTITY_TYPES[record["kind"]]}
    unit = record["data"].get("unit")
    if unit:
        result["semantic_unit"] = UNITS[unit]
    return result


def relationship(record):
    return {**record, "semantic_relation": RELATIONSHIPS[record["relation"]]}


def manifest():
    return {
        "brick_version": BRICK_VERSION,
        "namespaces": {
            "brick": BRICK_NAMESPACE,
            "unit": QUDT_UNIT_NAMESPACE,
            "application": APPLICATION_NAMESPACE,
        },
        "entity_types": ENTITY_TYPES,
        "relationships": RELATIONSHIPS,
        "units": UNITS,
    }
