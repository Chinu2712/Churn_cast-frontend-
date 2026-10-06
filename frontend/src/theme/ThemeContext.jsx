import { createContext, useContext, useEffect, useState } from "react";

/*
  ThemeContext — the entire dark/light toggle mechanism in one small file.

  How it works:
  1. useState starts from whatever was saved in localStorage last time (or
     "light" the very first visit).
  2. useEffect writes the current theme onto <html data-theme="..."> every
     time it changes. index.css has rules keyed off that attribute, so this
     single line is what actually repaints every card, chart, and text color.
  3. We also persist the choice to localStorage so the preference survives a
     page refresh or closing the tab — "Dark/Light mode ... persists across
     pages" from the requirements is satisfied just by this hook living above
     the router in main.jsx.
*/

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => localStorage.getItem("churncast-theme") || "light");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("churncast-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === "light" ? "dark" : "light"));

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used inside a ThemeProvider");
  return ctx;
}
