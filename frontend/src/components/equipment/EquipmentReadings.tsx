import type { Entity, Issue, Observation } from "../../types";
import { ArrowRight, MapPin, ShieldCheck } from "lucide-react";
import { Value } from "../ui/common";
export function EquipmentReadings({
  equipment,
  points,
  current,
  installation,
  served,
  issue,
  onInvestigate,
}: {
  equipment: Entity;
  points: Entity[];
  current: Record<string, Observation>;
  installation: Entity[];
  served: Entity[];
  issue?: Issue;
  onInvestigate: (issue: Issue) => void;
}) {
  const types =
    equipment.kind === "AHU"
      ? [
          "Supply_Air_Temperature_Sensor",
          "Supply_Air_Temperature_Setpoint",
          "Run_Status",
          "Return_Air_Temperature_Sensor",
        ]
      : equipment.kind === "IAQ_Device"
        ? ["Zone_Air_Temperature_Sensor", "Humidity_Sensor", "CO2_Sensor"]
        : ["Electrical_Power_Sensor", "Electrical_Energy_Sensor"];
  const labels: Record<string, string> = {
    Supply_Air_Temperature_Sensor: "Supply air",
    Supply_Air_Temperature_Setpoint: "Setpoint",
    Run_Status: "Run status",
    Return_Air_Temperature_Sensor: "Return air · Context",
    Zone_Air_Temperature_Sensor: "Room temperature",
    Humidity_Sensor: "Humidity",
    CO2_Sensor: "CO₂",
    Electrical_Power_Sensor: "Active power",
    Electrical_Energy_Sensor: "Cumulative energy",
  };
  return (
    <aside className="min-w-0 border-t border-alto-100 bg-white/90 p-6 lg:border-l lg:border-t-0">
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-[13px] font-bold text-alto-900">
          Equipment readings
        </h3>
        <span className="rounded bg-alto-50 px-2 py-1 text-[9px] text-alto-500">
          Observed values
        </span>
      </div>
      <div className="grid grid-cols-2 gap-x-5 gap-y-6">
        {types.map((type) => (
          <div key={type}>
            <div className="mb-2 text-[10px] text-slate-500">
              {labels[type]}
            </div>
            <Value
              point={points.find((p) => p.kind === type)}
              current={current}
            />
          </div>
        ))}
      </div>
      <div className="mt-6 border-t border-slate-100 pt-5">
        <div className="flex items-center gap-2 text-[9px] font-semibold uppercase tracking-widest text-slate-400">
          <MapPin size={12} />
          Installed in
        </div>
        <p className="mt-2 text-[11px] text-slate-600">
          {installation.map((e) => e.label).join(", ") ||
            "Location not supplied"}
        </p>
        <div className="mt-4 text-[9px] font-semibold uppercase tracking-widest text-slate-400">
          {equipment.kind === "AHU" ? "Served zone" : "Measurement scope"}
        </div>
        <p className="mt-2 text-[11px] text-alto-700">
          {served.map((e) => e.label).join(", ") || "No mapped scope"}
        </p>
      </div>
      {issue ? (
        <button
          className={`mt-5 w-full justify-between rounded-lg border px-3 py-3 text-[10px] ${issue.status === "ACTIVE" ? "border-amber-200 bg-amber-50 text-amber-800" : "border-alto-100 bg-alto-50 text-alto-700"}`}
          onClick={() => onInvestigate(issue)}
        >
          <span>
            {issue.status === "ACTIVE"
              ? "Investigate active issue"
              : "Inspect recovered issue"}
          </span>
          <ArrowRight size={14} />
        </button>
      ) : (
        <div className="mt-5 flex items-center gap-2 text-[10px] text-slate-400">
          <ShieldCheck size={14} />
          No issue recorded for this equipment
        </div>
      )}
    </aside>
  );
}
