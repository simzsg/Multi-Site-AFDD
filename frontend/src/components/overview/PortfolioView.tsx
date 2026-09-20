import { useWorkspace } from "../../state/WorkspaceContext";
import { PortfolioMetrics } from "./PortfolioMetrics";
import { PropertyGrid } from "./PropertyGrid";
import { EquipmentOverview } from "./EquipmentOverview";
import { ContextReadings } from "./ContextReadings";
export function PortfolioView() {
  const { buildings } = useWorkspace();
  return (
    <>
      <PortfolioMetrics />
      <div className="section-title">
        <h2>
          Properties <span>{buildings.length}</span>
        </h2>
        <span className="muted">A connected view of your buildings</span>
      </div>
      <PropertyGrid />
      <EquipmentOverview />
      <ContextReadings />
    </>
  );
}
