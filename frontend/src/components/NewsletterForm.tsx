import { useState } from 'react';

export default function NewsletterForm() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setStatus('loading');
    try {
      const res = await fetch('/api/newsletter/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      setStatus(data.subscribed ? 'success' : 'error');
      if (data.subscribed) setEmail('');
    } catch {
      setStatus('error');
    }
  };

  if (status === 'success') {
    return <p className="text-score-green text-sm">Subscribed! Check your inbox.</p>;
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Get weekly AI repo digest"
        className="bg-bg-primary border border-border-subtle rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-accent focus:outline-none w-56"
      />
      <button
        type="submit"
        disabled={status === 'loading'}
        className="bg-accent hover:bg-accent-hover text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
      >
        {status === 'loading' ? '...' : 'Subscribe'}
      </button>
      {status === 'error' && <span className="text-score-red text-xs">Failed</span>}
    </form>
  );
}
