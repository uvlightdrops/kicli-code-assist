import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { io } from 'socket.io-client';
import {
  fetchSecrets,
  fetchSettings,
  saveSecret,
  saveSettings,
  SecretSnapshot,
  SettingRow,
  SettingsApiError,
  SettingsSnapshot,
  SettingValue,
} from '../services/runtimeSettings';

/**
 * Typed editor for every schema field of the merged ki-core configuration.
 *
 * Values are stored as overrides in config/runtime/runtime.yaml. llm.*, http.*
 * and agent.* apply on the next request; everything else needs a restart.
 * KI_CFG_* environment variables and creds.yaml take precedence and are shown
 * read-only. Secrets are never sent to the browser.
 */

type Draft = Record<string, { raw: string; value?: SettingValue; error?: string }>;

const isListOfScalars = (value: SettingValue) =>
  Array.isArray(value) && value.every(v => v === null || typeof v !== 'object');

function display(row: SettingRow, value: SettingValue): string {
  if (row.types.includes('array') && (value === null || isListOfScalars(value))) {
    return ((value as SettingValue[] | null) ?? []).map(v => String(v)).join('\n');
  }
  if (value !== null && typeof value === 'object') return JSON.stringify(value, null, 2);
  return value === null || value === undefined ? '' : String(value);
}

function parseInput(row: SettingRow, raw: string): { value?: SettingValue; error?: string } {
  const types = row.types;
  const trimmed = raw.trim();
  if (trimmed === '' && types.includes('null')) return { value: null };
  if (row.enum.length) {
    const match = row.enum.find(option => String(option) === raw);
    return match === undefined ? { error: 'Ungültige Auswahl' } : { value: match };
  }
  if (types.includes('boolean')) return { value: raw === 'true' };
  if (types.includes('integer')) {
    return /^-?\d+$/.test(trimmed) ? { value: Number(trimmed) } : { error: 'Ganzzahl erwartet' };
  }
  if (types.includes('number')) {
    const n = Number(trimmed);
    return trimmed !== '' && Number.isFinite(n) ? { value: n } : { error: 'Zahl erwartet' };
  }
  if (types.includes('array')) {
    if (row.effective === null || isListOfScalars(row.effective)) {
      return { value: raw.split('\n').map(s => s.trim()).filter(Boolean) };
    }
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? { value: parsed } : { error: 'JSON-Liste erwartet' };
    } catch {
      return { error: 'JSON-Liste erwartet' };
    }
  }
  if (types.includes('object')) {
    try {
      return { value: JSON.parse(raw) };
    } catch {
      return { error: 'JSON-Objekt erwartet' };
    }
  }
  return { value: raw };
}

const same = (a: SettingValue | undefined, b: SettingValue | undefined) => JSON.stringify(a) === JSON.stringify(b);

function Badge({ tone, children, title }: { tone: string; children: React.ReactNode; title?: string }) {
  return (
    <span title={title} className={`text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap ${tone}`}>
      {children}
    </span>
  );
}

function RowBadges({ row }: { row: SettingRow }) {
  return (
    <div className="flex flex-wrap gap-1">
      {row.applies === 'restart' ? (
        <Badge tone="bg-amber-900 text-amber-200" title="Wirkt erst nach Neustart des Servers">Neustart nötig</Badge>
      ) : (
        <Badge tone="bg-emerald-900 text-emerald-200" title="Wirkt ab der nächsten Anfrage">live (nächste Anfrage)</Badge>
      )}
      {row.overridden && <Badge tone="bg-blue-900 text-blue-200" title="Wert stammt aus runtime.yaml">runtime.yaml</Badge>}
      {row.shadowed_by && (
        <Badge tone="bg-purple-900 text-purple-200" title="Höhere Ebene überschreibt diesen Wert">
          überschrieben durch {row.shadowed_by}
        </Badge>
      )}
      {row.secret && (
        <Badge tone={row.configured ? 'bg-gray-700 text-gray-200' : 'bg-red-900 text-red-200'}>
          {row.configured ? 'Secret gesetzt' : 'Secret fehlt'}
        </Badge>
      )}
    </div>
  );
}

