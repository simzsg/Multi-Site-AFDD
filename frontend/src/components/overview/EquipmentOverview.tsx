import { useState } from "react";
import { Activity, Box, Gauge, List, Search, Wind } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
import { Empty } from "../ui/common";
import { EquipmentInspector } from "../equipment/EquipmentInspector";
import { EquipmentCard } from "../equipment/EquipmentCard";
import { EquipmentTable } from "../equipment/EquipmentTable";

export function EquipmentOverview() {
  const {
    current,
    issues,
    query,
    setQuery,
    ahus,
    related,
    contextEquipment,
    openIssue,
  } = useWorkspace();
  const [kind, setKind] = useState("AHU"),
    [selected, setSelected] = useState(""),
    [display, setDisplay] = useState<"3d" | "table">("3d");
  const equipment =
    kind === "AHU"
      ? ahus
      : contextEquipment.filter(
          (e) =>
            e.kind === kind &&
            e.label.toLowerCase().includes(query.toLowerCase()),
        );
  const inspected = equipment.find((e) => e.id === selected) ?? equipment[0];
  const issueFor = (id: string) =>
    issues.find((i) => i.equipment_id === id && i.status === "ACTIVE") ??
    issues.find((i) => i.equipment_id === id);
  return (
    <section
      className="mb-6 rounded-xl border border-slate-200/80 bg-white p-4 sm:p-6"
      aria-labelledby="equipment-title"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2
            id="equipment-title"
            className="text-base font-bold text-alto-900"
          >
            Equipment overview
          </h2>
          <p className="mt-1 text-[11px] text-slate-400">
            A closer look at the systems behind your buildings.
          </p>
        </div>
        <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 text-slate-400">
          <Search size={14} />
          <input
            aria-label="Search equipment"
            placeholder="Search equipment…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-40 border-0 bg-transparent px-0 py-2 text-[11px] shadow-none focus:shadow-none"
          />
        </label>
      </div>
      <div className="my-5 flex flex-wrap items-center justify-between gap-3">
        <div
          className="flex gap-1 rounded-lg bg-slate-50 p-1"
          role="group"
          aria-label="Equipment type"
        >
          {[
            { kind: "AHU", label: "Air handling", icon: Wind },
            { kind: "IAQ_Device", label: "Air quality", icon: Activity },
            { kind: "Electrical_Meter", label: "Energy meters", icon: Gauge },
          ].map((t) => (
            <button
              key={t.kind}
              aria-pressed={kind === t.kind}
              onClick={() => {
                setKind(t.kind);
                setSelected("");
                setQuery("");
                setDisplay("3d");
              }}
              className={`rounded-md border-0 px-3 py-2 text-[10px] ${kind === t.kind ? "bg-white text-alto-700 shadow-sm" : "bg-transparent text-slate-400 hover:bg-white"}`}
            >
              <t.icon size={13} />
              {t.label}
            </button>
          ))}
        </div>
        {kind === "AHU" && (
          <div
            className="flex gap-1 rounded-lg border border-slate-200 p-1"
            role="group"
            aria-label="Equipment display"
          >
            <button
              aria-pressed={display === "3d"}
              onClick={() => setDisplay("3d")}
              className={`rounded-md border-0 px-3 py-1.5 text-[10px] ${display === "3d" ? "bg-alto-50 text-alto-700" : "bg-white text-slate-400"}`}
            >
              <Box size={13} />
              3D explorer
            </button>
            <button
              aria-pressed={display === "table"}
              onClick={() => setDisplay("table")}
              className={`rounded-md border-0 px-3 py-1.5 text-[10px] ${display === "table" ? "bg-alto-50 text-alto-700" : "bg-white text-slate-400"}`}
            >
              <List size={13} />
              Table
            </button>
          </div>
        )}
      </div>
      {!equipment.length ? (
        <Empty title="No equipment matches this scope">
          Choose another property or clear your search.
        </Empty>
      ) : display === "table" ? (
        <EquipmentTable />
      ) : (
        <>
          {inspected && (
            <EquipmentInspector
              equipment={inspected}
              points={related(inspected.id, "hasPoint")}
              current={current}
              installation={related(inspected.id, "hasLocation")}
              served={related(
                inspected.id,
                kind === "AHU" ? "feeds" : "measuresSpace",
              )}
              issue={issueFor(inspected.id)}
              onInvestigate={openIssue}
            />
          )}
          <div className="mb-3 mt-5 flex items-center justify-between">
            <h3 className="text-[11px] font-semibold text-slate-500">
              Select equipment to explore
            </h3>
            <span className="text-[10px] text-slate-400">
              {equipment.length} in scope
            </span>
          </div>
          <div className="grid max-h-[360px] grid-cols-1 gap-3 overflow-y-auto p-0.5 min-[480px]:grid-cols-2 xl:grid-cols-4">
            {equipment.map((e) => {
              const primary = related(e.id, "hasPoint").find(
                (p) =>
                  p.kind ===
                  (kind === "AHU"
                    ? "Supply_Air_Temperature_Sensor"
                    : kind === "IAQ_Device"
                      ? "Zone_Air_Temperature_Sensor"
                      : "Electrical_Power_Sensor"),
              );
              return (
                <EquipmentCard
                  key={e.id}
                  equipment={e}
                  selected={inspected?.id === e.id}
                  observation={primary ? current[primary.id] : undefined}
                  issue={issueFor(e.id)}
                  onSelect={() => setSelected(e.id)}
                />
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
