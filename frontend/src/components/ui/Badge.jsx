import { riskBucketClass } from "../../utils/format";

/** Small colored pill used for risk buckets (High / Medium / Low) and flags. */
export default function Badge({ children }) {
  return <span className={`badge ${riskBucketClass(children)}`}>{children}</span>;
}
