import { useWorkspace } from "../../state/WorkspaceContext";
import { RuleList } from "./RuleList";
import { RuleDetail } from "./RuleDetail";
export function RuleLibrary() {
  useWorkspace();
  return (
    <div className="rule-layout">
      <RuleList />
      <RuleDetail />
    </div>
  );
}
