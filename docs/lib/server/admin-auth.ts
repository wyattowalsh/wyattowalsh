import 'server-only';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import {
  isAdminPasswordVerifier,
  verifyAdminPassword,
} from '@/lib/server/admin-password';
import {
  getAdminReadiness,
  getDocsServerConfig,
  hasAdminCredentials,
} from '@/lib/server/config';
import {
  ADMIN_SESSION_COOKIE,
  ADMIN_SESSION_MAX_LIFETIME_MS,
  buildAdminSessionCookieOptions,
  createAdminSessionToken,
  verifyAdminSessionToken,
} from '@/lib/server/session';

export type AdminAuthenticationResult =
  | { ok: true }
  | {
      ok: false;
      reason:
        | 'invalid'
        | 'credentials_missing'
        | 'distributed_limiter_missing'
        | 'redis_configuration_invalid';
    };

export async function authenticateAdminPassword(
  password: string,
): Promise<AdminAuthenticationResult> {
  const config = getDocsServerConfig();
  const readiness = getAdminReadiness(config);
  if (!readiness.available) {
    return { ok: false, reason: readiness.reason };
  }

  // DOCS_ADMIN_PASSWORD holds a scrypt verifier (see admin-password.ts), not plaintext.
  if (!isAdminPasswordVerifier(config.adminPassword)) {
    return { ok: false, reason: 'credentials_missing' };
  }

  const ok = await verifyAdminPassword(password, config.adminPassword);
  return ok ? { ok: true } : { ok: false, reason: 'invalid' };
}

export async function getValidatedAdminSession() {
  const config = getDocsServerConfig();
  if (!hasAdminCredentials(config) || !getAdminReadiness(config).available) {
    return null;
  }

  const cookieStore = await cookies();
  const token = cookieStore.get(ADMIN_SESSION_COOKIE)?.value;
  if (!token) {
    return null;
  }

  return verifyAdminSessionToken(token, config.sessionSecret);
}

export async function requireAdminSession() {
  const session = await getValidatedAdminSession();
  if (!session) {
    redirect('/admin/login');
  }

  return session;
}

export async function createAdminSessionCookie() {
  const config = getDocsServerConfig();
  if (!getAdminReadiness(config).available) {
    throw new Error('Admin login is unavailable.');
  }
  const { token, expiresAt } = await createAdminSessionToken(
    config.sessionSecret,
    ADMIN_SESSION_MAX_LIFETIME_MS,
  );

  return {
    name: ADMIN_SESSION_COOKIE,
    value: token,
    options: buildAdminSessionCookieOptions(config.isProduction, expiresAt),
  };
}

export function createClearedAdminSessionCookie() {
  const config = getDocsServerConfig();
  return {
    name: ADMIN_SESSION_COOKIE,
    value: '',
    options: {
      ...buildAdminSessionCookieOptions(config.isProduction, 0),
      maxAge: 0,
    },
  };
}
