import { ArrowRight, Wind } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
import { Value } from "../ui/common";
export function EquipmentTable() {
  const { ahus, issues, zonesFor, point, current, openIssue } = useWorkspace();
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Equipment / served zone</th>
            <th>Run status</th>
            <th>Supply air</th>
            <th>Setpoint</th>
            <th>
              Return air <small>Context</small>
            </th>
            <th>Attention</th>
          </tr>
        </thead>
        <tbody>
          {ahus.map((eq) => {
            const active =
              issues.find(
                (i) => i.equipment_id === eq.id && i.status === "ACTIVE",
              ) ?? issues.find((i) => i.equipment_id === eq.id);
            return (
              <tr key={eq.id}>
                <td>
                  <div className="equipment-name">
                    <span>
                      <Wind size={17} />
                    </span>
                    <div>
                      <strong>{eq.label}</strong>
                      <small>
                        {zonesFor(eq)
                          .map((z) => z.label)
                          .join(", ")}
                      </small>
                    </div>
                  </div>
                </td>
                {[
                  "Run_Status",
                  "Supply_Air_Temperature_Sensor",
                  "Supply_Air_Temperature_Setpoint",
                  "Return_Air_Temperature_Sensor",
                ].map((kind) => (
                  <td key={kind}>
                    <Value point={point(eq, kind)} current={current} />
                  </td>
                ))}
                <td>
                  {active ? (
                    <button
                      className="text-button danger-text"
                      onClick={() => openIssue(active)}
                    >
                      Investigate <ArrowRight size={14} />
                      <small>{active.status}</small>
                    </button>
                  ) : (
                    <span className="muted">No active issue</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
