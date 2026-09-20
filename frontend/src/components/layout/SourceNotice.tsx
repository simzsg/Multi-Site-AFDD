import { GitBranch } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
export function SourceNotice() {
  const { entities } = useWorkspace();
  return (
    <div className="source-notice">
      <GitBranch size={14} />
      <strong>
        {entities.some((e) => e.data.source === "candidate-starter-pack")
          ? "Candidate starter pack · source replay"
          : "Synthetic demonstration inventory"}
      </strong>
      <span>
        {entities.some((e) => e.data.source === "candidate-starter-pack")
          ? "Recorded 15 Jan 2026 · original timestamps preserved"
          : "Engineering fixtures, separate from supplied data"}
      </span>
    </div>
  );
}
