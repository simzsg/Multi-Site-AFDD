import { RuleList } from "./RuleList";
import { RuleDetail } from "./RuleDetail";
export function RuleLibrary() {
  return (
    <div className="rule-layout">
      <RuleList />
      <RuleDetail />
    </div>
  );
}
