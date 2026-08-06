import type { Grade } from "@/lib/api";

const STYLES: Record<Grade, string> = {
  A: "bg-grade-a-soft text-grade-a",
  B: "bg-grade-b-soft text-grade-b",
  C: "bg-grade-c-soft text-grade-c",
  F: "bg-grade-f-soft text-grade-f",
};

const LABELS: Record<Grade, string> = {
  A: "Clean",
  B: "Minor flags",
  C: "Caution",
  F: "High risk",
};

export function GradeBadge({ grade, size = "md" }: { grade: Grade; size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "h-6 w-6 text-xs",
    md: "h-8 w-8 text-sm",
    lg: "h-12 w-12 text-lg",
  }[size];

  return (
    <span
      className={`inline-flex items-center justify-center rounded-lg font-mono font-semibold ${STYLES[grade]} ${sizeClasses}`}
      title={LABELS[grade]}
    >
      {grade}
    </span>
  );
}

export function GradeLabel({ grade }: { grade: Grade }) {
  return <span className="text-text-muted text-sm">{LABELS[grade]}</span>;
}
