import React, { useState } from 'react';
import { api } from '../services/api';
import { IconShield } from './Icons';

interface Props {
  onAuthenticated: (token: string) => void;
}

export const AdminLoginPage: React.FC<Props> = ({ onAuthenticated }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await api.loginAdmin(username, password);
      onAuthenticated(result.token);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : 'Admin sign-in failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="admin-login-shell">
      <section className="card admin-login-card">
        <div className="admin-login-brand">
          <span className="admin-login-icon"><IconShield size={22} /></span>
          <div>
            <h1>SecureSessionGuard</h1>
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <label className="form-group">
            <span>Username</span>
            <input
              className="form-input"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label className="form-group">
            <span>Password</span>
            <input
              className="form-input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>
          {error && <p role="alert" className="admin-login-error">{error}</p>}
          <button className="btn btn-primary admin-login-submit" type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <p className="admin-login-demo">Controlled demo credentials: admin / admin</p>
      </section>
    </main>
  );
};
