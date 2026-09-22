import { useCallback, useState } from "react";
import type { AIResult, Issue, Preview, Rule } from "../types";
import { errorMessage } from "../lib/api";
import { example } from "../lib/format";
import { useWorkspaceData } from "./useWorkspaceData";
import { useWorkspaceProjection } from "./useWorkspaceProjection";

export function useWorkspaceController() {
  const [view, setView] = useState<
    "overview" | "issues" | "rules" | "pipeline"
  >("overview");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [building, setBuilding] = useState("");
  const [floor, setFloor] = useState("");
  const [zone, setZone] = useState("");
  const [query, setQuery] = useState("");
  const [selectedIssue, setSelectedIssue] = useState("");
  const [selectedRule, setSelectedRule] = useState("");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [editor, setEditor] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [reviewer, setReviewer] = useState("");
  const [authorOpen, setAuthorOpen] = useState(false);
  const [prompt, setPrompt] = useState(example);
  const [mode, setMode] = useState<"demo" | "model">("demo");
  const [aiResult, setAiResult] = useState<AIResult | null>(null);
  const [auditFilter, setAuditFilter] = useState("");
  const data = useWorkspaceData(auditFilter);
  const projection = useWorkspaceProjection({
    ...data,
    building,
    floor,
    zone,
    query,
    selectedIssue,
    selectedRule,
  });

  const act = useCallback(
    async (operation: () => Promise<void>) => {
      setBusy(true);
      setNotice("");
      try {
        await operation();
        await data.refresh();
      } catch (operationError) {
        setNotice(errorMessage(operationError));
      } finally {
        setBusy(false);
      }
    },
    [data.refresh],
  );
  const openRule = useCallback((rule: Rule) => {
    setSelectedRule(rule.id);
    setEditor(JSON.stringify(rule.config, null, 2));
    setPreview(null);
    setConfirmed(false);
    setView("rules");
  }, []);
  const openIssue = useCallback((issue: Issue) => {
    setSelectedIssue(issue.id);
    setView("issues");
  }, []);

  return {
    ...data,
    ...projection,
    view,
    setView,
    notice,
    setNotice,
    busy,
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
    auditFilter,
    setAuditFilter,
    act,
    openRule,
    openIssue,
  };
}
