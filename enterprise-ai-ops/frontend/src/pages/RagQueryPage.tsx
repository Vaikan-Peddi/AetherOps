import { Send } from "lucide-react";
import React, { useState } from "react";
import { api } from "../api/client";
import { Panel } from "../components/Panel";

type Source = {
  filename: string;
  chunk_text: string;
  score: number;
};

export function RagQueryPage({ organizationId }: { organizationId: string }) {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const result = await api.ragQuery(organizationId, query);
      setAnswer(result.answer);
      setSources(result.sources);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
      <Panel title="Ask Documents">
        <form onSubmit={submit} className="grid gap-3">
          <textarea className="min-h-32 rounded-md border border-slate-300 p-3 text-sm" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="What should the operator know?" />
          <button disabled={loading} title="Run RAG query" className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-900 px-3 text-sm font-semibold text-white disabled:opacity-60">
            <Send size={16} />
            {loading ? "Querying..." : "Query"}
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      </Panel>
      <Panel title="Response">
        {answer ? <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">{answer}</p> : <p className="text-sm text-slate-500">Run a query to see the synthesized response.</p>}
        {sources.length ? (
          <div className="mt-5 grid gap-3">
            {sources.map((source, idx) => (
              <article key={`${source.filename}-${idx}`} className="rounded-lg border border-slate-200 p-3">
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-950">{source.filename}</p>
                  <p className="rounded-md bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-800">{source.score.toFixed(2)}</p>
                </div>
                <p className="line-clamp-4 text-sm leading-6 text-slate-600">{source.chunk_text}</p>
              </article>
            ))}
          </div>
        ) : null}
      </Panel>
    </div>
  );
}
