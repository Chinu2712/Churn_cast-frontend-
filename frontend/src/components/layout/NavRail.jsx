import { NavLink } from "react-router-dom";

/*
  NavRail — the left-hand navigation strip present on every page.

  Uses React Router's <NavLink>, which automatically adds an "active" CSS
  class to whichever link matches the current URL -- that's the only logic
  needed to highlight the current page.
*/
const NAV_ITEMS = [
  { to: "/", code: "OV", label: "Overview" },
  { to: "/explorer", code: "CR", label: "Customer Risk Explorer" },
  { to: "/diagnostics", code: "MD", label: "Model Diagnostics & Monitoring" },
];

export default function NavRail() {
  return (
    <nav className="nav-rail" aria-label="Primary">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === "/"}
          className={({ isActive }) => "nav-rail-item" + (isActive ? " active" : "")}
          title={item.label}
        >
          <span aria-hidden="true">{item.code}</span>
          <span className="sr-only">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
