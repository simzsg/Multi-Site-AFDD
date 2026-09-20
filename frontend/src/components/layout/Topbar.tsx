import { ChevronRight, RefreshCw } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
export function Topbar() {
  const { view, refresh, live } = useWorkspace();
  return (
    <header className="topbar">
      <div>
        Workspace <ChevronRight size={13} />{" "}
        <strong>
          {
            {
              overview: "Portfolio overview",
              issues: "Issue investigation",
              rules: "Rule library",
              pipeline: "Pipeline health",
            }[view]
          }
        </strong>
      </div>
      <div>
        <span className={`connection ${live ? "" : "offline"}`}>
          <span className="dot" />
          {live ? "Receiving telemetry" : "Telemetry idle"}
        </span>
        <button
          className="icon-button"
          onClick={() => void refresh()}
          aria-label="Refresh"
        >
          <RefreshCw size={16} />
        </button>
      </div>
    </header>
  );
}
