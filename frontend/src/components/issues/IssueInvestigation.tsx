import { ShieldCheck, TriangleAlert } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
import { Badge, Empty, Value } from "../ui/common";
import { date } from "../../lib/format";
import { Trend } from "./Trend";
import { AffectedSpaces } from "./AffectedSpaces";
export function IssueInvestigation() {
  const {
    entities,
    current,
    setSelectedIssue,
    label,
    related,
    parent,
    filteredIssues,
    issue,
  } = useWorkspace();
  return !filteredIssues.length ? (
    <Empty title="No issues in this scope">
      Activate a reviewed rule and stream telemetry to begin monitoring.
    </Empty>
  ) : (
    <>
      <div className="issue-tabs">
        {filteredIssues.map((i) => (
          <button
            className={issue?.id === i.id ? "active" : ""}
            key={i.id}
            onClick={() => setSelectedIssue(i.id)}
          >
            {label(i.equipment_id)}{" "}
            <Badge tone={i.status === "ACTIVE" ? "amber" : "green"}>
              {i.status}
            </Badge>
          </button>
        ))}
      </div>
      {issue && (
        <>
          <div className="issue-banner">
            <span className="alert-icon">
              <TriangleAlert size={24} />
            </span>
            <div>
              <div className="eyebrow">
                {issue.data.severity} · {issue.status}
              </div>
              <h2>{label(issue.equipment_id)} · Temperature deviation</h2>
              <p>
                Difference {issue.data.calculated_difference.toFixed(1)}{" "}
                {issue.data.effective.unit} was{" "}
                {issue.data.effective.operator === "DIFF_LT"
                  ? "below"
                  : "above"}{" "}
                {issue.data.threshold} {issue.data.effective.unit} for{" "}
                {issue.data.effective.duration_minutes} continuous minutes while
                the AHU was{" "}
                {issue.data.effective.operating_equals ? "ON" : "OFF"}.
              </p>
            </div>
            <Badge>Rule v{issue.data.rule_version}</Badge>
          </div>
          <div className="investigation-grid">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>What triggered this issue?</h2>
                  <p>
                    {date(issue.data.trigger_interval.start)} →{" "}
                    {date(issue.data.trigger_interval.end)}
                  </p>
                </div>
                <Badge tone="green">Evidence preserved</Badge>
              </div>
              <Trend
                samples={issue.data.observations}
                logic={issue.data.effective}
              />
              <div className="evidence-summary">
                <div>
                  <small>THRESHOLD</small>
                  <strong>
                    {issue.data.effective.operator === "DIFF_LT" ? "<" : ">"}{" "}
                    {issue.data.threshold} {issue.data.effective.unit}
                  </strong>
                </div>
                <div>
                  <small>DURATION</small>
                  <strong>
                    {issue.data.effective.duration_minutes} minutes
                  </strong>
                </div>
                <div>
                  <small>RUN STATUS</small>
                  <strong>
                    {issue.data.effective.operating_equals ? "ON" : "OFF"}{" "}
                    throughout
                  </strong>
                </div>
                <div>
                  <small>DATA QUALITY</small>
                  <strong>{issue.data.data_quality}</strong>
                </div>
              </div>
              <div className="explanation">
                <ShieldCheck size={18} />
                <p>
                  All triggering observations are preserved with device
                  timestamps. No stale or missing inputs qualify. This signal
                  supports investigation; it does not establish a mechanical
                  root cause.
                </p>
              </div>
            </section>
            <AffectedSpaces />
          </div>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Context around the issue</h2>
                <p>
                  Live context only — these readings did not trigger this issue
                </p>
              </div>
            </div>
            <div className="context-grid">
              {entities
                .filter(
                  (e) =>
                    e.id === issue.equipment_id ||
                    (e.kind === "IAQ_Device" &&
                      related(e.id, "hasLocation").some((r) =>
                        issue.data.affected.rooms.some(
                          (room) => room.id === r.id,
                        ),
                      )) ||
                    (e.kind === "Electrical_Meter" &&
                      [
                        ...related(e.id, "measuresSpace"),
                        ...related(e.id, "hasLocation"),
                      ].some((f) =>
                        issue.data.affected.zones.some(
                          (z) => parent(z.id, "Floor")?.id === f.id,
                        ),
                      )),
                )
                .flatMap((eq) =>
                  related(eq.id, "hasPoint")
                    .filter(
                      (p) =>
                        eq.kind !== "AHU" ||
                        ["Return_Air_Temperature_Sensor", "Alarm"].includes(
                          p.kind,
                        ),
                    )
                    .map((p) => (
                      <div key={p.id}>
                        <small>
                          {eq.label} · {p.label}
                        </small>
                        <Value point={p} current={current} />
                      </div>
                    )),
                )}
            </div>
          </section>
          <details className="panel evidence-details">
            <summary>
              Inspect raw evidence · {issue.data.observations.length}{" "}
              observations
            </summary>
            <pre>{JSON.stringify(issue.data, null, 2)}</pre>
          </details>
        </>
      )}
    </>
  );
}
