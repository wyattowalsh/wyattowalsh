export const ADMIN_SESSION_COOKIE = 'docs-admin-session';

type AdminSessionPayload = {
  role: 'admin';
  issuedAt: number;
  expiresAt: number;
};

function toHex(bytes: ArrayBuffer): string {
  return Array.from(new Uint8Array(bytes), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}

async function importHmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
}

async function signValue(value: string, secret: string): Promise<string> {
  const key = await importHmacKey(secret);
  const signature = await crypto.subtle.sign(
    'HMAC',
    key,
    new TextEncoder().encode(value),
  );
  return toHex(signature);
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

export async function createAdminSessionToken(
  secret: string,
  lifetimeMs: number,
): Promise<{ token: string; expiresAt: number }> {
  const issuedAt = Date.now();
  const expiresAt = issuedAt + lifetimeMs;
  const payload: AdminSessionPayload = {
    role: 'admin',
    issuedAt,
    expiresAt,
  };
  const encodedPayload = encodeURIComponent(JSON.stringify(payload));
  const signature = await signValue(encodedPayload, secret);

  return {
    token: `${encodedPayload}.${signature}`,
    expiresAt,
  };
}

export async function verifyAdminSessionToken(
  token: string,
  secret: string,
): Promise<AdminSessionPayload | null> {
  const separatorIndex = token.lastIndexOf('.');
  if (separatorIndex <= 0) {
    return null;
  }

  const encodedPayload = token.slice(0, separatorIndex);
  const signature = token.slice(separatorIndex + 1);
  const expectedSignature = await signValue(encodedPayload, secret);
  if (!constantTimeEqual(signature, expectedSignature)) {
    return null;
  }

  try {
    const payload = JSON.parse(
      decodeURIComponent(encodedPayload),
    ) as Partial<AdminSessionPayload>;

    if (
      payload.role !== 'admin' ||
      typeof payload.issuedAt !== 'number' ||
      typeof payload.expiresAt !== 'number' ||
      payload.expiresAt <= Date.now()
    ) {
      return null;
    }

    return payload as AdminSessionPayload;
  } catch {
    return null;
  }
}

export function buildAdminSessionCookieOptions(
  isProduction: boolean,
  expiresAt: number,
) {
  return {
    httpOnly: true,
    sameSite: 'lax' as const,
    secure: isProduction,
    path: '/',
    expires: new Date(expiresAt),
  };
}