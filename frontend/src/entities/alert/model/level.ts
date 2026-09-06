import type { AlertLevel } from "@/entities/alert/model/types";
import type { BadgeVariant } from "@/shared/ui/StatusBadge";

const LEVEL_VARIANTS: Record<AlertLevel, BadgeVariant> = {
  critical: "danger",
  warning: "warning",
  info: "success",
};

export function getLevelVariant(level: AlertLevel): BadgeVariant {
  return LEVEL_VARIANTS[level] ?? "success";
}
