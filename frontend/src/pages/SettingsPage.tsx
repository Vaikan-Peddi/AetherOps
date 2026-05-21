import { Panel } from "../components/Panel";

export function SettingsPage() {
  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <Panel title="Model Routing">
        <div className="grid gap-2 text-sm text-slate-700">
          <p>CHAT {"->"} llama3.1:8b</p>
          <p>RAG {"->"} llama3.1:8b</p>
          <p>CODING {"->"} qwen2.5-coder:7b</p>
          <p>REASONING {"->"} deepseek-r1:8b</p>
          <p>SUMMARIZATION {"->"} llama3.1:8b</p>
        </div>
      </Panel>
      <Panel title="Connectors">
        <div className="grid gap-2 text-sm text-slate-700">
          <p>Gmail connector scaffold: OAuth-ready</p>
          <p>Slack connector scaffold: OAuth-ready</p>
          <p>GitHub connector scaffold: OAuth-ready</p>
        </div>
      </Panel>
    </div>
  );
}
