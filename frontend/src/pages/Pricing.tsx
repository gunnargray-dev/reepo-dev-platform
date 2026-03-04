import { useEffect, useState } from 'react';

interface Tier {
  name: string;
  price: string;
  price_yearly?: string;
  features: string[];
}

const FALLBACK_TIERS: Tier[] = [
  {
    name: 'Free',
    price: '$0',
    features: ['Browse all repos', 'Basic search', '3 collections', '100 API requests/day', 'Community access'],
  },
  {
    name: 'Pro',
    price: '$9/mo',
    price_yearly: '$79/yr',
    features: ['Everything in Free', 'Unlimited collections', 'Comparison tool', 'CSV/JSON export', '10,000 API requests/day', 'Priority support'],
  },
];

export default function Pricing() {
  const [tiers, setTiers] = useState<Tier[]>(FALLBACK_TIERS);

  useEffect(() => {
    document.title = 'Pricing — Reepo.dev';
    fetch('/api/pricing')
      .then((r) => r.json())
      .then((data) => { if (data.tiers) setTiers(data.tiers); })
      .catch(() => {});
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold text-white mb-3">Simple, transparent pricing</h1>
        <p className="text-gray-400 text-lg">Start free. Upgrade when you need more power.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {tiers.map((tier) => (
          <div
            key={tier.name}
            className={`card p-8 flex flex-col ${tier.name === 'Pro' ? 'border-accent/50 ring-1 ring-accent/20' : ''}`}
          >
            <h2 className="text-xl font-bold text-white">{tier.name}</h2>
            <div className="mt-4 mb-6">
              <span className="text-4xl font-bold text-white">{tier.price}</span>
              {tier.price_yearly && (
                <span className="text-sm text-gray-400 ml-2">or {tier.price_yearly}</span>
              )}
            </div>
            <ul className="space-y-3 flex-1">
              {tier.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-sm text-gray-300">
                  <svg className="w-4 h-4 text-score-green flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {f}
                </li>
              ))}
            </ul>
            <button className={`mt-8 w-full py-3 rounded-lg font-medium transition-colors ${tier.name === 'Pro' ? 'bg-accent hover:bg-accent-hover text-white' : 'bg-bg-primary border border-border-subtle text-gray-300 hover:text-white'}`}>
              {tier.name === 'Pro' ? 'Upgrade to Pro' : 'Current plan'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
