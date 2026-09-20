import {
  Activity,
  ArrowUpRight,
  ChevronRight,
  CircleHelp,
  Layers3,
  LayoutDashboard,
  ShieldCheck,
  SlidersHorizontal,
  TriangleAlert,
} from "lucide-react";
import { useWorkspace } from "../../state/WorkspaceContext";
export function Sidebar() {
  const { view, setView, activeIssues } = useWorkspace();
  return (
    <aside className="sidebar">
      <a className="brand" href="#" onClick={() => setView("overview")}>
        <span className="brand-icon">
          <Layers3 size={23} />
        </span>
        alto<span className="brand-period">.</span>
      </a>
      <div className="workspace">
        <span className="workspace-icon">A</span>
        <div>
          AltoTech Global<small>Building operations</small>
        </div>
        <ChevronRight size={15} />
      </div>
      <div className="nav-label">WORKSPACE</div>
      <nav>
        {(
          [
            {
              key: "overview",
              title: "Portfolio overview",
              icon: LayoutDashboard,
            },
            {
              key: "issues",
              title: "Issue investigation",
              icon: TriangleAlert,
            },
            { key: "rules", title: "Rule library", icon: SlidersHorizontal },
            { key: "pipeline", title: "Pipeline health", icon: Activity },
          ] as const
        ).map((n) => (
          <button
            key={n.key}
            className={view === n.key ? "nav-item selected" : "nav-item"}
            onClick={() => setView(n.key)}
          >
            <n.icon size={18} />
            {n.title}
            {n.key === "issues" && activeIssues.length > 0 && (
              <span className="nav-count">{activeIssues.length}</span>
            )}
          </button>
        ))}
      </nav>
      <div className="sidebar-note">
        <ShieldCheck size={21} />
        <strong>Intelligence, with oversight.</strong>
        <p>Every rule is reviewed by you. Every issue has evidence.</p>
      </div>
      <a
        className="help-link"
        href="http://localhost:8000/docs"
        target="_blank"
        rel="noreferrer"
      >
        <CircleHelp size={17} /> API documentation <ArrowUpRight size={14} />
      </a>
      <div className="profile">
        <span>PE</span>
        <div>
          Property engineer<small>Local assessment workspace</small>
        </div>
      </div>
    </aside>
  );
}
