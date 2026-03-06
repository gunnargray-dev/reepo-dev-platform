import { Card, CardContent } from '@/components/ui/card';

interface StatCardProps {
  label: string;
  value: string;
}

export function StatCard({ label, value }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xl font-semibold font-mono tabular-nums text-foreground">{value}</div>
        <div className="mt-0.5 text-[12px] text-muted-foreground">{label}</div>
      </CardContent>
    </Card>
  );
}
