/** Search every loaded JSON field without allocating a second serialized payload. */
export function recordMatches(record: unknown, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) return true;
  const pending: unknown[] = [record];
  const seen = new WeakSet<object>();
  while (pending.length) {
    const value = pending.pop();
    if (value !== null && typeof value === "object") {
      if (seen.has(value)) continue;
      seen.add(value);
      for (const [key, child] of Object.entries(value)) {
        if (!Array.isArray(value) && key.toLowerCase().includes(needle))
          return true;
        pending.push(child);
      }
    } else if (
      value !== undefined &&
      String(value).toLowerCase().includes(needle)
    ) {
      return true;
    }
  }
  return false;
}
