import { Building2, Radio, TriangleAlert, Wind } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
export function PortfolioMetrics() {
  const {
    building,
    buildings,
    floors,
    ahus,
    activeIssues,
    scopedPoints,
    servedRoomCount,
    freshCount,
  } = useWorkspace();
  return (
    <div className="metrics">
      <div>
        <span>
          Properties monitored <Building2 size={17} />
        </span>
        <strong>
          {building ? 1 : buildings.length}
          <small>properties</small>
        </strong>
        <p>
          {floors.length} floors · {servedRoomCount} served rooms
        </p>
      </div>
      <div>
        <span>
          AHUs in scope <Wind size={17} />
        </span>
        <strong>
          {ahus.length}
          <small>air handling units</small>
        </strong>
        <p>Explicit equipment-to-space relationships</p>
      </div>
      <div className="metric-alert">
        <span>
          Active issues <TriangleAlert size={17} />
        </span>
        <strong>
          {activeIssues.length}
          <small>requiring attention</small>
        </strong>
        <p>
          {activeIssues.filter((i) => i.data.severity === "CRITICAL").length}{" "}
          critical · Evidence available
        </p>
      </div>
      <div>
        <span>
          Fresh observations <Radio size={17} />
        </span>
        <strong>
          {freshCount}
          <small>/ {scopedPoints.length} AHU points</small>
        </strong>
        <p>GOOD quality · observed within 2 minutes</p>
      </div>
    </div>
  );
}
