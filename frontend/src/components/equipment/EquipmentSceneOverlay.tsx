import { Box, RotateCcw } from "lucide-react";
import type { Entity, Observation } from "../../types";
import { Value } from "../ui/common";

const anchors: Record<string, [number, number, number]> = {
  Supply_Air_Temperature_Sensor: [2.2, 1.12, 0],
  Supply_Air_Temperature_Setpoint: [1.38, 1.46, 0.87],
  Run_Status: [1.23, 1.07, 0.3],
  Return_Air_Temperature_Sensor: [-2.2, 1.12, 0],
  Zone_Air_Temperature_Sensor: [-0.4, 1.4, 0.3],
  Humidity_Sensor: [0.4, 1.4, 0.3],
  CO2_Sensor: [0, 0.6, 0.3],
  Electrical_Power_Sensor: [-0.4, 1.5, 0.45],
  Electrical_Energy_Sensor: [0.4, 1, 0.45],
};

const labels: Record<string, string> = {
  Supply_Air_Temperature_Sensor: "Supply air",
  Supply_Air_Temperature_Setpoint: "Setpoint",
  Run_Status: "Run status",
  Return_Air_Temperature_Sensor: "Return air",
  Zone_Air_Temperature_Sensor: "Temperature",
  Humidity_Sensor: "Humidity",
  CO2_Sensor: "CO₂",
  Electrical_Power_Sensor: "Power",
  Electrical_Energy_Sensor: "Energy",
};

type ReadingsProps = {
  points: Entity[];
  current: Record<string, Observation>;
  onSelectPoint: (point: Entity) => void;
  overlayRef: React.RefObject<HTMLDivElement | null>;
};

export function SceneReadings({ points, current, onSelectPoint, overlayRef }: ReadingsProps) {
  const displayed = points.filter((point) => anchors[point.kind]);
  return (
    <div
      ref={overlayRef}
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-label="3D sensor readings"
    >
      <svg className="absolute inset-0 h-full w-full" aria-hidden="true">
        {displayed.map((point, index) => (
          <line
            key={point.id}
            data-line={index}
            stroke="#53806b"
            strokeWidth="1.5"
            strokeDasharray="3 2"
          />
        ))}
      </svg>
      {displayed.map((point, index) => (
        <button
          key={point.id}
          data-anchor={JSON.stringify(anchors[point.kind])}
          data-index={index}
          data-testid={`sensor-${point.kind}`}
          onClick={() => onSelectPoint(point)}
          aria-label={`View history: ${point.label}`}
          className="pointer-events-auto absolute left-0 top-0 block w-[120px] rounded-lg border border-alto-500/30 bg-white/95 p-2 text-left shadow-sm hover:border-alto-700 focus:ring-2 focus:ring-alto-700"
        >
          <span className="block text-[10px] text-alto-700">{labels[point.kind]} ↗</span>
          <Value point={point} current={current} />
        </button>
      ))}
    </div>
  );
}

export function SceneFallback({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center bg-alto-50 px-8 text-center">
      <Box size={48} strokeWidth={1} className="text-alto-500" />
      <h3 className="mt-4">3D preview unavailable</h3>
      <p className="mt-2 max-w-64 text-xs text-slate-500">
        You can still inspect every reading and relationship below.
      </p>
      <button className="mt-5" onClick={onRetry}>
        <RotateCcw size={14} />
        Retry 3D
      </button>
    </div>
  );
}
