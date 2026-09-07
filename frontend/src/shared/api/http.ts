import { API_BASE_URL } from "@/shared/config/env";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ErrorBody = { detail?: unknown };

async function readErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as ErrorBody;
    return typeof body.detail === "string" ? body.detail : fallback;
  } catch {
    return fallback;
  }
}

/**
 * Единственное место, которое знает, как этот API сообщает об ошибках, — чтобы
 * ни одному вызывающему коду не приходилось помнить про `response.ok`.
 */
export async function request<T>(
  path: string,
  { fallbackError = "Запрос не удался", ...init }: RequestInit & { fallbackError?: string } = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", ...init });

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response, fallbackError), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export function toMessage(error: unknown, fallback = "Произошла ошибка"): string {
  return error instanceof Error ? error.message : fallback;
}
