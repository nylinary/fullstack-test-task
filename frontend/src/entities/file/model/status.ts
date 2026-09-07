import type { BadgeVariant } from "@/shared/ui/StatusBadge";
import type { FileItem, ProcessingStatus } from "@/entities/file/model/types";

const PROCESSING_VARIANTS: Record<ProcessingStatus, BadgeVariant> = {
  failed: "danger",
  processing: "warning",
  processed: "success",
  uploaded: "secondary",
};

export function getProcessingVariant(status: ProcessingStatus): BadgeVariant {
  return PROCESSING_VARIANTS[status] ?? "secondary";
}

export function getScanVariant(file: FileItem): BadgeVariant {
  return file.requires_attention ? "warning" : "success";
}

/** Файл, над которым бэкенд ещё работает; такие дашборд продолжает опрашивать. */
export function isPending(file: FileItem): boolean {
  return file.processing_status !== "processed" && file.processing_status !== "failed";
}
