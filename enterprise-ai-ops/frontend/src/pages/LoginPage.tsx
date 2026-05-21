import React, { useState } from "react";
import { api, type User } from "../api/client";

type Props = {
  onAuthenticated: (user: User, organizationId?: string) => void;
  onRegisterClick: () => void;
};

export function LoginPage({ onAuthenticated, onRegisterClick }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await api.login({ email, password });
      api.setToken(result.access_token);
      onAuthenticated(result.user, result.organization_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthFrame title="Welcome back" actionLabel="Sign in" onSubmit={submit} loading={loading} error={error}>
      <input className="h-11 rounded-md border border-slate-300 px-3" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} />
      <input className="h-11 rounded-md border border-slate-300 px-3" placeholder="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
      <button type="button" onClick={onRegisterClick} className="text-sm font-medium text-emerald-700 hover:text-emerald-900">
        Create an account
      </button>
    </AuthFrame>
  );
}

export function AuthFrame({
  title,
  actionLabel,
  children,
  onSubmit,
  loading,
  error
}: {
  title: string;
  actionLabel: string;
  children: React.ReactNode;
  onSubmit: (event: React.FormEvent) => void;
  loading: boolean;
  error: string;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <img src="/logo.svg" alt="AetherOps" className="h-14 w-auto" />
        <h1 className="mt-2 text-2xl font-semibold text-slate-950">{title}</h1>
        <div className="mt-6 grid gap-3">{children}</div>
        {error ? <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        <button disabled={loading} className="mt-5 h-11 w-full rounded-md bg-slate-900 px-4 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60">
          {loading ? "Working..." : actionLabel}
        </button>
      </form>
    </main>
  );
}
