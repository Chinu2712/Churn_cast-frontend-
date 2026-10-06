import NavRail from "./NavRail";

/*
  PageLayout — wraps every route: nav rail on the left, scrollable content
  area on the right. Pages only need to provide their own inner content.
*/
export default function PageLayout({ children }) {
  return (
    <div className="app-shell">
      <NavRail />
      <main className="main">{children}</main>
    </div>
  );
}
