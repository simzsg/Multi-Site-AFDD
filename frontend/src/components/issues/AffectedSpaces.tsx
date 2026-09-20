import { ArrowDown, Layers3, Wind } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
export function AffectedSpaces() {
  const { label, issue } = useWorkspace();
  if (!issue) return null;
  return (
    <section className="panel affected-panel">
      <div className="panel-heading">
        <div>
          <h2>Potentially affected spaces</h2>
          <p>Derived from service relationships</p>
        </div>
      </div>
      <div className="space-tree">
        <div>
          <Wind size={19} />
          <strong>{label(issue.equipment_id)}</strong>
        </div>
        <span>
          <ArrowDown size={15} /> directly feeds
        </span>
        {issue.data.affected.zones.map((z) => (
          <div key={z.id}>
            <Layers3 size={18} />
            {z.label}
          </div>
        ))}
        <span>
          <ArrowDown size={15} /> contains
        </span>
        {issue.data.affected.rooms.map((r) => (
          <div className="room-node" key={r.id}>
            <span className="dot" />
            {r.label}
          </div>
        ))}
      </div>
      <div className="installation">
        <small>INSTALLATION LOCATION</small>
        <p>{issue.data.affected.installation.map((r) => r.label).join(", ")}</p>
        <span>Separate from the rooms served above.</span>
      </div>
    </section>
  );
}
