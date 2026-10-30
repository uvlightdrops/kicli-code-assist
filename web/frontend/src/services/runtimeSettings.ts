/**
 * Client for the shared runtime settings API (GET/POST /api/settings).
 *
 * Writes go to config/runtime/runtime.yaml on the server; secrets are never
 * transferred (rows only carry a `configured` flag, values live in creds.yaml).
 */

export type SettingType = 'string' | 'integer' | 'number' | 'boolean' | 'array' | 'object' | 'null';
export type SettingValue = string | number | boolean | null | SettingValue[] | { [key: string]: SettingValue };

export interface SettingRow {
  path: string;
  label: string;
  description: string;
  type: SettingType | string;
  types: string[];
  enum: SettingValue[];
  effective: SettingValue;
  override: SettingValue;
  overridden: boolean;
  configured: boolean;
  editable: boolean;
  reason: string;
  secret: boolean;
  restart_required: boolean;
  shadowed: boolean;
  shadowed_by: 'creds.yaml' | 'KI_CFG_*' | string | null;
  applies: 'restart' | 'next_request';
  section: string;
}

export interface SettingsSnapshot {
  revision: string;
  rows: SettingRow[];
  target: string;
  token: string;
  token_header: string;
  restart_required_paths?: string[];
}

export class SettingsApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

let cachedToken: { header: string; token: string } | null = null;

async function parse(response: Response): Promise<SettingsSnapshot> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new SettingsApiError(response.status, data.error || `HTTP ${response.status}`);
  }
  if (data.token && data.token_header) {
    cachedToken = { header: data.token_header, token: data.token };
  }
  return data as SettingsSnapshot;
}

export async function fetchSettings(): Promise<SettingsSnapshot> {
  return parse(await fetch('/api/settings', { cache: 'no-store', credentials: 'same-origin' }));
}

/** Header carrying the per-process write token (fetched from GET /api/settings). */
export async function settingsWriteHeaders(): Promise<Record<string, string>> {
  if (!cachedToken) {
    await fetchSettings();
  }
  return cachedToken ? { [cachedToken.header]: cachedToken.token } : {};
}

export async function saveSettings(
  revision: string,
  changes: Record<string, SettingValue>,
  remove: string[] = [],
): Promise<SettingsSnapshot> {
  const headers = { 'Content-Type': 'application/json', ...(await settingsWriteHeaders()) };
  const response = await fetch('/api/settings', {
    method: 'POST',
    headers,
    credentials: 'same-origin',
    body: JSON.stringify({ revision, changes, remove }),
  });
  return parse(response);
}

export interface SecretRow {
  path: string;
  label: string;
  configured: boolean;
  overridden: boolean;
  editable: boolean;
  reason: string;
  restart_required: boolean;
  applies: 'restart' | 'next_request';
  section: string;
}

export interface SecretSnapshot {
  revision: string;
  rows: SecretRow[];
  editable: boolean;
  reason: string;
  target: string;
}

async function parseSecrets(response: Response): Promise<SecretSnapshot> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new SettingsApiError(response.status, data.error || `HTTP ${response.status}`);
  }
  return data as SecretSnapshot;
}

/** Credential inventory: paths + configured flag only, never values. */
export async function fetchSecrets(): Promise<SecretSnapshot> {
  return parseSecrets(await fetch('/api/settings/secrets', { cache: 'no-store', credentials: 'same-origin' }));
}

/** Write-only: sends a new value (or removes the creds.yaml entry); nothing is returned. */
export async function saveSecret(
  revision: string, path: string, change: { value: string } | { remove: true },
): Promise<SecretSnapshot> {
  const headers = { 'Content-Type': 'application/json', ...(await settingsWriteHeaders()) };
  const response = await fetch('/api/settings/secrets', {
    method: 'POST',
    headers,
    credentials: 'same-origin',
    body: JSON.stringify({ revision, path, ...change }),
  });
  return parseSecrets(response);
}
