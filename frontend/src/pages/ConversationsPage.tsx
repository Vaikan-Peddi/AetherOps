import { useEffect, useState } from "react";
import { api, type Conversation } from "../api/client";
import { Panel } from "../components/Panel";

export function ConversationsPage({ organizationId }: { organizationId: string }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  useEffect(() => {
    if (!organizationId) return;
    api.conversations(organizationId).then(setConversations);
  }, [organizationId]);

  return (
    <Panel title="Conversation Memory">
      <div className="grid gap-3">
        {conversations.map((conversation) => (
          <article key={conversation.id} className="rounded-lg border border-slate-200 p-4">
            <h3 className="font-semibold text-slate-950">{conversation.title}</h3>
            <p className="text-sm text-slate-500">{new Date(conversation.updated_at).toLocaleString()}</p>
          </article>
        ))}
        {!conversations.length ? <p className="text-sm text-slate-500">No conversations yet.</p> : null}
      </div>
    </Panel>
  );
}
