import 'server-only';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { getDocsServerConfig, isAdminConfigured } from '@/lib/server/config';
import {
  ADMIN_SESSION_COOKIE,
  buildAdminSessionCookieOptions,
  createAdminSessionToken,
  verifyAdminSessionToken,
} from '@/lib/server/session';

const ADMIN_SESSION_LIFETIME_MS = 1000 * 60 * 60 * 12;

function toHex(bytes: ArrayBuffer): string {
  return Array.from(new Uint8Array(bytes), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(value),
  );
  return toHex(digest);
}

function constantTimeEqual(left: string, right: string): boolean {
  if (left.length !== right.length) {
    return false;
  }

  let mismatch = 0;
  for (let index = 0; index < left.length; index += 1) {
    mismatch |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }

  return mismatch === 0;
}

export async function authenticateAdminPassword(password: string): Promise<{
  ok: boolean;
  reason?: 'invalid' | 'misconfigured';
}> {
  const config = getDocsServerConfig();
  if (!isAdminConfigured(config)) {
    return { ok: false, reason: 'misconfigured' };
  }

  const [receivedHash, expectedHash] = await Promise.all([
    sha256Hex(password),
    sha256Hex(config.adminPassword),
  ]);

  return constantTimeEqual(receivedHash, expectedHash)
    ? { ok: true }
    : { ok: false, reason: 'invalid' };
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