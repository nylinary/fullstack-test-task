"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchAlerts } from "@/entities/alert/api/alertApi";
import type { AlertItem } from "@/entities/alert/model/types";
import { fetchFiles } from "@/entities/file/api/fileApi";
import { isPending } from "@/entities/file/model/status";
import type { FileItem } from "@/entities/file/model/types";
import { toMessage } from "@/shared/api/http";
import { PROCESSING_POLL_INTERVAL_MS } from "@/shared/config/env";

/**
 * Весь поток данных дашборда живёт здесь, поэтому компоненты ниже остаются
 * декларативными: они рисуют то, что им дали, и порождают события.
 */
export function useFilesDashboard() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const load = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!silent) {
      setIsLoading(true);
    }
    setError(null);

    try {
      const [nextFiles, nextAlerts] = await Promise.all([fetchFiles(), fetchAlerts()]);
      if (!isMounted.current) {
        return;
      }
      setFiles(nextFiles);
      setAlerts(nextAlerts);
    } catch (cause) {
      if (isMounted.current) {
        setError(toMessage(cause));
      }
    } finally {
      if (isMounted.current) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Обработка идёт в воркере Celery, поэтому только что загруженный файл
  // доходит до финального статуса чуть позже ответа на загрузку. Тихо обновляем
  // данные, пока всё не устоится, вместо того чтобы заставлять пользователя
  // жать "Обновить".
  const hasPending = files.some(isPending);
  useEffect(() => {
    if (!hasPending) {
      return;
    }

    const timer = setTimeout(() => void load({ silent: true }), PROCESSING_POLL_INTERVAL_MS);
    return () => clearTimeout(timer);
  }, [hasPending, files, load]);

  const refresh = useCallback(() => void load(), [load]);

  return { files, alerts, isLoading, error, refresh, reload: load };
}
