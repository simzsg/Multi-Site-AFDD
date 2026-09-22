from fastapi import APIRouter

from app.semantic import manifest

from ..dependencies import InventoryDep

router = APIRouter()


@router.get("/api/ontology")
def ontology_manifest():
    return manifest()


@router.get("/api/entities")
def entities(service: InventoryDep, kind: str | None = None):
    return service.entities(kind)


@router.get("/api/equipment")
def equipment(service: InventoryDep):
    return service.equipment()


@router.get("/api/points")
def points(service: InventoryDep):
    return service.points()


@router.get("/api/relationships")
def relationships(service: InventoryDep):
    return service.relationships()


@router.get("/api/equipment/{identity}/relationships")
def equipment_relationships(service: InventoryDep, identity: str):
    return service.equipment_relationships(identity)


@router.get("/api/equipment/{identity}/served-spaces")
def spaces(service: InventoryDep, identity: str):
    return service.spaces(identity)


@router.get("/api/zones/{identity}/rooms")
def zone_rooms(service: InventoryDep, identity: str):
    return service.zone_rooms(identity)


def register_discovery_routes():
    for path, kind in [
        ("buildings", "Building"),
        ("floors", "Floor"),
        ("zones", "HVAC_Zone"),
        ("rooms", "Room"),
    ]:

        def discovery(service: InventoryDep, kind=kind):
            return service.entities(kind)

        router.add_api_route(f"/api/{path}", discovery, methods=["GET"], name=path)


register_discovery_routes()
