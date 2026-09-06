"use client";

import { useCallback, useState } from "react";

import { uploadFile } from "@/entities/file/api/fileApi";
import { toMessage } from "@/shared/api/http";

type Options = { onUploaded: () => Promise<void> | void };

/**
 * Owns the upload form state and the submit workflow; the modal below is a
 * pure rendering of what this hook exposes.
 */
export function useUploadFile({ onUploaded }: Options) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setTitle("");
    setFile(null);
    setError(null);
  }, []);

  const open = useCallback(() => setIsOpen(true), []);

  const close = useCallback(() => {
    setIsOpen(false);
    reset();
  }, [reset]);

  const submit = useCallback(async () => {
    if (!title.trim() || !file) {
      setError("Укажите название и выберите файл");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await uploadFile(title.trim(), file);
      setIsOpen(false);
      reset();
      await onUploaded();
    } catch (cause) {
      setError(toMessage(cause));
    } finally {
      setIsSubmitting(false);
    }
  }, [file, onUploaded, reset, title]);

  return { isOpen, isSubmitting, title, file, error, open, close, setTitle, setFile, submit };
}
