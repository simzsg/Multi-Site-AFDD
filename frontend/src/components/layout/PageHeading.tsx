import { Sparkles } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
export function PageHeading() {
  const { view, setAuthorOpen, setAiResult } = useWorkspace();
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">BUILDING INTELLIGENCE</div>
        <h1>
          {
            {
              overview: "Your portfolio, in perspective.",
              issues: "Understand the issue.",
              rules: "Operational knowledge, formalized.",
              pipeline: "Follow the data.",
            }[view]
          }
        </h1>
        <p>
          {
            {
              overview:
                "A clear view of equipment health, from portfolio to room.",
              issues:
                "Trace the signal. Review the evidence. Find the affected spaces.",
              rules:
                "Reusable monitoring rules with clear scope and human control.",
              pipeline:
                "Ingestion, evaluation, and an auditable trail of every decision.",
            }[view]
          }
        </p>
      </div>
      <button
        className="primary"
        onClick={() => {
          setAuthorOpen(true);
          setAiResult(null);
        }}
      >
        <Sparkles size={17} /> Create a rule
      </button>
    </div>
  );
}
