import type { Config, Sample } from "../../types";
import { time } from "../../lib/format";
import { Empty } from "../ui/common";
export function Trend({
  samples,
  logic,
}: {
  samples: Sample[];
  logic: Config["logic"];
}) {
  if (!samples.length) return <Empty title="No observations" />;
  const values = samples
    .flatMap((s) => [
      s.observations[logic.left]?.value,
      s.observations[logic.right]?.value,
    ])
    .filter((n): n is number => n != null);
  const min = Math.floor(Math.min(...values) - 2),
    max = Math.ceil(Math.max(...values) + 2);
  const x = (i: number) => 55 + (i / Math.max(1, samples.length - 1)) * 680;
  const y = (v: number) => 220 - ((v - min) / (max - min)) * 180;
  const line = (kind: string) =>
    samples
      .map(
        (s, i) =>
          `${i ? "L" : "M"}${x(i)},${y(s.observations[kind]?.value ?? min)}`,
      )
      .join(" ");
  return (
    <div className="trend">
      <svg
        viewBox="0 0 780 270"
        role="img"
        aria-label="Supply air and setpoint temperatures during the qualifying interval"
      >
        <rect x="55" y="25" width="680" height="195" fill="#fdf5ef" />
        {[0, 1, 2, 3, 4].map((i) => (
          <g key={i}>
            <line
              x1="55"
              x2="735"
              y1={40 + i * 45}
              y2={40 + i * 45}
              stroke="#e6e9e5"
              strokeDasharray="3 4"
            />
            <text x="15" y={45 + i * 45}>
              {(max - (i * (max - min)) / 4).toFixed(0)}°
            </text>
          </g>
        ))}
        <path
          d={line(logic.right)}
          stroke="#95a19f"
          strokeWidth="2"
          strokeDasharray="6 5"
          fill="none"
        />
        <path
          d={line(logic.left)}
          stroke="#b66541"
          strokeWidth="3"
          fill="none"
        />
        <line
          x1="735"
          x2="735"
          y1="25"
          y2="220"
          stroke="#b66541"
          strokeDasharray="3 3"
        />
        <text x="570" y="18" fill="#b66541">
          Issue triggered ↓
        </text>
        {[0, Math.floor((samples.length - 1) / 2), samples.length - 1].map(
          (i, n) => (
            <text key={n} x={x(i) - 18} y="248">
              {time(samples[i].at)}
            </text>
          ),
        )}
      </svg>
      <div className="legend">
        <span>
          <i className="sat" />
          Supply air temperature
        </span>
        <span>
          <i />
          Temperature setpoint
        </span>
        <span className="muted">Shaded: qualifying interval</span>
      </div>
    </div>
  );
}
