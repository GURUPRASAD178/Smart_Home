import { useEffect, useState } from "react";

// A number field that saves when you leave it (or press Enter) instead of on every keystroke.
function NumberSetting({ label, unit, value, min, max, step, onSave }) {
  const [draft, setDraft] = useState(String(value));
  useEffect(() => setDraft(String(value)), [value]);

  const commit = () => {
    const n = Number(draft);
    if (draft.trim() === "" || Number.isNaN(n) || n === value) return setDraft(String(value));
    onSave(n);
  };

  return (
    <label className="field">
      <span>{label}</span>
      <span className="field-input">
        <input
          type="number"
          inputMode="decimal"
          value={draft}
          min={min}
          max={max}
          step={step}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
        />
        <span className="unit">{unit}</span>
      </span>
    </label>
  );
}

export function AlarmPanel({ config, onArm, onSilence }) {
  const status = config.alarm_active ? "Triggered" : config.armed ? "Armed" : "Off";
  return (
    <section className={`panel alarm ${config.alarm_active ? "is-triggered" : ""}`} aria-labelledby="alarm-h">
      <h2 id="alarm-h">Alarm</h2>
      <p className="alarm-status">{status}</p>
      <p className="hint">
        {config.armed
          ? "Any movement at the IR sensor sounds the buzzer."
          : "Arm it when you leave. Movement at the IR sensor will then sound the buzzer."}
      </p>
      <div className="button-row">
        <button type="button" className={config.armed ? "btn" : "btn btn-primary"} onClick={() => onArm(!config.armed)}>
          {config.armed ? "Disarm" : "Arm alarm"}
        </button>
        {config.alarm_active && (
          <button type="button" className="btn btn-danger" onClick={onSilence}>
            Silence buzzer
          </button>
        )}
      </div>
    </section>
  );
}

export function SettingsPanel({ config, onSave }) {
  return (
    <section className="panel" aria-labelledby="settings-h">
      <h2 id="settings-h">Rules</h2>
      <NumberSetting
        label="Fan starts at"
        unit="°C"
        value={config.temp_threshold}
        min={15}
        max={60}
        step={0.5}
        onSave={(v) => onSave({ temp_threshold: v })}
      />
      <NumberSetting
        label="Light stays on for"
        unit="seconds"
        value={config.light_timeout}
        min={3}
        max={600}
        step={1}
        onSave={(v) => onSave({ light_timeout: v })}
      />
    </section>
  );
}

export function SimPanel({ temp, onTemp, onMotion }) {
  const [value, setValue] = useState(Math.round(temp ?? 26));
  return (
    <section className="panel sim" aria-labelledby="sim-h">
      <h2 id="sim-h">Simulator</h2>
      <p className="hint">No Arduino is connected, so the readings are made up. Use these to try the rules.</p>
      <label className="field">
        <span>Room temperature</span>
        <span className="field-input">
          <input
            type="range"
            min="18"
            max="40"
            step="0.5"
            value={value}
            onChange={(e) => setValue(Number(e.target.value))}
            onMouseUp={() => onTemp(value)}
            onTouchEnd={() => onTemp(value)}
            onKeyUp={() => onTemp(value)}
          />
          <span className="unit">{value}°C</span>
        </span>
      </label>
      <button type="button" className="btn" onClick={onMotion}>
        Walk past the sensor
      </button>
    </section>
  );
}
