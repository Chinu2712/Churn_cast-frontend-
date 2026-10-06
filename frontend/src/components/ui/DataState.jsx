/** Shared loading / error placeholder so pages don't repeat this boilerplate. */
export default function DataState({ loading, error, children }) {
  if (error) return <p className="error-text">Could not load data: {error.message}</p>;
  if (loading) return <p className="loading-text">Loading…</p>;
  return children;
}