function Editor({
  row, raw, disabled, onChange,
}: { row: SettingRow; raw: string; disabled: boolean; onChange: (raw: string) => void }) {
  const base = 'w-full bg-gray-900 border border-gray-600 rounded px-2 py-1 text-sm text-gray-100 disabled:opacity-60';
  if (row.secret) {
    return (
      <div className="text-xs text-gray-400">
        {row.configured ? '•••••• (konfiguriert)' : 'nicht gesetzt'} – Wert im Abschnitt „Zugangsdaten“ setzen (wird in <code>creds.yaml</code> gespeichert).
      </div>
    );
  }
  if (row.enum.length) {
    return (
      <select className={base} value={raw} disabled={disabled} onChange={e => onChange(e.target.value)}>
        {!row.enum.some(option => String(option) === raw) && <option value={raw}>{raw || '—'}</option>}
        {row.enum.map(option => <option key={String(option)} value={String(option)}>{String(option)}</option>)}
      </select>
    );
  }
  if (row.types.includes('boolean')) {
    return (
      <label className="flex items-center gap-2 text-sm text-gray-300">
        <input type="checkbox" checked={raw === 'true'} disabled={disabled}
          onChange={e => onChange(e.target.checked ? 'true' : 'false')} />
        {raw === 'true' ? 'an' : 'aus'}
      </label>
    );
  }
  if (row.types.includes('array') || row.types.includes('object')) {
    return (
      <textarea className={`${base} font-mono`} rows={Math.min(6, Math.max(2, raw.split('\n').length))}
        value={raw} disabled={disabled} onChange={e => onChange(e.target.value)}
        placeholder={row.types.includes('array') ? 'Ein Eintrag pro Zeile' : 'JSON'} />
    );
  }
  const numeric = row.types.includes('integer') || row.types.includes('number');
  return (
    <input className={base} type={numeric ? 'number' : 'text'} step={row.types.includes('integer') ? 1 : 'any'}
      value={raw} disabled={disabled} onChange={e => onChange(e.target.value)} />
  );
}

