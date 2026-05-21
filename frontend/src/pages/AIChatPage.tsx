import { Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { api, type Conversation, type ConversationMessage } from "../api/client";
import { Panel } from "../components/Panel";

type LocalMessage = Pick<ConversationMessage, "role" | "content" | "provider" | "model">;

export function AIChatPage({ organizationId }: { organizationId: string }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState("");
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  async function loadConversations() {
    const next = await api.conversations(organizationId);
    setConversations(next);
    if (!conversationId && next[0]) setConversationId(next[0].id);
  }

  useEffect(() => {
    if (!organizationId) return;
    loadConversations();
  }, [organizationId]);

  useEffect(() => {
    if (!organizationId || !conversationId) return;
    api.messages(organizationId, conversationId).then(setMessages).catch(() => setMessages([]));
  }, [organizationId, conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function newConversation() {
    const conversation = await api.createConversation(organizationId, "New chat");
    setConversations((current) => [conversation, ...current]);
    setConversationId(conversation.id);
    setMessages([]);
  }

  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (!input.trim() || streaming) return;
    const userText = input;
    setInput("");
    setStreaming(true);
    setMessages((current) => [...current, { role: "USER", content: userText }, { role: "ASSISTANT", content: "" }]);
    let activeConversationId = conversationId;
    try {
      await api.streamChat(
        {
          organization_id: organizationId,
          conversation_id: activeConversationId || undefined,
          message: userText,
          task_type: "CHAT"
        },
        (eventData) => {
          if (eventData.type === "meta" && eventData.conversation_id) {
            activeConversationId = eventData.conversation_id;
            setConversationId(eventData.conversation_id);
          }
          if (eventData.type === "token" && eventData.token) {
            setMessages((current) => {
              const next = [...current];
              const last = next[next.length - 1];
              next[next.length - 1] = { ...last, content: last.content + eventData.token, provider: eventData.provider, model: eventData.model };
              return next;
            });
          }
        }
      );
      await loadConversations();
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[280px_1fr]">
      <Panel title="Conversations">
        <button onClick={newConversation} className="mb-3 h-10 w-full rounded-md bg-slate-900 px-3 text-sm font-semibold text-white">
          New Chat
        </button>
        <div className="grid gap-2">
          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => setConversationId(conversation.id)}
              className={`rounded-md px-3 py-2 text-left text-sm ${conversation.id === conversationId ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              {conversation.title}
            </button>
          ))}
        </div>
      </Panel>

      <Panel title="AI Chat">
        <div className="mb-4 h-[56vh] overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="grid gap-4">
            {messages.map((message, index) => (
              <div key={index} className={`max-w-3xl rounded-lg p-3 text-sm leading-6 ${message.role === "USER" ? "ml-auto bg-slate-900 text-white" : "bg-white text-slate-800 shadow-sm"}`}>
                <ReactMarkdown>{message.content || (streaming && index === messages.length - 1 ? "..." : "")}</ReactMarkdown>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        </div>
        <form onSubmit={send} className="flex gap-2">
          <input
            className="h-11 min-w-0 flex-1 rounded-md border border-slate-300 px-3 text-sm"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask AetherOps..."
          />
          <button disabled={streaming} className="inline-flex h-11 items-center gap-2 rounded-md bg-slate-900 px-4 text-sm font-semibold text-white disabled:opacity-60">
            <Send size={16} />
            Send
          </button>
        </form>
      </Panel>
    </div>
  );
}
