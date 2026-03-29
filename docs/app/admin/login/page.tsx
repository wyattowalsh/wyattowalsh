import { redirect } from 'next/navigation';
import { getValidatedAdminSession } from '@/lib/server/admin-auth';
import {
  getDocsServerConfig,
  getTelemetryStorageDescription,
  isAdminConfigured,
} from '@/lib/server/config';

type LoginPageProps = {
  searchParams: Promise<{
    error?: string;
    next?: string;
  }>;
};

const ERROR_COPY: Record<string, string> = {
  invalid: 'That password was rejected.',
  config: 'Admin access is not configured yet. Set the docs admin env vars first.',
  server: 'The login request failed unexpectedly. Check the admin telemetry log.',
};

export default async function AdminLoginPage({ searchParams }: LoginPageProps) {
  const [session, params] = await Promise.all([
    getValidatedAdminSession(),
    searchParams,
  ]);

  if (session) {
    redirect('/admin');
  }

  const config = getDocsServerConfig();
  const isConfigured = isAdminConfigured(config);
  const storage = getTelemetryStorageDescription(config);
  const errorCopy = params.error ? ERROR_COPY[params.error] : undefined;
  const nextPath = params.next?.startsWith('/') && !params.next.startsWith('//') ? params.next : '/admin';

  return (
    <main className="admin-login-page">
      <section className="admin-login-card">
        <div className="admin-eyebrow">Observability</div>
        <h1 className="admin-title">Telemetry explorer</h1>
        <p className="admin-copy">
          Sign in with the shared password to explore page traffic, searches,
          clicks, and recent telemetry from the docs app.
        </p>

        {!isConfigured ? (
          <div className="admin-alert admin-alert-warning">
            <strong>Missing configuration.</strong>
            <span>
              Set <code>DOCS_ADMIN_PASSWORD</code> and <code>DOCS_ADMIN_SESSION_SECRET</code>
              before using the admin panel.
            </span>
          </div>
        ) : null}

        {errorCopy ? (
          <div className="admin-alert admin-alert-error">{errorCopy}</div>
        ) : null}

        <form className="admin-form" action="/api/admin/login" method="post">
          <input type="hidden" name="next" value={nextPath} />
          <label className="admin-field">
            <span>Password</span>
            <input
              type="password"
              name="password"
              placeholder="Enter the shared admin password"
              autoComplete="current-password"
              required
            />
          </label>
          <button type="submit" className="admin-button" disabled={!isConfigured}>
            Sign in
          </button>
        </form>

        <p className="admin-footnote">
          Telemetry stays first-party in a local store. Current target:{' '}
          <code>{storage.target}</code>.
        </p>
      </section>
    </main>
  );
}