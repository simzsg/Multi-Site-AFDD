import {
  Activity,
  ArrowRight,
  Radio,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
import { Badge } from "../ui/common";
import { date, stale } from "../../lib/format";
export function PipelineHealth() {
  const { pipeline, audits, auditFilter, setAuditFilter, live } =
    useWorkspace();
  return (
    <>
      <div className="metrics">
        <div>
          <span>
            Ingestion <Radio size={17} />
          </span>
          <strong className="word-metric">{live ? "Receiving" : "Idle"}</strong>
          <p>{date(pipeline.ingestion?.last_received_at)}</p>
        </div>
        <div>
          <span>
            Evaluator <Activity size={17} />
          </span>
          <strong className="word-metric">
            {stale(pipeline.evaluator?.last_evaluated_at, 45)
              ? "Idle"
              : "Running"}
          </strong>
          <p>{date(pipeline.evaluator?.last_evaluated_at)}</p>
        </div>
        <div>
          <span>
            Rejected events <TriangleAlert size={17} />
          </span>
          <strong>{pipeline.rejected}</strong>
          <p>Visible in the audit log below</p>
        </div>
        <div>
          <span>
            Duplicates suppressed <ShieldCheck size={17} />
          </span>
          <strong>{pipeline.duplicates}</strong>
          <p>No second telemetry effect</p>
        </div>
      </div>
      <p className="quality-summary">
        {pipeline.late ?? 0} late point observations ·{" "}
        {pipeline.incomplete ?? 0} explicit missing measurements ·{" "}
        {pipeline.data_gap ?? 0} detected point gaps
      </p>
      <div className="pipeline-flow">
        <span>Simulator</span>
        <ArrowRight />
        <span>Redis Streams</span>
        <ArrowRight />
        <span>Ingestion</span>
        <ArrowRight />
        <span>TimescaleDB</span>
        <ArrowRight />
        <span>AFDD evaluator</span>
      </div>
      <div className="section-title">
        <h2>Event trail</h2>
        <select
          aria-label="Audit event type"
          value={auditFilter}
          onChange={(e) => setAuditFilter(e.target.value)}
        >
          <option value="">All events</option>
          {[
            "rejected",
            "duplicate",
            "late",
            "incomplete",
            "data_gap",
            "issue_triggered",
            "human_confirmed_activation",
          ].map((a) => (
            <option key={a} value={a}>
              {a.replaceAll("_", " ")}
            </option>
          ))}
        </select>
        <span className="muted">
          {pipeline.pending_evaluations} pending evaluations · Latest ingestion
          lag {pipeline.ingestion?.lag_seconds?.toFixed(1) ?? "—"}s
        </span>
      </div>
      <section className="panel">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Platform time</th>
                <th>Event</th>
                <th>Trace context</th>
              </tr>
            </thead>
            <tbody>
              {audits.map((a) => (
                <tr key={a.id}>
                  <td className="nowrap">{date(a.at)}</td>
                  <td>
                    <Badge tone={a.action === "rejected" ? "amber" : ""}>
                      {a.action.replaceAll("_", " ")}
                    </Badge>
                  </td>
                  <td>
                    <details>
                      <summary>
                        {String(
                          a.data.event_id ??
                            a.data.rule_version ??
                            a.data.issue_id ??
                            "View details",
                        )}
                      </summary>
                      <pre>{JSON.stringify(a.data, null, 2)}</pre>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
