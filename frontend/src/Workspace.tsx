import { LoaderCircle, ShieldCheck, X } from "lucide-react";
import { useWorkspace } from "./state/WorkspaceContext";
import { Sidebar } from "./components/layout/Sidebar";
import { Topbar } from "./components/layout/Topbar";
import { PageHeading } from "./components/layout/PageHeading";
import { SourceNotice } from "./components/layout/SourceNotice";
import { ScopeFilters } from "./components/overview/ScopeFilters";
import { RuleAuthoringModal } from "./components/rules/RuleAuthoringModal";
import { PortfolioView } from "./components/overview/PortfolioView";
import { IssueInvestigation } from "./components/issues/IssueInvestigation";
import { RuleLibrary } from "./components/rules/RuleLibrary";
import { PipelineHealth } from "./components/pipeline/PipelineHealth";
export function Workspace() {
  const { view, loading, error, notice, setNotice, authorOpen, refresh } =
    useWorkspace();
  return (
    <div className="app-shell">
      <Sidebar />
      <main>
        <Topbar />
        <div className="page">
          <PageHeading />
          <SourceNotice />
          {error && (
            <div className="error" role="alert">
              {error} <button onClick={() => void refresh()}>Retry</button>
            </div>
          )}
          {notice && (
            <div className="notice" role="status">
              {notice}
              <button
                className="icon-button"
                onClick={() => setNotice("")}
                aria-label="Dismiss"
              >
                <X size={15} />
              </button>
            </div>
          )}
          {loading ? (
            <div className="empty">
              <LoaderCircle className="spin" />
              <p>Loading your workspace…</p>
            </div>
          ) : (
            <>
              {(view === "overview" || view === "issues") && <ScopeFilters />}
              {view === "overview" && <PortfolioView />}
              {view === "issues" && <IssueInvestigation />}
              {view === "rules" && <RuleLibrary />}
              {view === "pipeline" && <PipelineHealth />}
            </>
          )}
          <footer>
            <span>
              <ShieldCheck size={13} /> Explainable by design. Reviewed by
              people.
            </span>
            <span>ALTO / AFDD WORKSPACE</span>
          </footer>
        </div>
      </main>
      {authorOpen && <RuleAuthoringModal />}
    </div>
  );
}
