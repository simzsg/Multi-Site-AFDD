import { lazy, Suspense, useState } from "react";
import {
  Box,
  Expand,
  Layers3,
  LoaderCircle,
  MousePointer2,
  Pause,
  Play,
  RotateCcw,
} from "lucide-react";
import type { Entity, Issue, Observation } from "../../types";
import type { CameraView } from "./EquipmentScene";
import { PointHistory } from "./PointHistory";
import { EquipmentReadings } from "./EquipmentReadings";
import { stale } from "../../lib/format";
const EquipmentScene = lazy(() => import("./EquipmentScene"));
export function EquipmentInspector({
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
  const [selectedPoint, setSelectedPoint] = useState<Entity | null>(null);
  const [exploded, setExploded] = useState(false),
    [rotate, setRotate] = useState(false),
    [cameraView, setCameraView] = useState<CameraView>("isometric"),
    [resetKey, setResetKey] = useState(0);
  const runPoint = points.find((p) => p.kind === "Run_Status");
  const run = runPoint && current[runPoint.id];
  const running =
    !!run &&
    run.quality === "GOOD" &&
    run.value === 1 &&
    !stale(run.device_timestamp);
  const kind =
    equipment.kind === "AHU"
      ? "Air handling unit"
      : equipment.kind === "IAQ_Device"
        ? "Indoor air quality sensor"
        : "Electricity meter";
  return (
    <section
      aria-label={`3D equipment inspector: ${equipment.label}`}
      className="overflow-hidden rounded-xl border border-alto-100 bg-[#f2f5ed] shadow-[0_6px_30px_-20px_#284f4840]"
    >
      <div className="grid min-w-0 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="relative min-w-0">
          <div className="absolute inset-x-0 top-0 z-10 flex items-start justify-between gap-3 p-5 sm:p-6">
            <div>
              <div className="flex items-center gap-2 text-[9px] font-medium uppercase tracking-[.16em] text-alto-500">
                <Box size={13} />
                Equipment explorer{" "}
                <span className="rounded border border-alto-500/20 px-1.5 py-0.5 text-[8px]">
                  3D
                </span>
              </div>
              <h3
                className="mt-2 text-[16px] font-bold tracking-tight text-alto-900"
                data-testid="inspector-equipment-name"
              >
                {equipment.label}
              </h3>
              <p className="mt-1 text-[10px] text-alto-500">{kind}</p>
            </div>
            <button
              className="rounded-lg border-white/80 bg-white/70 p-2 text-alto-700 shadow-sm hover:bg-white"
              aria-label="Reset 3D view"
              onClick={() => {
                setCameraView("isometric");
                setResetKey((n) => n + 1);
                setRotate(false);
              }}
            >
              <RotateCcw size={15} />
            </button>
          </div>
          <div className="relative h-[365px] bg-[radial-gradient(ellipse_at_center,#ffffff_0%,#edf3e9_78%)] pt-8 sm:h-[410px]">
            <Suspense
              fallback={
                <div className="flex h-full flex-col items-center justify-center gap-3 text-alto-500">
                  <LoaderCircle size={23} className="animate-spin" />
                  <span className="text-xs">Preparing equipment model…</span>
                </div>
              }
            >
              <EquipmentScene
                kind={equipment.kind}
                points={points}
                current={current}
                onSelectPoint={setSelectedPoint}
                equipmentName={equipment.label}
                activeFault={issue?.status === "ACTIVE"}
                running={running}
                exploded={exploded}
                rotate={rotate}
                cameraView={cameraView}
                resetKey={resetKey}
              />
            </Suspense>
            <div className="absolute bottom-3 left-5 right-5 flex justify-between text-[9px] text-alto-500/80">
              <span className="flex items-center gap-1.5">
                <MousePointer2 size={11} />
                Drag to orbit · Scroll to zoom
              </span>
              <span className="hidden sm:inline">
                Illustrative anatomy · not a surveyed model
              </span>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-alto-100 bg-white/60 px-4 py-3">
            <div
              className="flex gap-1"
              role="group"
              aria-label="3D camera views"
            >
              {(["isometric", "front", "top"] as const).map((view) => (
                <button
                  key={view}
                  aria-pressed={cameraView === view}
                  onClick={() => setCameraView(view)}
                  className={`rounded-md border-0 px-2.5 py-1.5 text-[9px] capitalize ${cameraView === view ? "bg-alto-700 text-white hover:bg-alto-900" : "bg-transparent text-alto-500 hover:bg-white"}`}
                >
                  {view}
                </button>
              ))}
            </div>
            <div className="flex gap-1">
              <button
                aria-pressed={exploded}
                onClick={() => setExploded((v) => !v)}
                className={`rounded-md border-0 px-2.5 py-1.5 text-[9px] ${exploded ? "bg-alto-100 text-alto-900" : "bg-transparent text-alto-500"}`}
              >
                <Layers3 size={12} />
                {exploded ? "Close anatomy" : "Explore anatomy"}
              </button>
              <button
                aria-label={rotate ? "Pause model rotation" : "Rotate model"}
                aria-pressed={rotate}
                onClick={() => setRotate((v) => !v)}
                className="rounded-md border-0 bg-transparent p-2 text-alto-500"
              >
                {rotate ? <Pause size={12} /> : <Play size={12} />}
              </button>
            </div>
          </div>
        </div>
        <EquipmentReadings
          equipment={equipment}
          points={points}
          current={current}
          installation={installation}
          served={served}
          issue={issue}
          onInvestigate={onInvestigate}
        />
      </div>
      {selectedPoint && points.some((p) => p.id === selectedPoint.id) && (
        <PointHistory
          key={selectedPoint.id}
          point={selectedPoint}
          onClose={() => setSelectedPoint(null)}
        />
      )}
      <div className="flex items-center gap-2 border-t border-alto-100 bg-white/60 px-5 py-2.5 text-[9px] text-slate-400">
        <Expand size={11} />
        Model geometry is illustrative. Readings and spatial relationships come
        from the equipment registry.
      </div>
    </section>
  );
}
