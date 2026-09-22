import { useCallback, useMemo } from "react";
import type {
  Edge,
  Entity,
  Issue,
  Observation,
  Pipeline,
  Rule,
} from "../types";
import { stale } from "../lib/format";
import { useOntologyIndex } from "./useOntologyIndex";

type ProjectionInput = {
  entities: Entity[];
  edges: Edge[];
  current: Record<string, Observation>;
  issues: Issue[];
  rules: Rule[];
  pipeline: Pipeline;
  building: string;
  floor: string;
  zone: string;
  query: string;
  selectedIssue: string;
  selectedRule: string;
};

export function useWorkspaceProjection(input: ProjectionInput) {
  const {
    entities,
    edges,
    current,
    issues,
    rules,
    pipeline,
    building,
    floor,
    zone,
    query,
    selectedIssue,
    selectedRule,
  } = input;
  const ontology = useOntologyIndex(entities, edges);
  const { related, parent, zonesFor, floorsFor, buildingFor } = ontology;
  const point = useCallback(
    (equipment: Entity, kind: string) =>
      related(equipment.id, "hasPoint").find((entity) => entity.kind === kind),
    [related],
  );

  const projection = useMemo(() => {
    const buildings = entities.filter((entity) => entity.kind === "Building");
    const floors = entities.filter(
      (entity) =>
        entity.kind === "Floor" &&
        (!building || parent(entity.id, "Building")?.id === building),
    );
    const zones = entities.filter(
      (entity) =>
        entity.kind === "HVAC_Zone" &&
        (!floor || parent(entity.id, "Floor")?.id === floor) &&
        (!building ||
          parent(parent(entity.id, "Floor")?.id ?? "", "Building")?.id ===
            building),
    );
    const scopedAhus = entities.filter(
      (entity) =>
        entity.kind === "AHU" &&
        (!building || buildingFor(entity)?.id === building) &&
        (!floor || floorsFor(entity).some((item) => item.id === floor)) &&
        (!zone || zonesFor(entity).some((item) => item.id === zone)),
    );
    const normalizedQuery = query.trim().toLocaleLowerCase();
    const ahus = scopedAhus.filter((entity) =>
      entity.label.toLocaleLowerCase().includes(normalizedQuery),
    );
    const ahuIds = new Set(ahus.map((entity) => entity.id));
    const filteredIssues = issues.filter((issue) =>
      ahuIds.has(issue.equipment_id),
    );
    const scopedRooms = new Set(
      scopedAhus.flatMap((equipment) =>
        zonesFor(equipment).flatMap((item) =>
          related(item.id, "hasPart").map((room) => room.id),
        ),
      ),
    );
    const scopedFloors = new Set(
      scopedAhus.flatMap((equipment) =>
        floorsFor(equipment).map((item) => item.id),
      ),
    );
    const contextEquipment = entities.filter(
      (entity) =>
        (entity.kind === "IAQ_Device" &&
          related(entity.id, "hasLocation").some((room) =>
            scopedRooms.has(room.id),
          )) ||
        (entity.kind === "Electrical_Meter" &&
          [
            ...related(entity.id, "measuresSpace"),
            ...related(entity.id, "hasLocation"),
          ].some((item) => scopedFloors.has(item.id))),
    );
    const scopedPoints = ahus.flatMap((equipment) =>
      related(equipment.id, "hasPoint"),
    );
    const servedRoomCount = new Set(
      ahus.flatMap((equipment) =>
        zonesFor(equipment).flatMap((item) =>
          related(item.id, "hasPart")
            .filter((room) => room.kind === "Room")
            .map((room) => room.id),
        ),
      ),
    ).size;
    const freshCount = scopedPoints.filter(
      (item) =>
        current[item.id] &&
        !stale(current[item.id].device_timestamp) &&
        current[item.id].quality === "GOOD",
    ).length;

    return {
      buildings,
      floors,
      zones,
      ahus,
      filteredIssues,
      activeIssues: filteredIssues.filter((issue) => issue.status === "ACTIVE"),
      issue:
        issues.find((item) => item.id === selectedIssue) ?? filteredIssues[0],
      rule: rules.find((item) => item.id === selectedRule),
      live: !stale(
        pipeline.ingestion?.heartbeat_at ??
          pipeline.ingestion?.last_received_at,
        90,
      ),
      scopedRooms,
      scopedFloors,
      contextEquipment,
      scopedPoints,
      servedRoomCount,
      freshCount,
    };
  }, [
    building,
    buildingFor,
    current,
    entities,
    floor,
    floorsFor,
    issues,
    parent,
    pipeline,
    query,
    related,
    rules,
    selectedIssue,
    selectedRule,
    zone,
    zonesFor,
  ]);

  return { ...ontology, point, ...projection };
}
