import { Upload } from "lucide-react";
import React, { useEffect, useState } from "react";
import { api, type DocumentRecord } from "../api/client";
import { Panel } from "../components/Panel";

export function DocumentsPage({ organizationId }: { organizationId: string }) {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function load() {
    if (!organizationId) return;
    setDocuments(await api.documents(organizationId));
  }

  useEffect(() => {
    load().catch((err) => setMessage(err instanceof Error ? err.message : "Could not load documents"));
  }, [organizationId]);

  async function upload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setLoading(true);
    setMessage("Extracting PDF text and writing embeddings to Qdrant...");
    try {
      await api.uploadDocument(organizationId, file);
      setFile(null);
      setMessage("Upload complete");
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
      <Panel title="Upload PDF">
        <form onSubmit={upload} className="grid gap-3">
          <input type="file" accept="application/pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="rounded-md border border-slate-300 p-2 text-sm" />
          <button disabled={!file || loading} title="Upload PDF" className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-900 px-3 text-sm font-semibold text-white disabled:opacity-60">
            <Upload size={16} />
            {loading ? "Uploading..." : "Upload"}
          </button>
        </form>
        {message ? <p className="mt-3 text-sm text-slate-600">{message}</p> : null}
      </Panel>
      <Panel title="Documents">
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="py-2 pr-4">Filename</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Pages</th>
                <th className="py-2 pr-4">Chunks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {documents.map((document) => (
                <tr key={document.id}>
                  <td className="py-3 pr-4 font-medium text-slate-950">{document.filename}</td>
                  <td className="py-3 pr-4">{document.status}</td>
                  <td className="py-3 pr-4">{document.page_count}</td>
                  <td className="py-3 pr-4">{document.chunk_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!documents.length ? <p className="py-4 text-sm text-slate-500">No documents uploaded yet.</p> : null}
        </div>
      </Panel>
    </div>
  );
}
