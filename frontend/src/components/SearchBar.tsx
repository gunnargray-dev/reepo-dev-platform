import { useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  compact?: boolean;
  defaultValue?: string;
}

export default function SearchBar({ onSearch, placeholder, compact, defaultValue = '' }: SearchBarProps) {
  const [query, setQuery] = useState(defaultValue);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };

  if (compact) {
    return (
      <form onSubmit={handleSubmit} className="relative">
        <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder || 'Search repos...'}
          className="w-full bg-bg-card border border-border-subtle rounded-lg pl-9 pr-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-accent transition-colors" />
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </form>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="relative max-w-2xl mx-auto">
      <input type="text" value={query} onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder || 'Search 500+ AI repos...'}
        className="w-full bg-bg-card border border-border-subtle rounded-xl pl-12 pr-32 py-4 text-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all" />
      <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 btn-primary text-sm">Search</button>
    </form>
  );
}
