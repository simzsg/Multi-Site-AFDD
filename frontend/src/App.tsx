import { WorkspaceProvider } from "./state/WorkspaceContext";
import { Workspace } from "./Workspace";
export default function App() {
  return (
    <WorkspaceProvider>
      <Workspace />
    </WorkspaceProvider>
  );
}
