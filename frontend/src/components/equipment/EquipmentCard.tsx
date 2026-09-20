import { Activity, ArrowUpRight, Gauge, Wind } from "lucide-react";
import type { Entity, Issue, Observation } from "../../types";
import { stale } from "../../lib/format";
export function EquipmentCard({
  equipment,
  selected,
  observation,
  issue,
  onSelect,
}: {
  equipment: Entity;
  selected: boolean;
  observation?: Observation;
  issue?: Issue;
  onSelect: () => void;
}) {
  const Icon =
    equipment.kind === "AHU"
      ? Wind
      : equipment.kind === "IAQ_Device"
        ? Activity
        : Gauge;
  return (
    <button
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={`Inspect ${equipment.label} in 3D`}
      className={`group flex min-w-0 flex-col items-stretch justify-start rounded-xl border p-4 text-left transition-all ${selected ? "border-alto-500 bg-alto-50 shadow-sm ring-1 ring-alto-500/20" : "border-slate-200/70 bg-white hover:border-alto-500/50 hover:bg-alto-50/60"}`}
    >
      <div className="flex items-center justify-between">
        <span
          className={`flex h-9 w-9 items-center justify-center rounded-lg ${selected ? "bg-alto-700 text-white" : "bg-alto-50 text-alto-500"}`}
        >
          <Icon size={18} />
        </span>
        <ArrowUpRight
          size={15}
          className={selected ? "text-alto-700" : "text-slate-300"}
        />
      </div>
      <strong className="mt-3 truncate text-[12px] font-semibold text-alto-900">
        {equipment.label}
      </strong>
      <div className="mt-2 flex items-center justify-between gap-2">
        <span className="text-[10px] font-normal text-slate-400">
          {observation
            ? stale(observation.device_timestamp)
              ? "Recorded reading"
              : "Fresh reading"
            : "No readings"}
        </span>
        <span className="text-[12px] font-semibold text-alto-700">
          {observation?.value == null ? "—" : observation.value.toFixed(1)}{" "}
          {observation?.unit === "C" ? "°C" : observation?.unit}
        </span>
      </div>
      {issue && (
        <span
          className={`mt-3 text-[9px] font-medium ${issue.status === "ACTIVE" ? "text-amber-700" : "text-slate-500"}`}
        >
          {issue.status === "ACTIVE"
            ? "● Attention required"
            : "◌ Recovered issue · Evidence available"}
        </span>
      )}
    </button>
  );
}
