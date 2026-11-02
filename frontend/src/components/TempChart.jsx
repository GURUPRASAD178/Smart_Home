// Temperature over the last minute, with the fan threshold drawn in and
// small ticks along the bottom wherever the IR sensor saw movement.

const W = 640;
const H = 220;
const PAD = { top: 16, right: 16, bottom: 30, left: 40 };

function clock(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function TempChart({ readings, threshold }) {
  if (readings.length < 2) {
    return <p className="empty">Waiting for the first few readings…</p>;
  }

  const temps = readings.map((r) => r.temp);
  let lo = Math.min(...temps, threshold) - 1;
  let hi = Math.max(...temps, threshold) + 1;
  if (hi - lo < 6) {
    const mid = (hi + lo) / 2;
    lo = mid - 3;
    hi = mid + 3;
  }

  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const x = (i) => PAD.left + (i / (readings.length - 1)) * innerW;
  const y = (t) => PAD.top + (1 - (t - lo) / (hi - lo)) * innerH;

  const line = readings.map((r, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(r.temp).toFixed(1)}`).join(" ");
  const ticks = [lo, (lo + hi) / 2, hi].map((t) => Math.round(t));
  const last = readings[readings.length - 1];

  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`Temperature over the last ${readings.length} readings, now ${last.temp} degrees`}>
      {ticks.map((t) => (
        <g key={t}>
          <line x1={PAD.left} x2={W - PAD.right} y1={y(t)} y2={y(t)} className="chart-grid" />
          <text x={PAD.left - 8} y={y(t) + 4} textAnchor="end" className="chart-text">{t}°</text>
        </g>
      ))}

      <line x1={PAD.left} x2={W - PAD.right} y1={y(threshold)} y2={y(threshold)} className="chart-threshold" />
      <text x={W - PAD.right} y={y(threshold) - 6} textAnchor="end" className="chart-text chart-text-accent">
        Fan starts at {threshold}°
      </text>

      <path d={line} className="chart-line" />
      <circle cx={x(readings.length - 1)} cy={y(last.temp)} r="4.5" className="chart-dot" />

      {readings.map((r, i) =>
        r.motion ? (
          <line key={i} x1={x(i)} x2={x(i)} y1={H - PAD.bottom + 8} y2={H - PAD.bottom + 16} className="chart-motion" />
        ) : null
      )}

      <text x={PAD.left} y={H - 2} className="chart-text">{clock(readings[0].at)}</text>
      <text x={W - PAD.right} y={H - 2} textAnchor="end" className="chart-text">{clock(last.at)}</text>
    </svg>
  );
}
