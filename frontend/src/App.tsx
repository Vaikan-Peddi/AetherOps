import { useEffect, useState } from "react";
import { api, type Organization, type User } from "./api/client";
import { Shell, type View } from "./components/Shell";
import { DashboardPage } from "./pages/DashboardPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { LoginPage } from "./pages/LoginPage";
import { ObservabilityPage } from "./pages/ObservabilityPage";
import { RagQueryPage } from "./pages/RagQueryPage";
import { RegisterPage } from "./pages/RegisterPage";
import { WorkflowsPage } from "./pages/WorkflowsPage";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [view, setView] = useState<View>("dashboard");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [booting, setBooting] = useState(true);

  async function loadOrganizations(selectedId?: string) {
    const orgs = await api.organizations();
    setOrganizations(orgs);
    setOrganizationId(selectedId || orgs[0]?.id || "");
  }

  async function onAuthenticated(nextUser: User, selectedOrgId?: string) {
    setUser(nextUser);
    await loadOrganizations(selectedOrgId);
  }

  useEffect(() => {
    async function boot() {
      if (!api.token) {
        setBooting(false);
        return;
      }
      try {
        const currentUser = await api.me();
        setUser(currentUser);
        await loadOrganizations();
      } catch {
        api.setToken(null);
      } finally {
        setBooting(false);
      }
    }
    boot();
  }, []);

  if (booting) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-slate-600">Loading platform...</div>;
  }

  if (!user) {
    return authMode === "login" ? (
      <LoginPage onAuthenticated={onAuthenticated} onRegisterClick={() => setAuthMode("register")} />
    ) : (
      <RegisterPage onAuthenticated={onAuthenticated} onLoginClick={() => setAuthMode("login")} />
    );
  }

  function logout() {
    api.setToken(null);
    setUser(null);
    setOrganizations([]);
    setOrganizationId("");
  }

  function renderView() {
    if (!organizationId && view !== "dashboard") {
      return <DashboardPage organizations={organizations} onOrganizationsChanged={(orgs, selectedId) => { setOrganizations(orgs); if (selectedId) setOrganizationId(selectedId); }} />;
    }
    if (view === "documents") return <DocumentsPage organizationId={organizationId} />;
    if (view === "rag") return <RagQueryPage organizationId={organizationId} />;
    if (view === "workflows") return <WorkflowsPage organizationId={organizationId} />;
    if (view === "observability") return <ObservabilityPage organizationId={organizationId} />;
    return (
      <DashboardPage
        organizations={organizations}
        onOrganizationsChanged={(orgs, selectedId) => {
          setOrganizations(orgs);
          if (selectedId) setOrganizationId(selectedId);
        }}
      />
    );
  }

  return (
    <Shell
      user={user}
      organizations={organizations}
      organizationId={organizationId}
      view={view}
      onViewChange={setView}
      onOrganizationChange={setOrganizationId}
      onLogout={logout}
    >
      {renderView()}
    </Shell>
  );
}
