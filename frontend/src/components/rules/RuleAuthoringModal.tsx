import {
  ArrowRight,
  Check,
  LoaderCircle,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import type { AIResult } from "../../types";
import { useWorkspace } from "../../state/WorkspaceContext";
import { Badge } from "../ui/common";
import { api } from "../../lib/api";
export function RuleAuthoringModal() {
  const {
    notice,
    busy,
    setPreview,
    setAuthorOpen,
    prompt,
    setPrompt,
    mode,
    setMode,
    aiResult,
    setAiResult,
    modelConfigured,
    act,
    openRule,
  } = useWorkspace();
  return (
    <div
      className="modal-backdrop"
      onClick={() => !busy && setAuthorOpen(false)}
    >
      <section
        className="author-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="author-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-top">
          <span className="sparkle-icon">
            <Sparkles size={22} />
          </span>
          <button
            className="icon-button"
            aria-label="Close rule authoring"
            disabled={busy}
            onClick={() => setAuthorOpen(false)}
          >
            <X size={20} />
          </button>
        </div>
        <div className="eyebrow">AI-ASSISTED RULE AUTHORING</div>
        <h2 id="author-title">Turn your knowledge into a rule.</h2>
        <p>
          Describe what to monitor. Review the logic and affected equipment
          before anything goes live.
        </p>
        <label className="field-label">
          Describe your monitoring rule
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={6}
          />
        </label>
        <div className="mode-selector">
          <label>
            Authoring mode
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as "demo" | "model")}
            >
              <option value="demo">Demo · exact example, no model call</option>
              <option value="model">
                Real model
                {modelConfigured ? "" : " · server credentials required"}
              </option>
            </select>
          </label>
        </div>
        <div className="author-safety">
          <ShieldCheck size={17} />
          <span>AI can draft and preview. Only you can activate.</span>
        </div>
        <button
          className="primary full-width"
          disabled={busy || prompt.length < 10}
          onClick={() =>
            void act(async () => {
              const result = await api<AIResult>("/ai/requests", {
                prompt,
                mode,
              });
              setAiResult(result);
            })
          }
        >
          {busy ? (
            <LoaderCircle className="spin" size={17} />
          ) : (
            <Sparkles size={17} />
          )}{" "}
          {busy
            ? "Discovering, validating & previewing…"
            : "Generate rule draft"}
        </button>
        {notice && (
          <p className="error" role="alert">
            {notice}
          </p>
        )}
        {aiResult && (
          <div className="ai-result">
            <Badge tone={aiResult.state === "DRAFT_READY" ? "green" : "amber"}>
              {aiResult.state.replaceAll("_", " ")}
            </Badge>
            <p>{aiResult.message}</p>
            <ol>
              {aiResult.traces.map((t, i) => (
                <li key={i}>
                  <Check size={13} />
                  {t.tool.replaceAll("_", " ")}
                  <small>{t.elapsed_ms} ms</small>
                </li>
              ))}
            </ol>
            {aiResult.draft && (
              <button
                className="primary full-width"
                onClick={() => {
                  openRule(aiResult.draft!);
                  setPreview(aiResult.preview ?? null);
                  setAuthorOpen(false);
                }}
              >
                Review draft & targets <ArrowRight size={16} />
              </button>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
