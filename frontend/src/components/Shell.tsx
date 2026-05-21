import { BarChart3, FileText, LayoutDashboard, LogOut, Network, Search, type LucideIcon } from "lucide-react";
import type React from "react";
import type { Organization, User } from "../api/client";

export type View = "dashboard" | "documents" | "rag" | "workflows" | "observability";

const navItems: Array<{ id: View; label: string; icon: LucideIcon }> = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "rag", label: "RAG Query", icon: Search },
  { id: "workflows", label: "Workflows", icon: Network },
  { id: "observability", label: "Observability", icon: BarChart3 }
];

type Props = {
  user: User;
  organizations: Organization[];
  organizationId: string;
  view: View;
  onViewChange: (view: View) => void;
  onOrganizationChange: (id: string) => void;
  onLogout: () => void;
  children: React.ReactNode;
};

export function Shell({
  user,
  organizations,
  organizationId,
  view,
  onViewChange,
  onOrganizationChange,
  onLogout,
  children
}: Props) {
  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-20 items-center border-b border-slate-200 px-6">
          <img src="/logo.svg" alt="AetherOps" className="h-12 w-auto" />
        </div>
        <nav className="space-y-1 p-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = view === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                title={item.label}
                className={`flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm font-medium ${
                  active ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                }`}
              >
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="lg:pl-72">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="flex min-h-20 flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
            <div>
              <p className="text-sm text-slate-500">Signed in as {user.email}</p>
              <h2 className="text-2xl font-semibold text-slate-950">{navItems.find((item) => item.id === view)?.label}</h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={organizationId}
                onChange={(event) => onOrganizationChange(event.target.value)}
                className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm"
              >
                {organizations.map((organization) => (
                  <option key={organization.id} value={organization.id}>
                    {organization.name}
                  </option>
                ))}
              </select>
              <button
                onClick={onLogout}
                title="Log out"
                className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                <LogOut size={16} />
                Log out
              </button>
            </div>
          </div>
          <div className="flex gap-1 overflow-x-auto px-4 pb-3 lg:hidden">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`shrink-0 rounded-md px-3 py-2 text-sm font-medium ${
                  view === item.id ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </header>
        <section className="px-4 py-6 sm:px-6 lg:px-8">{children}</section>
      </main>
    </div>
  );
}
