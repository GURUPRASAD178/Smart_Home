function clock(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function EventLog({ events }) {
  if (!events.length) {
    return <p className="empty">Nothing has happened yet. Walk past the sensor or raise the temperature.</p>;
  }
  return (
    <ul className="events">
      {events.map((e) => (
        <li key={e.id} className={e.kind === "alert" ? "is-alert" : ""}>
          <time dateTime={e.at}>{clock(e.at)}</time>
          <span>{e.message}</span>
        </li>
      ))}
    </ul>
  );
}
