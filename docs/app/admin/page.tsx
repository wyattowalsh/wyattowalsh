import Link from 'next/link';
import { unstable_noStore as noStore } from 'next/cache';
import { requireAdminSession } from '@/lib/server/admin-auth';
import { getTelemetryDashboardSnapshot } from '@/lib/server/telemetry-store';

type AdminPageProps = {
  searchParams: Promise<{
    window?: string;
  }>;
};

const WINDOW_OPTIONS = [1, 7, 30] as const;

function formatEventDetail(value?: string | number) {
  if (value === undefined || value === '') {
    return '—';
  }

  return typeof value === 'number' ? value.toLocaleString() : value;
}

export default async function AdminPage({ searchParams }: AdminPageProps) {
  noStore();
  await requireAdminSession();

  const params = await searchParams;
  const selectedWindow = Number.parseInt(params.window ?? '7', 10);
  const windowDays = WINDOW_OPTIONS.includes(selectedWindow as 1 | 7 | 30)
    ? selectedWindow
    : 7;
  const snapshot = await getTelemetryDashboardSnapshot(windowDays);

  return (
    <main className="admin-dashboard">
      <section className="admin-hero">
        <div>
          <div className="admin-eyebrow">Protected</div>
          <h1 className="admin-title">Telemetry explorer</h1>
          <p className="admin-copy admin-copy-wide">
            Explore the docs app telemetry in one place: traffic, searches,
            clicks, referrers, and recent events collected from the site.
          </p>
        </div>
        <div className="admin-toolbar">
          {WINDOW_OPTIONS.map((option) => (
            <Link
              key={option}
              href={`/admin?window=${option}`}
              className={option === windowDays ? 'admin-pill admin-pill-active' : 'admin-pill'}
            >
              {option === 1 ? '24h' : `${option}d`}
            </Link>
          ))}
          <form action="/api/admin/logout" method="post">
            <button type="submit" className="admin-ghost-button">
              Sign out
            </button>
          </form>
        </div>
      </section>

      <section className="admin-summary-grid">
        <article className="admin-metric-card">
          <span className="admin-metric-label">Page views</span>
          <strong>{snapshot.summary.pageViews.toLocaleString()}</strong>
          <span>{snapshot.summary.uniqueSessions.toLocaleString()} active sessions</span>
        </article>
        <article className="admin-metric-card">
          <span className="admin-metric-label">Searches</span>
          <strong>{snapshot.summary.searches.toLocaleString()}</strong>
          <span>Queries recorded from the docs search API</span>
        </article>
        <article className="admin-metric-card">
          <span className="admin-metric-label">CTA clicks</span>
          <strong>{snapshot.summary.ctaClicks.toLocaleString()}</strong>
          <span>{snapshot.summary.outboundClicks.toLocaleString()} outbound link clicks</span>
        </article>
        <article className="admin-metric-card">
          <span className="admin-metric-label">API health</span>
          <strong>{snapshot.summary.apiRequests.toLocaleString()}</strong>
          <span>
            {snapshot.summary.apiErrors.toLocaleString()} errors, avg latency{' '}
            {snapshot.summary.averageApiLatencyMs}ms
          </span>
        </article>
      </section>

      <section className="admin-grid-two-up">
        <article className="admin-panel">
          <div className="admin-panel-heading">
            <h2>Traffic timeline</h2>
            <span>{windowDays === 1 ? 'Past day' : `Past ${windowDays} days`}</span>
          </div>
          <div className="admin-timeline">
            {snapshot.timeline.length === 0 ? (
              <p className="admin-empty-state">No traffic has been recorded yet.</p>
            ) : (
              snapshot.timeline.map((point) => (
                <div key={point.label} className="admin-timeline-row">
                  <span>{point.label}</span>
                  <div>
                    <strong>{point.pageViews}</strong>
                    <span>views</span>
                  </div>
                  <div>
                    <strong>{point.searches}</strong>
                    <span>searches</span>
                  </div>
                  <div>
                    <strong>{point.ctaClicks}</strong>
                    <span>CTA</span>
                  </div>
                  <div>
                    <strong>{point.apiErrors}</strong>
                    <span>errors</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="admin-panel">
          <div className="admin-panel-heading">
            <h2>Route health</h2>
            <span>API timings and failure counts</span>
          </div>
          <div className="admin-list">
            {snapshot.routeHealth.length === 0 ? (
              <p className="admin-empty-state">No API observations yet.</p>
            ) : (
              snapshot.routeHealth.map((route) => (
                <div key={route.route} className="admin-list-row">
                  <div>
                    <strong>{route.route}</strong>
                    <span>
                      {route.requests} requests, {route.errors} errors
                    </span>
                  </div>
                  <div className="admin-list-metrics">
                    <span>{route.averageLatencyMs}ms avg</span>
                    <span>{route.maxLatencyMs}ms max</span>
                    <span>{formatEventDetail(route.lastStatusCode)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>
      </section>

      <section className="admin-grid-three-up">
        <article className="admin-panel">
          <div className="admin-panel-heading">
            <h2>Top pages</h2>
            <span>Most viewed paths</span>
          </div>
          <div className="admin-list">
            {snapshot.topPages.length === 0 ? (
              <p className="admin-empty-state">No page views yet.</p>
            ) : (
              snapshot.topPages.map((page) => (
                <div key={page.pathname} className="admin-list-row">
                  <div>
                    <strong>{page.title ?? page.pathname}</strong>
                    <span>{page.pathname}</span>
                  </div>
                  <div className="admin-list-metrics">
                    <span>{page.views} views</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="admin-panel">
          <div className="admin-panel-heading">
            <h2>Top searches</h2>
            <span>Search intent from docs navigation</span>
          </div>
          <div className="admin-list">
            {snapshot.topSearches.length === 0 ? (
              <p className="admin-empty-state">No search queries yet.</p>
            ) : (
              snapshot.topSearches.map((search) => (
                <div key={search.query} className="admin-list-row">
                  <div>
                    <strong>{search.query}</strong>
                    <span>docs search term</span>
                  </div>
                  <div className="admin-list-metrics">
                    <span>{search.count}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="admin-panel">
          <div className="admin-panel-heading">
            <h2>CTA performance</h2>
            <span>Explicitly tagged calls to action</span>
          </div>
          <div className="admin-list">
            {snapshot.topCallsToAction.length === 0 ? (
              <p className="admin-empty-state">No CTA interactions yet.</p>
            ) : (
              snapshot.topCallsToAction.map((cta) => (
                <div key={cta.label} className="admin-list-row">
                  <div>
                    <strong>{cta.label}</strong>
                    <span>clicks recorded</span>
                  </div>
                  <div className="admin-list-metrics">
                    <span>{cta.count}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>
      </section>

      <section className="admin-grid-two-up">
        <article className="admin-panel">
          <div className="admin-panel-heading">
            <h2>Top referrers</h2>
            <span>External and internal entry points</span>
          </div>
          <div className="admin-list">
            {snapshot.topReferrers.length === 0 ? (
              <p className="admin-empty-state">No referrer data yet.</p>
            ) : (
              snapshot.topReferrers.map((referrer) => (
                <div key={referrer.referrer} className="admin-list-row">
                  <div>
                    <strong>{referrer.referrer}</strong>
                    <span>entry traffic source</span>
                  </div>
                  <div className="admin-list-metrics">
                    <span>{referrer.visits}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="admin-panel">
          <div className="admin-panel-heading">
            <h2>Recent events</h2>
            <span>Latest sanitized telemetry records</span>
          </div>
          <div className="admin-event-log">
            {snapshot.recentEvents.length === 0 ? (
              <p className="admin-empty-state">No telemetry has been ingested yet.</p>
            ) : (
              snapshot.recentEvents.map((event) => (
                <div key={event.id} className="admin-event-row">
                  <div>
                    <strong>{event.name}</strong>
                    <span>{event.occurredAt}</span>
                  </div>
                  <div>
                    <span>{formatEventDetail(event.pathname ?? event.route ?? event.label)}</span>
                    <span>{formatEventDetail(event.statusCode ?? event.searchQuery)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>
      </section>

      <section className="admin-footer-note">
        <span>Store adapter: {snapshot.adapter}</span>
        <span>Retained events: {snapshot.totalRetainedEvents}</span>
        <span>Storage target: {snapshot.storageTarget}</span>
      </section>
    </main>
  );
}