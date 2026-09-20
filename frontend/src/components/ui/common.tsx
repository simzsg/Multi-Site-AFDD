import { Layers3 } from "lucide-react";
import type { Entity, Observation } from "../../types";
import { date, stale } from "../../lib/format";
export function Badge({
  children,
  tone = "",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return (
    <span className={`badge ${tone}`}>
      <span className="dot" />
      {children}
    </span>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <Layers3 size={28} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Value({
  point,
  current,
}: {
  point?: Entity;
  current: Record<string, Observation>;
}) {
  const value = point && current[point.id];
  if (value?.value === null)
    return (
      <div className="reading">
        <strong>— Missing</strong>
        <span className="warning-text">
          {value.quality} · {date(value.device_timestamp)}
        </span>
      </div>
    );
  if (!value)
    return (
      <span className="muted">
        — <small>Missing</small>
      </span>
    );
  return (
    <div className="reading">
      <strong>
        {value.unit === "bool"
          ? value.value
            ? "ON"
            : "OFF"
          : value.value.toFixed(1)}{" "}
        <small>
          {value.unit === "bool" ? "" : value.unit === "C" ? "°C" : value.unit}
        </small>
      </strong>
      <span
        className={
          stale(value.device_timestamp) || value.quality !== "GOOD"
            ? "warning-text"
            : "muted"
        }
      >
        {value.quality} · {stale(value.device_timestamp) ? "Stale" : "Fresh"}
        <br />
        {date(value.device_timestamp)}
      </span>
    </div>
  );
}
