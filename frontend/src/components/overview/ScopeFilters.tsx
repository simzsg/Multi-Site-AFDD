import { ListFilter } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
export function ScopeFilters() {
  const {
    building,
    setBuilding,
    floor,
    setFloor,
    zone,
    setZone,
    label,
    parent,
    buildings,
    floors,
    zones,
    ahus,
  } = useWorkspace();
  return (
    <div className="filters">
      <span>
        <ListFilter size={16} /> Scope
      </span>
      <select
        aria-label="Property"
        value={building}
        onChange={(e) => {
          setBuilding(e.target.value);
          setFloor("");
          setZone("");
        }}
      >
        <option value="">All properties</option>
        {buildings.map((b) => (
          <option key={b.id} value={b.id}>
            {b.label}
          </option>
        ))}
      </select>
      <select
        aria-label="Floor"
        value={floor}
        onChange={(e) => {
          setFloor(e.target.value);
          setZone("");
        }}
      >
        <option value="">All floors</option>
        {floors.map((f) => (
          <option key={f.id} value={f.id}>
            {label(parent(f.id, "Building")?.id ?? "")} · {f.label}
          </option>
        ))}
      </select>
      <select
        aria-label="Zone"
        value={zone}
        onChange={(e) => setZone(e.target.value)}
      >
        <option value="">All zones</option>
        {zones.map((z) => (
          <option key={z.id} value={z.id}>
            {z.label}
          </option>
        ))}
      </select>
      <span className="filter-note">{ahus.length} AHUs in scope</span>
    </div>
  );
}
