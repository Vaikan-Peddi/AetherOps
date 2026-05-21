import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { api, type ConnectorInfo, type ProviderHealth } from "../api/client";
import { Panel } from "../components/Panel";

export function SettingsPage() {
  const [routes, setRoutes] = useState<Record<string, { provider: string; model: string }>>({});
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [connectors, setConnectors] = useState<ConnectorInfo[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    setMessage("");
    try {
      const [routeData, providerData, connectorData] = await Promise.all([
        api.aiRoutes(),
        api.providerHealth(),
        api.connectors()
      ]);
      setRoutes(routeData);
      setProviders(providerData.providers);
      setConnectors(connectorData.connectors);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not load settings");
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <Panel title="Model Routing">
        <button onClick={load} className="mb-4 inline-flex h-10 items-center gap-2 rounded-md border border-slate-300 px-3 text-sm font-medium hover:bg-slate-100">
          <RefreshCw size={16} />
          Refresh
        </button>
        {message ? <p className="mb-3 text-sm text-red-700">{message}</p> : null}
        <div className="grid gap-2">
          {Object.entries(routes).map(([task, route]) => (
            <div key={task} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm">
              <span className="font-semibold text-slate-950">{task}</span>
              <span className="text-slate-600">{route.provider} / {route.model}</span>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Provider Health">
        <div className="grid gap-3">
          {providers.map((provider) => (
            <article key={`${provider.provider}-${provider.model}`} className="rounded-lg border border-slate-200 p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-950">{provider.provider}</h3>
                <span className={`rounded-md px-2 py-1 text-xs font-semibold ${provider.ok ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"}`}>
                  {provider.ok ? "healthy" : "not ready"}
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{provider.model}</p>
              {provider.error ? <p className="mt-2 text-xs text-red-700">{provider.error}</p> : null}
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Connectors">
        <div className="grid gap-3">
          {connectors.map((connector) => (
            <article key={connector.name} className="rounded-lg border border-slate-200 p-4">
              <h3 className="font-semibold capitalize text-slate-950">{connector.name}</h3>
              <p className="mt-1 text-sm text-slate-600">{connector.oauth_scopes.join(", ") || "No scopes configured"}</p>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Operational Notes">
        <div className="grid gap-2 text-sm text-slate-700">
          <p>Ollama must be reachable from Docker at http://host.docker.internal:11434.</p>
          <p>Cloud providers are scaffolded and report unhealthy until API keys are configured.</p>
          <p>Connector OAuth flows are intentionally placeholders, but execution contracts are in place.</p>
        </div>
      </Panel>
    </div>
  );
}
