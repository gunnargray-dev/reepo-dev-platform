import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

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
    document.title = 'Pricing -- Reepo.dev';
    fetch('/api/pricing')
      .then((r) => r.json())
      .then((data) => { if (data.tiers) setTiers(data.tiers); })
      .catch(() => {});
  }, []);

  return (
    <div className="mx-auto max-w-2xl animate-fade-in px-4 py-16 sm:px-6">
      <div className="mb-10 text-center">
        <h1 className="text-xl font-semibold text-foreground">Pricing</h1>
        <p className="mt-1 text-[14px] text-muted-foreground">Start free. Upgrade when you need more.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {tiers.map((tier) => (
          <Card key={tier.name} className={tier.name === 'Pro' ? 'ring-1 ring-border' : ''}>
            <CardContent className="flex flex-col p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-[15px] font-semibold text-foreground">{tier.name}</h2>
                {tier.name === 'Pro' && <Badge variant="secondary">Popular</Badge>}
              </div>
              <div className="mb-5 mt-4">
                <span className="font-mono text-3xl font-semibold text-foreground">{tier.price}</span>
                {tier.price_yearly && <span className="ml-1.5 text-[13px] text-muted-foreground">or {tier.price_yearly}</span>}
              </div>
              <ul className="flex-1 space-y-2.5">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-[13px] text-muted-foreground">
                    <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-foreground" />
                    {f}
                  </li>
                ))}
              </ul>
              <Button variant={tier.name === 'Pro' ? 'default' : 'outline'} className="mt-6 w-full">
                {tier.name === 'Pro' ? 'Upgrade to Pro' : 'Current plan'}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
