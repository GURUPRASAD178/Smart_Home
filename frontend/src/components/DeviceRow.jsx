export default function DeviceRow({ label, hint, device, onToggle, onAuto }) {
  const state = device.on ? "On" : "Off";
  return (
    <li className={`device ${device.on ? "is-on" : ""}`}>
      <div className="device-text">
        <h3>{label}</h3>
        <p className="device-state">
          {state}, {device.auto ? "automatic" : "set by hand"}
        </p>
        <p className="hint">{hint}</p>
      </div>
      <div className="device-controls">
        <button
          type="button"
          role="switch"
          aria-checked={device.on}
          aria-label={`${label} ${device.on ? "on" : "off"}`}
          className="switch"
          onClick={() => onToggle(!device.on)}
        >
          <span className="switch-knob" />
        </button>
        <button type="button" className="chip" aria-pressed={device.auto} disabled={device.auto} onClick={onAuto}>
          Auto
        </button>
      </div>
    </li>
  );
}
