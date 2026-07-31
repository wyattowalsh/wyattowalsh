import 'server-only';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import {
  isAdminPasswordVerifier,
  verifyAdminPassword,
} from '@/lib/server/admin-password';
import { getDocsServerConfig, isAdminConfigured } from '@/lib/server/config';
import {
  ADMIN_SESSION_COOKIE,
  buildAdminSessionCookieOptions,
  createAdminSessionToken,
  verifyAdminSessionToken,
} from '@/lib/server/session';

const ADMIN_SESSION_LIFETIME_MS = 1000 * 60 * 60 * 12;

export async function authenticateAdminPassword(password: string): Promise<{
  ok: boolean;
  reason?: 'invalid' | 'misconfigured';
}> {
  const config = getDocsServerConfig();
  if (!isAdminConfigured(config)) {
    return { ok: false, reason: 'misconfigured' };
  }

  // DOCS_ADMIN_PASSWORD holds a scrypt verifier (see admin-password.ts), not plaintext.
  if (!isAdminPasswordVerifier(config.adminPassword)) {
    return { ok: false, reason: 'misconfigured' };
  }

  const ok = await verifyAdminPassword(password, config.adminPassword);
  return ok ? { ok: true } : { ok: false, reason: 'invalid' };
}

export async function getValidatedAdminSession() {
  const config = getDocsServerConfig();
  if (!isAdminConfigured(config)) {
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
  const { token, expiresAt } = await createAdminSessionToken(
    config.sessionSecret,
    ADMIN_SESSION_LIFETIME_MS,
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
