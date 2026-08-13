const ADMIN_DESTINATION_ORIGIN = 'https://admin.invalid';
const DEFAULT_ADMIN_DESTINATION = '/admin';
const ENCODED_PATH_SEPARATOR = /%(?:2f|5c)/i;

/**
 * Reduce an untrusted post-login destination to a same-origin admin path.
 *
 * Returning a normalized path instead of a URL keeps callers from accidentally
 * carrying an attacker-controlled origin into a redirect.
 */
export function parseAdminDestination(
  value: string | null | undefined,
): string {
  if (!value || value.length > 2_048 || !value.startsWith('/')) {
    return DEFAULT_ADMIN_DESTINATION;
  }

  const rawPath = value.split(/[?#]/u, 1)[0] ?? '';
  if (
    value.startsWith('//') ||
    value.includes('\\') ||
    ENCODED_PATH_SEPARATOR.test(rawPath)
  ) {
    return DEFAULT_ADMIN_DESTINATION;
  }

  try {
    const baseUrl = new URL(ADMIN_DESTINATION_ORIGIN);
    const destination = new URL(value, baseUrl);
    if (
      destination.origin !== baseUrl.origin ||
      (destination.pathname !== '/admin' &&
        !destination.pathname.startsWith('/admin/'))
    ) {
      return DEFAULT_ADMIN_DESTINATION;
    }

    // Fragments never reach the server and are unnecessary for the admin UI.
    return `${destination.pathname}${destination.search}`;
  } catch {
    return DEFAULT_ADMIN_DESTINATION;
  }
}
