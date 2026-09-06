import type { AlertItem } from "@/entities/alert/model/types";
import { request } from "@/shared/api/http";

export const DEFAULT_PAGE_SIZE = 100;

export function fetchAlerts(limit = DEFAULT_PAGE_SIZE): Promise<AlertItem[]> {
  return request<AlertItem[]>(`/alerts?limit=${limit}`, {
    fallbackError: "Не удалось загрузить данные",
  });
}
