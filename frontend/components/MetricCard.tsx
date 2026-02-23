interface MetricCardProps {
  label: string;
  value: string | number;
  icon: string;
}

export default function MetricCard({ label, value, icon }: MetricCardProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 text-center shadow-sm hover:shadow-md transition-shadow duration-200">
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-3xl font-bold text-slate-900 tracking-tight">{typeof value === 'number' ? value.toLocaleString() : value}</div>
      <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">{label}</div>
    </div>
  );
}
