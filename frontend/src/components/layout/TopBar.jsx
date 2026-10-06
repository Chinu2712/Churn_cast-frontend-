import { useTheme } from "../../theme/ThemeContext";

/*
  TopBar — page title on the left, theme toggle on the right.
  Every page passes its own title in; the toggle button itself is shared.
*/
export default function TopBar({ title }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <div className="topbar">
      <h1>{title}</h1>
      <button
        type="button"
        className="theme-toggle"
        onClick={toggleTheme}
        aria-pressed={isDark}
        aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
      >
        <span aria-hidden="true">{isDark ? "\u263D" : "\u2600"}</span>
        <span>{isDark ? "Dark theme" : "Light theme"}</span>
      </button>
    </div>
  );
}
