import React, { useState } from "react";
import { api, type User } from "../api/client";
import { AuthFrame } from "./LoginPage";

type Props = {
  onAuthenticated: (user: User, organizationId?: string) => void;
  onLoginClick: () => void;
};

export function RegisterPage({ onAuthenticated, onLoginClick }: Props) {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await api.register({ email, password, full_name: fullName, organization_name: organizationName });
      api.setToken(result.access_token);
      onAuthenticated(result.user, result.organization_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthFrame title="Create workspace" actionLabel="Register" onSubmit={submit} loading={loading} error={error}>
      <input className="h-11 rounded-md border border-slate-300 px-3" placeholder="Full name" value={fullName} onChange={(event) => setFullName(event.target.value)} />
      <input className="h-11 rounded-md border border-slate-300 px-3" placeholder="Organization" value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} />
      <input className="h-11 rounded-md border border-slate-300 px-3" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} />
      <input className="h-11 rounded-md border border-slate-300 px-3" placeholder="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
      <button type="button" onClick={onLoginClick} className="text-sm font-medium text-emerald-700 hover:text-emerald-900">
        Already have an account
      </button>
    </AuthFrame>
  );
}
