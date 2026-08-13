import { redirect } from 'next/navigation';
import { getValidatedAdminSession } from '@/lib/server/admin-auth';
import { parseAdminDestination } from '@/lib/server/admin-destination';
import { buildAdminLoginAction } from '@/lib/server/admin-login-handler';
import {
  getAdminReadiness,
  getDocsServerConfig,
  getTelemetryStorageDescription,
} from '@/lib/server/config';

type LoginPageProps = {
  searchParams: Promise<{
    error?: string;
    next?: string;
  }>;
};

const ERROR_COPY: Record<string, string> = {
  invalid_request: 'The login request was malformed. Try submitting the form again.',
  invalid: 'That password was rejected.',
  config: 'Admin access is not configured yet. Set the docs admin env vars first.',
  limiter:
    'Admin sign-in is unavailable because a production-safe distributed limiter is not configured.',
  rate: 'Too many sign-in attempts. Wait a minute before trying again.',
  server: 'The login request failed unexpectedly. Review the server logs.',
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
  const readiness = getAdminReadiness(config);
  const storage = getTelemetryStorageDescription(config);
  const errorCopy = params.error ? ERROR_COPY[params.error] : undefined;
  const nextPath = parseAdminDestination(params.next);
  const loginAction = buildAdminLoginAction(nextPath);
  const telemetryCopy =
    storage.availability === 'disabled'
      ? 'Telemetry collection is disabled for this deployment.'
      : storage.availability === 'unavailable'
        ? `Telemetry is unavailable: ${storage.target}.`
        : config.isProduction
          ? 'First-party telemetry is enabled for this deployment.'
          : `Development telemetry target: ${storage.target}.`;

  return (
    <main className="admin-login-page">
      <section className="admin-login-card">
        <div className="admin-eyebrow">Observability</div>
        <h1 className="admin-title">Telemetry explorer</h1>
        <p className="admin-copy">
          Sign in with the shared password to explore page traffic, searches,
          clicks, and recent first-party telemetry when collection is enabled.
        </p>

        {!readiness.available ? (
          <div className="admin-alert admin-alert-warning">
            {readiness.reason === 'credentials_missing' ? (
              <>
                <strong>Missing credentials.</strong>
                <span>
                  Set a scrypt verifier in <code>DOCS_ADMIN_PASSWORD</code> and a
                  long secret in <code>DOCS_ADMIN_SESSION_SECRET</code> before
                  using the admin panel.
                </span>
              </>
            ) : (
              <>
                <strong>Production sign-in is disabled.</strong>
                <span>
                  {readiness.reason === 'redis_configuration_invalid'
                    ? 'The Redis configuration is incomplete, and no approved distributed login limiter is available.'
                    : 'No approved distributed login limiter is configured. The development-only memory limiter never runs in production.'}
                </span>
              </>
            )}
          </div>
        ) : null}

        {errorCopy ? (
          <div className="admin-alert admin-alert-error">{errorCopy}</div>
        ) : null}

        <form className="admin-form" action={loginAction} method="post">
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
          <button
            type="submit"
            className="admin-button"
            disabled={!readiness.available}
          >
            Sign in
          </button>
        </form>

        <p className="admin-footnote">{telemetryCopy}</p>
      </section>
    </main>
  );
}
