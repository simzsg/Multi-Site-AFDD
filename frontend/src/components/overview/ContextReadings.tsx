import { useWorkspace } from "../../state/WorkspaceContext";
import { Value } from "../ui/common";
export function ContextReadings() {
  const { current, related, contextEquipment } = useWorkspace();
  return (
    <details className="panel overview-context">
      <summary>
        Room IAQ & floor meters{" "}
        <span>{contextEquipment.length} devices · Context observations</span>
      </summary>
      <div className="context-grid">
        {contextEquipment.flatMap((eq) =>
          related(eq.id, "hasPoint").map((p) => (
            <div key={p.id}>
              <small>
                {eq.label} · {p.label}
              </small>
              <Value point={p} current={current} />
            </div>
          )),
        )}
      </div>
    </details>
  );
}
