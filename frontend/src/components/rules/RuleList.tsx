import { GitBranch } from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
import { Badge, Empty } from "../ui/common";
export function RuleList() {
  const { rules, rule, openRule } = useWorkspace();
  return (
    <section className="panel rule-list">
      <div className="panel-heading">
        <h2>
          Rule versions <span className="muted">{rules.length}</span>
        </h2>
      </div>
      {!rules.length ? (
        <Empty title="Your rule library is empty">
          Create a rule from a natural-language request.
        </Empty>
      ) : (
        rules.map((r) => (
          <button
            key={r.id}
            className={rule?.id === r.id ? "selected-rule" : ""}
            onClick={() => openRule(r)}
          >
            <div>
              <GitBranch size={18} />
              <Badge tone={r.status === "ACTIVE" ? "green" : ""}>
                {r.status}
              </Badge>
            </div>
            <h3>{r.config.name}</h3>
            <p>
              Version {r.version} · {r.config.logic.threshold}°C /{" "}
              {r.config.logic.duration_minutes} min
            </p>
          </button>
        ))
      )}
    </section>
  );
}
