import { useEffect, useState } from "react";
import type { Entity, Observation } from "../../types";
import { date } from "../../lib/format";
import { Value } from "../ui/common";

export function PointHistory({
  point,
  onClose,
}: {
  point: Entity;
  onClose: () => void;
}) {
  const [rows, setRows] = useState<Observation[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    fetch(`/api/points/${encodeURIComponent(point.id)}/history?limit=120`, {
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Unable to load point history");
        return response.json() as Promise<Observation[]>;
      })
      .then((data) => {
        setRows(data.reverse());
        setLoading(false);
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setError(String(e.message));
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [point.id]);
  return (
    <section
      aria-label="Selected point history"
      className="border-t border-alto-100 bg-white p-5"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3>{point.label}</h3>
          <p className="break-all text-xs text-slate-500">
            {point.id} · Latest 120 observations
          </p>
        </div>
        <button onClick={onClose}>Close history</button>
      </div>
      {loading ? (
        <p role="status">Loading history…</p>
      ) : error ? (
        <p role="alert">{error}</p>
      ) : rows.length === 0 ? (
        <p>No observations recorded.</p>
      ) : (
        <div className="mt-3 max-h-60 overflow-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr>
                <th>Device time</th>
                <th>Observed value / quality</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.event_id}>
                  <td className="p-2">{date(row.device_timestamp)}</td>
                  <td className="p-2">
                    <Value point={point} current={{ [point.id]: row }} />
                  </td>
                  <td className="max-w-40 break-all p-2">
                    {row.source?.file || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
