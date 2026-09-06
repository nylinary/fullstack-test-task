"use client";

import type { FormEvent } from "react";
import { Alert, Button, Form, Modal } from "react-bootstrap";

import type { useUploadFile } from "@/features/upload-file/model/useUploadFile";

export function UploadFileModal({ upload }: { upload: ReturnType<typeof useUploadFile> }) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void upload.submit();
  }

  return (
    <Modal show={upload.isOpen} onHide={upload.close} centered>
      <Form onSubmit={handleSubmit}>
        <Modal.Header closeButton>
          <Modal.Title>Добавить файл</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {upload.error ? <Alert variant="danger">{upload.error}</Alert> : null}
          <Form.Group className="mb-3">
            <Form.Label>Название</Form.Label>
            <Form.Control
              value={upload.title}
              onChange={(event) => upload.setTitle(event.target.value)}
              placeholder="Например, Договор с подрядчиком"
            />
          </Form.Group>
          <Form.Group>
            <Form.Label>Файл</Form.Label>
            <Form.Control
              type="file"
              onChange={(event) => upload.setFile((event.target as HTMLInputElement).files?.[0] ?? null)}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={upload.close}>
            Отмена
          </Button>
          <Button type="submit" variant="primary" disabled={upload.isSubmitting}>
            {upload.isSubmitting ? "Загрузка..." : "Сохранить"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
