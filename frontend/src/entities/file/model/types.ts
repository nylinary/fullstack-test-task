export type ProcessingStatus = "uploaded" | "processing" | "processed" | "failed";
export type ScanStatus = "clean" | "suspicious" | "failed";

export type FileItem = {
  id: string;
  title: string;
  original_name: string;
  mime_type: string;
  size: number;
  processing_status: ProcessingStatus;
  scan_status: ScanStatus | null;
  scan_details: string | null;
  metadata_json: Record<string, unknown> | null;
  requires_attention: boolean;
  created_at: string;
  updated_at: string;
};
