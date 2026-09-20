import { ArrowRight, ArrowUpRight, Building2 } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
import { Badge } from "../ui/common";
export function PropertyGrid() {
  const {
    entities,
    issues,
    building,
    setBuilding,
    setFloor,
    setZone,
    parent,
    buildingFor,
    buildings,
  } = useWorkspace();
  return (
    <div className="property-grid">
      {buildings.map((b, i) => {
        const units = entities.filter(
          (e) => e.kind === "AHU" && buildingFor(e)?.id === b.id,
        );
        const count = issues.filter(
          (issue) =>
            issue.status === "ACTIVE" &&
            units.some((u) => u.id === issue.equipment_id),
        ).length;
        return (
          <button
            className={`property-card ${building === b.id ? "chosen" : ""}`}
            key={b.id}
            onClick={() => {
              setBuilding(building === b.id ? "" : b.id);
              setFloor("");
              setZone("");
            }}
          >
            <div className={`building-illustration illustration-${i}`}>
              <Building2 size={78} strokeWidth={0.8} />
              <div className="building-grid" />
              <span className="property-number">0{i + 1}</span>
            </div>
            <div className="property-body">
              <div>
                <h3>{b.label}</h3>
                <ArrowUpRight size={18} />
              </div>
              <p>
                {b.data.property_type} property ·{" "}
                {
                  entities.filter(
                    (f) =>
                      f.kind === "Floor" &&
                      parent(f.id, "Building")?.id === b.id,
                  ).length
                }{" "}
                floors · {units.length} AHUs
              </p>
              <div className="property-footer">
                <Badge tone={count ? "amber" : "green"}>
                  {count
                    ? `${count} active issue${count > 1 ? "s" : ""}`
                    : "No active issues"}
                </Badge>
                <span>
                  View property <ArrowRight size={13} />
                </span>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
