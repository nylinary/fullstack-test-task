import type { FileItem } from "@/entities/file/model/types";
import { apiUrl, request } from "@/shared/api/http";

export const DEFAULT_PAGE_SIZE = 100;

export function fetchFiles(limit = DEFAULT_PAGE_SIZE): Promise<FileItem[]> {
  return request<FileItem[]>(`/files?limit=${limit}`, {
    fallbackError: "Не удалось загрузить данные",
  });
}

export function uploadFile(title: string, file: File): Promise<FileItem> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  return request<FileItem>("/files", {
    method: "POST",
    body: formData,
    fallbackError: "Не удалось загрузить файл",
  });
}

export function renameFile(id: string, title: string): Promise<FileItem> {
  return request<FileItem>(`/files/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
    fallbackError: "Не удалось переименовать файл",
  });
}

export function deleteFile(id: string): Promise<void> {
  return request<void>(`/files/${id}`, {
    method: "DELETE",
    fallbackError: "Не удалось удалить файл",
  });
}

export function downloadUrl(id: string): string {
  return apiUrl(`/files/${id}/download`);
}
