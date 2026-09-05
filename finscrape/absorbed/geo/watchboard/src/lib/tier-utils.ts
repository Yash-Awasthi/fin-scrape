export function tierClass(t: number | string): string {
  return t === 1 ? 't1' : t === 2 ? 't2' : t === 3 ? 't3' : t === 'all' ? 't3' : 't4';
}

export function tierLabel(t: number | string): string {
  return t === 1
    ? 'Official'
    : t === 2
      ? 'Major'
      : t === 3
        ? 'Institutional'
        : t === 'all'
          ? 'All tiers'
          : 'Unverified';
}

export function tierLabelFull(t: number | string): string {
  return t === 1
    ? 'Tier 1 — Official'
    : t === 2
      ? 'Tier 2 — Major Outlet'
      : t === 3
        ? 'Tier 3 — Institutional'
        : t === 'all'
          ? 'All tiers'
          : 'Tier 4';
}

export function tierLabelShort(t: number | string): string {
  return t === 1 ? 'T1' : t === 2 ? 'T2' : t === 3 ? 'T3' : t === 'all' ? 'T*' : 'T4';
}

export function contestedBadge(c: string): { text: string; className: string } {
  if (c === 'no') return { text: 'Verified', className: 'contested-no' };
  if (c === 'evolving') return { text: 'Evolving', className: 'contested-evolving' };
  if (c === 'heavily') return { text: 'Heavily Contested', className: 'contested-yes' };
  if (c === 'partial') return { text: 'Partial', className: 'contested-evolving' };
  return { text: 'Contested', className: 'contested-yes' };
}
