import {
  ArrowRight,
  Check,
  GitBranch,
  Search,
  ShieldCheck,
} from "lucide-react";
import type { Preview, Rule } from "../../types";
import { useWorkspace } from "../../state/WorkspaceContext";
import { Badge, Empty } from "../ui/common";
import { api } from "../../lib/api";
export function RuleDetail() {
  const {
    setNotice,
    busy,
    preview,
    setPreview,
    editor,
    setEditor,
    confirmed,
    setConfirmed,
    reviewer,
    setReviewer,
    act,
    label,
    rule,
    openRule,
  } = useWorkspace();
  return (
    <section className="panel rule-detail">
      {!rule ? (
        <Empty title="Select a rule to review">
          Explore its scope, logic, overrides, and target preview.
        </Empty>
      ) : (
        <>
          <div className="panel-heading">
            <div>
              <h2>{rule.config.name}</h2>
              <p>
                Version {rule.version} · {rule.status}
              </p>
            </div>
            <Badge tone="green">
              <ShieldCheck size={12} /> Human controlled
            </Badge>
          </div>
          <p className="rule-intent">{rule.config.intent}</p>
          <label className="editor-label">
            Structured configuration{" "}
            <small>
              Editing creates a new draft version and preserves existing
              evidence.
            </small>
            <textarea
              className="code-editor"
              aria-label="Rule configuration"
              value={editor}
              onChange={(e) => setEditor(e.target.value)}
            />
          </label>
          <div className="rule-actions">
            <button
              disabled={busy}
              onClick={() =>
                void act(async () => {
                  const result = await api<{
                    valid: boolean;
                    errors: string[];
                  }>(`/rules/${rule.id}/validate`, {});
                  setNotice(
                    result.valid
                      ? "Saved rule is valid."
                      : result.errors.join("; "),
                  );
                })
              }
            >
              <Check size={15} /> Validate saved rule
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void act(async () => {
                  setPreview(
                    await api<Preview>(`/rules/${rule.id}/preview`, {}),
                  );
                  setConfirmed(false);
                })
              }
            >
              <Search size={15} /> Preview saved targets
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void act(async () => {
                  const updated = await api<Rule>(
                    `/rules/${rule.id}/adjust`,
                    JSON.parse(editor),
                  );
                  openRule(updated);
                  setNotice(
                    "New draft version created. Review and preview before activation.",
                  );
                })
              }
            >
              <GitBranch size={15} /> Save as new version
            </button>
            {rule.status === "ACTIVE" && (
              <button
                disabled={busy}
                onClick={() =>
                  void act(async () => {
                    await api(`/rules/${rule.id}/disable`, {});
                    setNotice(
                      "Rule disabled. Existing active occurrences are stopped.",
                    );
                  })
                }
              >
                Disable
              </button>
            )}
          </div>
          {preview && (
            <div className="preview">
              <div className="section-title">
                <h3>Target preview</h3>
                <Badge tone="green">
                  {preview.matches.length} matched assets
                </Badge>
              </div>
              {preview.matches.map((m) => (
                <div className="preview-row" key={m.equipment_id}>
                  <div>
                    <strong>{m.label}</strong>
                    <small>
                      {m.paths
                        .map(
                          (p) =>
                            `${label(p.building)} → ${label(p.floor)} → ${label(p.zone)}`,
                        )
                        .join(", ")}
                    </small>
                  </div>
                  <div>
                    <strong>
                      {m.effective.threshold}°C / {m.effective.duration_minutes}{" "}
                      min
                    </strong>
                    <small>
                      Global {m.global.threshold}°C /{" "}
                      {m.global.duration_minutes} min
                      {Object.keys(m.override).length
                        ? " · Local override applied"
                        : " · No override"}
                    </small>
                  </div>
                </div>
              ))}
              {preview.exclusions.length > 0 && (
                <details>
                  <summary>
                    {preview.exclusions.length} excluded equipment
                  </summary>
                  {preview.exclusions.map((e) => (
                    <p key={e.equipment_id}>
                      {label(e.equipment_id)} — {e.reason}{" "}
                      {e.missing_points?.join(", ")}
                    </p>
                  ))}
                </details>
              )}
              {rule.status === "DRAFT" && (
                <div className="confirmation">
                  <h3>
                    <ShieldCheck size={18} /> Review & activate
                  </h3>
                  <p>
                    Activation uses the saved configuration above. Changes in
                    the editor must be saved as a new version first.
                  </p>
                  <input
                    aria-label="Reviewer name"
                    placeholder="Your name"
                    value={reviewer}
                    onChange={(e) => setReviewer(e.target.value)}
                  />
                  <label>
                    <input
                      type="checkbox"
                      checked={confirmed}
                      onChange={(e) => setConfirmed(e.target.checked)}
                    />{" "}
                    I reviewed the saved rule, matched assets, exclusions, and
                    effective values.
                  </label>
                  <button
                    className="primary"
                    disabled={
                      !confirmed ||
                      !reviewer.trim() ||
                      busy ||
                      !preview.matches.length ||
                      editor !== JSON.stringify(rule.config, null, 2)
                    }
                    onClick={() =>
                      void act(async () => {
                        await api(`/rules/${rule.id}/activate`, {
                          confirmed: true,
                          preview_digest: preview.digest,
                          reviewer,
                        });
                        setNotice("Rule activated with your review recorded.");
                        setConfirmed(false);
                      })
                    }
                  >
                    Confirm & activate <ArrowRight size={15} />
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
}
