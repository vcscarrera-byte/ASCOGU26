interface BadgeProps {
  label: string;
  variant: "tumor" | "drug" | "gene" | "relevance" | "buzz" | "session" | "gray";
  className?: string;
}

const variantStyles: Record<string, string> = {
  tumor: "bg-blue-100 text-blue-800",
  drug: "bg-emerald-100 text-emerald-800",
  gene: "bg-violet-100 text-violet-800",
  relevance: "bg-red-100 text-red-800",
  buzz: "bg-violet-100 text-violet-800",
  session: "bg-slate-100 text-slate-700",
  gray: "bg-slate-100 text-slate-600",
};

export default function Badge({ label, variant, className = "" }: BadgeProps) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-semibold ${variantStyles[variant]} ${className}`}>
      {label}
    </span>
  );
}
