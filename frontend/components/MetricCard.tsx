import Link from "next/link";

interface MetricCardProps {
  label: string;
  value: string | number;
  icon: string;
  href?: string;
}

export default function MetricCard({ label, value, icon, href }: MetricCardProps) {
  const content = (
    <>
      <div className="text-xl sm:text-2xl mb-1">{icon}</div>
      <div className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">{typeof value === 'number' ? value.toLocaleString() : value}</div>
      <div className="text-[10px] sm:text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">{label}</div>
    </>
  );

  if (href) {
    return (
      <Link href={href} className="bg-white border border-slate-200 rounded-xl p-3 sm:p-5 text-center shadow-sm hover:shadow-md transition-shadow duration-200 cursor-pointer block">
        {content}
      </Link>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3 sm:p-5 text-center shadow-sm hover:shadow-md transition-shadow duration-200">
      {content}
    </div>
  );
}
