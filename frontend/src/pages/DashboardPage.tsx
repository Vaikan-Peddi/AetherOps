import { Plus } from "lucide-react";
import React, { useState } from "react";
import { api, type Organization } from "../api/client";
import { Panel } from "../components/Panel";

type Props = {
  organizations: Organization[];
  onOrganizationsChanged: (organizations: Organization[], selectedId?: string) => void;
};

export function DashboardPage({ organizations, onOrganizationsChanged }: Props) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  async function createOrg(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setError("");
    try {
      const organization = await api.createOrganization(name);
      onOrganizationsChanged([...organizations, organization], organization.id);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create organization");
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
      <Panel title="Operations Home">
        <div className="grid gap-3 sm:grid-cols-3">
          <Metric label="Organizations" value={organizations.length} accent="bg-emerald-100 text-emerald-800" />
          <Metric label="Auth" value="JWT" accent="bg-sky-100 text-sky-800" />
          <Metric label="Vector DB" value="Qdrant" accent="bg-amber-100 text-amber-800" />
        </div>
      </Panel>
      <Panel title="Create Organization">
        <form onSubmit={createOrg} className="flex gap-2">
          <input className="h-10 min-w-0 flex-1 rounded-md border border-slate-300 px-3 text-sm" value={name} onChange={(event) => setName(event.target.value)} placeholder="Organization name" />
          <button title="Create organization" className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-900 px-3 text-sm font-semibold text-white">
            <Plus size={16} />
            Create
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      </Panel>
    </div>
  );
}

function Metric({ label, value, accent }: { label: string; value: string | number; accent: string }) {
  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-3 inline-flex rounded-md px-2.5 py-1 text-xl font-semibold ${accent}`}>{value}</p>
    </div>
  );
}
