import { useCallback, useEffect, useState } from "react";
import type {
  AIResult,
  Audit,
  Edge,
  Entity,
  Issue,
  Observation,
  Pipeline,
  Preview,
  Rule,
} from "../types";
import { api } from "../lib/api";
import { example, stale } from "../lib/format";
export function useWorkspaceController() {
  const [view, setView] = useState<
    "overview" | "issues" | "rules" | "pipeline"
  >("overview");
  const [entities, setEntities] = useState<Entity[]>([]),
    [edges, setEdges] = useState<Edge[]>([]);
  const [current, setCurrent] = useState<Record<string, Observation>>({}),
    [issues, setIssues] = useState<Issue[]>([]),
    [rules, setRules] = useState<Rule[]>([]);
  const [pipeline, setPipeline] = useState<Pipeline>({
      rejected: 0,
      duplicates: 0,
      pending_evaluations: 0,
    }),
    [audits, setAudits] = useState<Audit[]>([]);
  const [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  const [building, setBuilding] = useState(""),
    [floor, setFloor] = useState(""),
    [zone, setZone] = useState(""),
    [query, setQuery] = useState("");
  const [selectedIssue, setSelectedIssue] = useState(""),
    [selectedRule, setSelectedRule] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null),
    [editor, setEditor] = useState(""),
    [confirmed, setConfirmed] = useState(false),
    [reviewer, setReviewer] = useState("");
  const [authorOpen, setAuthorOpen] = useState(false),
    [prompt, setPrompt] = useState(example),
    [mode, setMode] = useState<"demo" | "model">("demo"),
    [aiResult, setAiResult] = useState<AIResult | null>(null);
  const [modelConfigured, setModelConfigured] = useState(false);
  const [auditFilter, setAuditFilter] = useState("");
  const refresh = useCallback(async () => {
    try {
      const [e, rel, c, i, r, p, a, h] = await Promise.all([
        api<Entity[]>("/entities"),
        api<Edge[]>("/relationships"),
        api<Record<string, Observation>>("/current"),
        api<Issue[]>("/issues"),
        api<Rule[]>("/rules"),
        api<Pipeline>("/pipeline-health"),
        api<Audit[]>(
          `/audit?limit=40${auditFilter ? "&action=" + auditFilter : ""}`,
        ),
        api<{ model_configured: boolean }>("/health"),
      ]);
      setEntities(e);
      setEdges(rel);
      setCurrent(c);
      setIssues(i);
      setRules(r);
      setPipeline(p);
      setAudits(a);
      setModelConfigured(h.model_configured);
      setError("");
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [auditFilter]);
  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), 10000);
    return () => clearInterval(id);
  }, [refresh]);
  const act = async (fn: () => Promise<void>) => {
    setBusy(true);
    setNotice("");
    try {
      await fn();
      await refresh();
    } catch (e) {
      setNotice(String(e));
    } finally {
      setBusy(false);
    }
  };
  const entity = (id: string) => entities.find((e) => e.id === id);
  const label = (id: string) => entity(id)?.label ?? id;
  const related = (id: string, relation: string) =>
    edges
      .filter((e) => e.source === id && e.relation === relation)
      .map((e) => entity(e.target))
      .filter((e): e is Entity => !!e);
  const parent = (id: string, kind: string) =>
    edges
      .filter((e) => e.target === id && e.relation === "hasPart")
      .map((e) => entity(e.source))
      .find((e) => e?.kind === kind);
  const zonesFor = (eq: Entity) =>
    related(eq.id, "feeds").filter((e) => e.kind === "HVAC_Zone");
  const floorsFor = (eq: Entity) =>
    zonesFor(eq)
      .map((z) => parent(z.id, "Floor"))
      .filter((e): e is Entity => !!e);
  const buildingFor = (eq: Entity) =>
    floorsFor(eq)
      .map((f) => parent(f.id, "Building"))
      .find(Boolean);
  const buildings = entities.filter((e) => e.kind === "Building");
  const floors = entities.filter(
    (e) =>
      e.kind === "Floor" &&
      (!building || parent(e.id, "Building")?.id === building),
  );
  const zones = entities.filter(
    (e) =>
      e.kind === "HVAC_Zone" &&
      (!floor || parent(e.id, "Floor")?.id === floor) &&
      (!building ||
        parent(parent(e.id, "Floor")?.id ?? "", "Building")?.id === building),
  );
  const scopedAhus = entities.filter(
    (e) =>
      e.kind === "AHU" &&
      (!building || buildingFor(e)?.id === building) &&
      (!floor || floorsFor(e).some((f) => f.id === floor)) &&
      (!zone || zonesFor(e).some((z) => z.id === zone)),
  );
  const ahus = scopedAhus.filter((e) =>
    e.label.toLowerCase().includes(query.toLowerCase()),
  );
  const point = (eq: Entity, kind: string) =>
    related(eq.id, "hasPoint").find((e) => e.kind === kind);
  const filteredIssues = issues.filter((i) =>
    ahus.some((e) => e.id === i.equipment_id),
  );
  const activeIssues = filteredIssues.filter((i) => i.status === "ACTIVE");
  const issue = issues.find((i) => i.id === selectedIssue) ?? filteredIssues[0];
  const rule = rules.find((r) => r.id === selectedRule);
  const openRule = (r: Rule) => {
    setSelectedRule(r.id);
    setEditor(JSON.stringify(r.config, null, 2));
    setPreview(null);
    setConfirmed(false);
    setView("rules");
  };
  const openIssue = (i: Issue) => {
    setSelectedIssue(i.id);
    setView("issues");
  };
  const live = !stale(
    pipeline.ingestion?.heartbeat_at ?? pipeline.ingestion?.last_received_at,
    90,
  );
  const scopedRooms = new Set(
    scopedAhus.flatMap((eq) =>
      zonesFor(eq).flatMap((z) => related(z.id, "hasPart").map((r) => r.id)),
    ),
  );
  const scopedFloors = new Set(
    scopedAhus.flatMap((eq) => floorsFor(eq).map((f) => f.id)),
  );
  const contextEquipment = entities.filter(
    (e) =>
      (e.kind === "IAQ_Device" &&
        related(e.id, "hasLocation").some((r) => scopedRooms.has(r.id))) ||
      (e.kind === "Electrical_Meter" &&
        [
          ...related(e.id, "measuresSpace"),
          ...related(e.id, "hasLocation"),
        ].some((f) => scopedFloors.has(f.id))),
  );
  const scopedPoints = ahus.flatMap((eq) => related(eq.id, "hasPoint"));
  const servedRoomCount = new Set(
    ahus.flatMap((eq) =>
      zonesFor(eq).flatMap((z) =>
        related(z.id, "hasPart")
          .filter((r) => r.kind === "Room")
          .map((r) => r.id),
      ),
    ),
  ).size;
  const freshCount = scopedPoints.filter(
    (p) =>
      current[p.id] &&
      !stale(current[p.id].device_timestamp) &&
      current[p.id].quality === "GOOD",
  ).length;

  return {
    view,
    setView,
    entities,
    setEntities,
    edges,
    setEdges,
    current,
    setCurrent,
    issues,
    setIssues,
    rules,
    setRules,
    pipeline,
    setPipeline,
    audits,
    setAudits,
    loading,
    setLoading,
    error,
    setError,
    notice,
    setNotice,
    busy,
    setBusy,
    building,
    setBuilding,
    floor,
    setFloor,
    zone,
    setZone,
    query,
    setQuery,
    selectedIssue,
    setSelectedIssue,
    selectedRule,
    setSelectedRule,
    preview,
    setPreview,
    editor,
    setEditor,
    confirmed,
    setConfirmed,
    reviewer,
    setReviewer,
    authorOpen,
    setAuthorOpen,
    prompt,
    setPrompt,
    mode,
    setMode,
    aiResult,
    setAiResult,
    modelConfigured,
    setModelConfigured,
    auditFilter,
    setAuditFilter,
    refresh,
    act,
    entity,
    label,
    related,
    parent,
    zonesFor,
    floorsFor,
    buildingFor,
    buildings,
    floors,
    zones,
    ahus,
    point,
    filteredIssues,
    activeIssues,
    issue,
    rule,
    openRule,
    openIssue,
    live,
    scopedRooms,
    scopedFloors,
    contextEquipment,
    scopedPoints,
    servedRoomCount,
    freshCount,
  };
}
