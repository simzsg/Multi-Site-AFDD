import { useCallback, useEffect, useRef, useState } from "react";
import type {
  Audit,
  Edge,
  Entity,
  Issue,
  Observation,
  Pipeline,
  Rule,
} from "../types";
import { api, errorMessage } from "../lib/api";

type WorkspaceSnapshot = {
  entities: Entity[];
  edges: Edge[];
  current: Record<string, Observation>;
  issues: Issue[];
  rules: Rule[];
  pipeline: Pipeline;
  audits: Audit[];
  modelConfigured: boolean;
};

const emptySnapshot: WorkspaceSnapshot = {
  entities: [],
  edges: [],
  current: {},
  issues: [],
  rules: [],
  pipeline: { rejected: 0, duplicates: 0, pending_evaluations: 0 },
  audits: [],
  modelConfigured: false,
};

export function useWorkspaceData(auditFilter: string) {
  const [snapshot, setSnapshot] = useState(emptySnapshot);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const activeRequest = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    try {
      const [
        entities,
        edges,
        current,
        issues,
        rules,
        pipeline,
        audits,
        health,
      ] = await Promise.all([
        api<Entity[]>("/entities", undefined, controller.signal),
        api<Edge[]>("/relationships", undefined, controller.signal),
        api<Record<string, Observation>>(
          "/current",
          undefined,
          controller.signal,
        ),
        api<Issue[]>("/issues", undefined, controller.signal),
        api<Rule[]>("/rules", undefined, controller.signal),
        api<Pipeline>("/pipeline-health", undefined, controller.signal),
        api<Audit[]>(
          `/audit?limit=40${auditFilter ? `&action=${encodeURIComponent(auditFilter)}` : ""}`,
          undefined,
          controller.signal,
        ),
        api<{ model_configured: boolean }>(
          "/health",
          undefined,
          controller.signal,
        ),
      ]);
      setSnapshot({
        entities,
        edges,
        current,
        issues,
        rules,
        pipeline,
        audits,
        modelConfigured: health.model_configured,
      });
      setError("");
    } catch (requestError) {
      if (!controller.signal.aborted) setError(errorMessage(requestError));
    } finally {
      if (activeRequest.current === controller) {
        activeRequest.current = null;
        setLoading(false);
      }
    }
  }, [auditFilter]);

  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(), 10_000);
    return () => {
      window.clearInterval(interval);
      const request = activeRequest.current;
      activeRequest.current = null;
      request?.abort();
    };
  }, [refresh]);

  return { ...snapshot, loading, error, refresh };
}
