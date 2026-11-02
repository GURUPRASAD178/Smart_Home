async function request(path, options) {
  const res = await fetch(`/api${path}`, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

const post = (path, body) =>
  request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const api = {
  status: () => request("/status/"),
  readings: (limit = 60) => request(`/readings/?limit=${limit}`),
  events: (limit = 12) => request(`/events/?limit=${limit}`),
  setDevice: (name, on) => post(`/devices/${name}/`, { on }),
  setAuto: (name) => post(`/devices/${name}/`, { auto: true }),
  setConfig: (values) => post("/config/", values),
  setArmed: (armed) => post("/alarm/", { armed }),
  silence: () => post("/alarm/", { silence: true }),
  sim: (values) => post("/sim/", values),
};
