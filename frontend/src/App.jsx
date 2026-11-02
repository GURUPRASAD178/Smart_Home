import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import TempChart from "./components/TempChart.jsx";
import DeviceRow from "./components/DeviceRow.jsx";
import EventLog from "./components/EventLog.jsx";
import { AlarmPanel, SettingsPanel, SimPanel } from "./components/Controls.jsx";

const POLL_MS = 1500;

export default function App() {
  const [status, setStatus] = useState(null);
  const [readings, setReadings] = useState([]);
  const [events, setEvents] = useState([]);
  const [offline, setOffline] = useState(false);
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [s, r, e] = await Promise.all([api.status(), api.readings(60), api.events(12)]);
      setStatus(s);
      setReadings(r.readings);
      setEvents(e.events);
      setOffline(false);
    } catch {
      setOffline(true);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  // Run an API call, show its error if it fails, then refresh straight away.
  const act = async (call) => {
    try {
      await call();
      setNotice("");
    } catch (err) {
      setNotice(err.message);
    }
    refresh();
  };

  if (!status) {
    return (
      <main className="shell">
        <div className="splash">
          <h1>Smart home</h1>
          {offline ? (
            <p>
              Can't reach the backend. Start it from the <code>backend</code> folder with{" "}
              <code>python manage.py runserver</code>, then reload this page.
            </p>
          ) : (
            <p>Connecting…</p>
          )}
        </div>
      </main>
    );
  }

  const { reading, devices, config, mode, online } = status;
  const temp = reading?.temp;
  const hot = temp !== undefined && temp >= config.temp_threshold;
  const isSim = mode === "sim";

  return (
    <main className="shell">
      <header className="top">
        <h1>Smart home</h1>
        <p className={`pill ${online && !offline ? "pill-ok" : "pill-bad"}`}>
          <span className="dot" aria-hidden="true" />
          {offline
            ? "Backend not responding"
            : !online
            ? "No readings from the Arduino"
            : isSim
            ? "Live, simulated sensors"
            : "Live, Arduino connected"}
        </p>
      </header>

      {config.alarm_active && (
        <div className="banner banner-alert" role="alert">
          Alarm triggered: movement was detected while the alarm was armed.
        </div>
      )}
      {!online && !offline && !isSim && (
        <div className="banner" role="status">
          The backend hasn't heard from the Arduino for a few seconds. Check the USB cable and the
          SERIAL_PORT setting.
        </div>
      )}
      {notice && (
        <div className="banner" role="status">
          {notice}
        </div>
      )}

      <div className="layout">
        <div className="col">
          <section className="panel hero" aria-labelledby="temp-h">
            <h2 id="temp-h">Room temperature</h2>
            <p className={`temp ${hot ? "is-hot" : ""}`} aria-live="polite">
              {temp !== undefined ? temp.toFixed(1) : "–"}
              <span className="temp-unit">°C</span>
            </p>
            <p className="motion">
              <span className={`dot ${reading?.motion ? "dot-motion" : ""}`} aria-hidden="true" />
              {reading?.motion ? "Movement at the sensor" : "No movement"}
            </p>
            <TempChart readings={readings} threshold={config.temp_threshold} />
            <p className="hint">Last minute. Ticks under the line mark movement.</p>
          </section>

          <section className="panel" aria-labelledby="events-h">
            <h2 id="events-h">Activity</h2>
            <EventLog events={events} />
          </section>
        </div>

        <div className="col">
          <section className="panel" aria-labelledby="devices-h">
            <h2 id="devices-h">Devices</h2>
            <ul className="devices">
              <DeviceRow
                label="Light"
                hint={`Turns on when the IR sensor sees movement and off after ${config.light_timeout} seconds.`}
                device={devices.light}
                onToggle={(on) => act(() => api.setDevice("light", on))}
                onAuto={() => act(() => api.setAuto("light"))}
              />
              <DeviceRow
                label="Fan"
                hint={`Runs at ${config.temp_threshold}°C or hotter and stops 1°C below that.`}
                device={devices.fan}
                onToggle={(on) => act(() => api.setDevice("fan", on))}
                onAuto={() => act(() => api.setAuto("fan"))}
              />
              <DeviceRow
                label="Buzzer"
                hint="Sounds when the alarm is triggered."
                device={devices.buzzer}
                onToggle={(on) => act(() => api.setDevice("buzzer", on))}
                onAuto={() => act(() => api.setAuto("buzzer"))}
              />
            </ul>
          </section>

          <AlarmPanel
            config={config}
            onArm={(armed) => act(() => api.setArmed(armed))}
            onSilence={() => act(() => api.silence())}
          />
          <SettingsPanel config={config} onSave={(values) => act(() => api.setConfig(values))} />
          {isSim && (
            <SimPanel
              temp={temp}
              onTemp={(t) => act(() => api.sim({ temp: t }))}
              onMotion={() => act(() => api.sim({ motion: true }))}
            />
          )}
        </div>
      </div>
    </main>
  );
}