function SecretsSection({ filter }: { filter: string }) {
  const [snapshot, setSnapshot] = useState<SecretSnapshot | null>(null);
  const [unavailable, setUnavailable] = useState<string | null>(null);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<{ tone: 'ok' | 'error'; text: string } | null>(null);

  const load = useCallback(async () => {
    try {
      setSnapshot(await fetchSecrets());
      setUnavailable(null);
    } catch (err) {
      setUnavailable(err instanceof Error ? err.message : 'Zugangsdaten nicht verfügbar');
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const submit = async (path: string, change: { value: string } | { remove: true }) => {
    if (!snapshot) return;
    setBusy(path);
    setMessage(null);
    try {
      setSnapshot(await saveSecret(snapshot.revision, path, change));
      setInputs(prev => ({ ...prev, [path]: '' }));
      setMessage({ tone: 'ok', text: `${path}: ${'remove' in change ? 'entfernt' : 'gespeichert'} – wirkt ab der nächsten Anfrage.` });
    } catch (err) {
      if (err instanceof SettingsApiError && err.status === 409) await load();
      setMessage({ tone: 'error', text: err instanceof Error ? err.message : 'Speichern fehlgeschlagen' });
    } finally {
      setBusy(null);
    }
  };

  const needle = filter.trim().toLowerCase();
  const rows = (snapshot?.rows ?? []).filter(row => !needle || row.path.toLowerCase().includes(needle));
  if (snapshot && needle && rows.length === 0) return null;

  return (
    <section className="border border-gray-700 rounded" data-testid="secrets-section">
      <h3 className="px-3 py-2 bg-gray-900 text-sm font-semibold">
        Zugangsdaten {snapshot && <span className="text-xs text-gray-400 font-normal">(nur schreiben → {snapshot.target})</span>}
      </h3>
      <div className="px-3 py-2 text-xs text-gray-400">
        Gespeicherte Werte werden nie angezeigt. Leere Eingabe ändert nichts; „Entfernen“ löscht den Eintrag aus {snapshot?.target ?? 'creds.yaml'}.
      </div>
      {unavailable && <div className="px-3 pb-2 text-sm text-amber-300">{unavailable}</div>}
      {message && <div className={`px-3 pb-2 text-sm ${message.tone === 'ok' ? 'text-emerald-300' : 'text-red-300'}`}>{message.text}</div>}
      <div className="divide-y divide-gray-700">
        {rows.map(row => {
          const disabled = !row.editable || !snapshot?.editable || busy !== null;
          const value = inputs[row.path] ?? '';
          return (
            <form key={row.path} className="px-3 py-2 space-y-1" data-secret-path={row.path}
              onSubmit={e => { e.preventDefault(); if (value.trim()) submit(row.path, { value }); }}>
              <div className="flex justify-between gap-2">
                <div className="text-sm font-mono">{row.path}</div>
                <div className="flex flex-wrap gap-1">
                  <Badge tone={row.configured ? 'bg-gray-700 text-gray-200' : 'bg-red-900 text-red-200'}>
                    {row.configured ? 'Secret gesetzt' : 'Secret fehlt'}
                  </Badge>
                  {row.applies === 'restart'
                    ? <Badge tone="bg-amber-900 text-amber-200">Neustart nötig</Badge>
                    : <Badge tone="bg-emerald-900 text-emerald-200">live (nächste Anfrage)</Badge>}
                </div>
              </div>
              <div className="flex gap-2">
                <input type="password" autoComplete="new-password" spellCheck={false}
                  className="flex-1 bg-gray-900 border border-gray-600 rounded px-2 py-1 text-sm text-gray-100 disabled:opacity-60"
                  placeholder={row.configured ? 'Neuen Wert eingeben, um zu ersetzen' : 'Wert eingeben'}
                  value={value} disabled={disabled}
                  onChange={e => setInputs(prev => ({ ...prev, [row.path]: e.target.value }))} />
                <button type="submit" className="px-2 py-1 text-xs bg-blue-600 text-white rounded disabled:opacity-50"
                  disabled={disabled || !value.trim()}>
                  Secret speichern
                </button>
                {row.overridden && (
                  <button type="button" className="px-2 py-1 text-xs bg-gray-700 rounded disabled:opacity-50"
                    disabled={disabled} onClick={() => submit(row.path, { remove: true })}>
                    Entfernen
                  </button>
                )}
              </div>
              {row.reason && <div className="text-xs text-gray-500">{row.reason}</div>}
            </form>
          );
        })}
      </div>
    </section>
  );
}

export function RuntimeSettingsPanel() {
  const [snapshot, setSnapshot] = useState<SettingsSnapshot | null>(null);
  const [draft, setDraft] = useState<Draft>({});
  const [removals, setRemovals] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ tone: 'ok' | 'warn' | 'error'; text: string } | null>(null);
  const [externalChange, setExternalChange] = useState(false);

  const dirty = Object.keys(draft).length > 0 || removals.size > 0;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setSnapshot(await fetchSettings());
      setDraft({});
      setRemovals(new Set());
      setExternalChange(false);
    } catch (err) {
      setMessage({ tone: 'error', text: err instanceof Error ? err.message : 'Laden fehlgeschlagen' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const socket = io({ path: '/socket.io', transports: ['websocket', 'polling'] });
    socket.on('settings.updated', (event: { revision?: string }) => {
      setSnapshot(current => {
        if (current && event.revision && event.revision !== current.revision) setExternalChange(true);
        return current;
      });
    });
    return () => { socket.disconnect(); };
  }, []);

  useEffect(() => {
    if (externalChange && !dirty && !saving) load();
  }, [externalChange, dirty, saving, load]);

  const rowsBySection = useMemo(() => {
    const groups = new Map<string, SettingRow[]>();
    const needle = filter.trim().toLowerCase();
    for (const row of snapshot?.rows ?? []) {
      const haystack = `${row.path} ${row.label} ${row.description}`.toLowerCase();
      if (needle && !haystack.includes(needle)) continue;
      groups.set(row.section, [...(groups.get(row.section) ?? []), row]);
    }
    return [...groups.entries()];
  }, [snapshot, filter]);

  const change = (row: SettingRow, raw: string) => {
    const parsed = parseInput(row, raw);
    setDraft(prev => {
      const next = { ...prev };
      if (!parsed.error && same(parsed.value, row.effective)) delete next[row.path];
      else next[row.path] = { raw, ...parsed };
      return next;
    });
    setRemovals(prev => { const next = new Set(prev); next.delete(row.path); return next; });
  };

  const resetOverride = (row: SettingRow) => {
    setDraft(prev => { const next = { ...prev }; delete next[row.path]; return next; });
    setRemovals(prev => new Set(prev).add(row.path));
  };

  const save = async () => {
    if (!snapshot) return;
    const invalid = Object.entries(draft).filter(([, d]) => d.error);
    if (invalid.length) {
      setMessage({ tone: 'error', text: `Ungültige Eingaben: ${invalid.map(([p]) => p).join(', ')}` });
      return;
    }
    const changes = Object.fromEntries(Object.entries(draft).map(([path, d]) => [path, d.value as SettingValue]));
    setSaving(true);
    try {
      const result = await saveSettings(snapshot.revision, changes, [...removals]);
      setSnapshot(result);
      setDraft({});
      setRemovals(new Set());
      const restart = result.restart_required_paths ?? [];
      setMessage(restart.length
        ? { tone: 'warn', text: `Gespeichert. Neustart nötig für: ${restart.join(', ')}` }
        : { tone: 'ok', text: 'Gespeichert – wirkt ab der nächsten Anfrage.' });
    } catch (err) {
      if (err instanceof SettingsApiError && err.status === 409) {
        setMessage({ tone: 'warn', text: 'Konfiguration wurde zwischenzeitlich geändert. Bitte neu laden und erneut speichern.' });
        setExternalChange(true);
      } else {
        setMessage({ tone: 'error', text: err instanceof Error ? err.message : 'Speichern fehlgeschlagen' });
      }
    } finally {
      setSaving(false);
    }
  };

  if (loading && !snapshot) return <div className="text-sm text-gray-400">Lade Konfiguration…</div>;
  if (!snapshot) {
    return (
      <div className="text-sm text-red-300 space-y-2">
        <div>{message?.text ?? 'Konfiguration nicht verfügbar.'}</div>
        <button className="px-2 py-1 bg-gray-700 rounded" onClick={load}>Erneut versuchen</button>
      </div>
    );
  }

  const toneClass = { ok: 'text-emerald-300', warn: 'text-amber-300', error: 'text-red-300' };

  return (
    <div className="space-y-4 text-gray-200">
      <div className="text-xs text-gray-400 space-y-1">
        <div>Änderungen werden als Override in <code>{snapshot.target}</code> gespeichert.</div>
        <div>
          Reihenfolge: Defaults → ki.yaml → Stage → runtime.yaml → <code>KI_CFG_*</code> → <code>creds.yaml</code>.
          API-Keys und andere Secrets landen in <code>creds.yaml</code> (Abschnitt „Zugangsdaten“, nur schreibbar).
        </div>
      </div>

      <div className="flex gap-2 items-center sticky top-0 bg-gray-800 py-2 z-10">
        <input className="flex-1 bg-gray-900 border border-gray-600 rounded px-2 py-1 text-sm"
          placeholder="Filter (Pfad, Beschreibung)…" value={filter} onChange={e => setFilter(e.target.value)} />
        <button className="px-3 py-1 text-sm bg-gray-700 rounded disabled:opacity-50" onClick={load} disabled={saving}>
          Neu laden
        </button>
        <button className="px-3 py-1 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
          onClick={save} disabled={!dirty || saving}>
          {saving ? 'Speichere…' : 'Speichern'}
        </button>
      </div>

      {message && <div className={`text-sm ${toneClass[message.tone]}`}>{message.text}</div>}
      {externalChange && dirty && (
        <div className="text-sm text-amber-300">Die Konfiguration wurde extern geändert; ungespeicherte Änderungen bleiben erhalten.</div>
      )}

      <SecretsSection filter={filter} />

      {rowsBySection.map(([section, rows]) => (
        <section key={section} className="border border-gray-700 rounded">
          <h3 className="px-3 py-2 bg-gray-900 text-sm font-semibold">{section}</h3>
          <div className="divide-y divide-gray-700">
            {rows.map(row => {
              const pending = draft[row.path];
              const removing = removals.has(row.path);
              const raw = pending?.raw ?? display(row, row.effective);
              const disabled = !row.editable || saving;
              return (
                <div key={row.path} className="px-3 py-2 space-y-1">
                  <div className="flex justify-between gap-2">
                    <div>
                      <div className="text-sm font-mono">{row.path}</div>
                      {row.description && <div className="text-xs text-gray-400">{row.description}</div>}
                    </div>
                    <RowBadges row={row} />
                  </div>
                  <Editor row={row} raw={raw} disabled={disabled} onChange={value => change(row, value)} />
                  {pending?.error && <div className="text-xs text-red-300">{pending.error}</div>}
                  {!row.editable && row.reason && <div className="text-xs text-gray-500">{row.reason}</div>}
                  {row.shadowed_by && row.editable && (
                    <div className="text-xs text-purple-300">
                      Ein Override in runtime.yaml wird durch {row.shadowed_by} verdeckt.
                    </div>
                  )}
                  {row.overridden && row.editable && (
                    <button className="text-xs text-blue-300 hover:underline disabled:opacity-50" disabled={saving || removing}
                      onClick={() => resetOverride(row)}>
                      {removing ? 'Override wird beim Speichern entfernt' : 'Override entfernen'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
