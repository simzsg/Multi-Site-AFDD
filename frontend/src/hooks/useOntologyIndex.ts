import { useCallback, useMemo } from "react";
import type { Edge, Entity } from "../types";

const edgeKey = (identity: string, relation: string) =>
  `${identity}\u0000${relation}`;

export function useOntologyIndex(entities: Entity[], edges: Edge[]) {
  const entityById = useMemo(
    () => new Map(entities.map((entity) => [entity.id, entity])),
    [entities],
  );
  const { outgoing, incoming } = useMemo(() => {
    const nextOutgoing = new Map<string, string[]>();
    const nextIncoming = new Map<string, string[]>();
    for (const edge of edges) {
      const outgoingKey = edgeKey(edge.source, edge.relation);
      const incomingKey = edgeKey(edge.target, edge.relation);
      const outgoingTargets = nextOutgoing.get(outgoingKey);
      if (outgoingTargets) outgoingTargets.push(edge.target);
      else nextOutgoing.set(outgoingKey, [edge.target]);
      const incomingSources = nextIncoming.get(incomingKey);
      if (incomingSources) incomingSources.push(edge.source);
      else nextIncoming.set(incomingKey, [edge.source]);
    }
    return { outgoing: nextOutgoing, incoming: nextIncoming };
  }, [edges]);
  const entity = useCallback(
    (identity: string) => entityById.get(identity),
    [entityById],
  );
  const label = useCallback(
    (identity: string) => entity(identity)?.label ?? identity,
    [entity],
  );
  const related = useCallback(
    (identity: string, relation: string) =>
      (outgoing.get(edgeKey(identity, relation)) ?? [])
        .map((target) => entityById.get(target))
        .filter((item): item is Entity => item !== undefined),
    [entityById, outgoing],
  );
  const parent = useCallback(
    (identity: string, kind: string) =>
      (incoming.get(edgeKey(identity, "hasPart")) ?? [])
        .map((source) => entityById.get(source))
        .find((item) => item?.kind === kind),
    [entityById, incoming],
  );
  const zonesFor = useCallback(
    (equipment: Entity) =>
      related(equipment.id, "feeds").filter(
        (entity) => entity.kind === "HVAC_Zone",
      ),
    [related],
  );
  const floorsFor = useCallback(
    (equipment: Entity) =>
      zonesFor(equipment)
        .map((zone) => parent(zone.id, "Floor"))
        .filter((entity): entity is Entity => entity !== undefined),
    [parent, zonesFor],
  );
  const buildingFor = useCallback(
    (equipment: Entity) =>
      floorsFor(equipment)
        .map((floor) => parent(floor.id, "Building"))
        .find((entity) => entity !== undefined),
    [floorsFor, parent],
  );
  return {
    entity,
    label,
    related,
    parent,
    zonesFor,
    floorsFor,
    buildingFor,
  };
}
