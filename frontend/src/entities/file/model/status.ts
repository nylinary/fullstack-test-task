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

/** A file the backend is still working on; the dashboard keeps polling these. */
export function isPending(file: FileItem): boolean {
  return file.processing_status !== "processed" && file.processing_status !== "failed";
}
