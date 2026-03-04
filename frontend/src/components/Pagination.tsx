interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages: (number | '...')[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push('...');
    for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) pages.push(i);
    if (page < totalPages - 2) pages.push('...');
    pages.push(totalPages);
  }

  return (
    <div className="flex items-center justify-center gap-1 mt-8">
      <button onClick={() => onPageChange(page - 1)} disabled={page <= 1}
        className="px-3 py-2 text-sm rounded-lg border border-border-subtle text-gray-400 hover:text-white hover:border-border-hover disabled:opacity-30 disabled:cursor-not-allowed transition-colors">Prev</button>
      {pages.map((p, i) =>
        p === '...' ? (
          <span key={`dots-${i}`} className="px-2 py-2 text-sm text-gray-500">...</span>
        ) : (
          <button key={p} onClick={() => onPageChange(p as number)}
            className={`px-3 py-2 text-sm rounded-lg border transition-colors ${p === page ? 'border-accent bg-accent/10 text-accent' : 'border-border-subtle text-gray-400 hover:text-white hover:border-border-hover'}`}>{p}</button>
        )
      )}
      <button onClick={() => onPageChange(page + 1)} disabled={page >= totalPages}
        className="px-3 py-2 text-sm rounded-lg border border-border-subtle text-gray-400 hover:text-white hover:border-border-hover disabled:opacity-30 disabled:cursor-not-allowed transition-colors">Next</button>
    </div>
  );
}
