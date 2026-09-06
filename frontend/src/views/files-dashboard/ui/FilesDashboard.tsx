"use client";

import { Alert, Button, Card, Col, Container, Row } from "react-bootstrap";

import { useUploadFile } from "@/features/upload-file/model/useUploadFile";
import { UploadFileModal } from "@/features/upload-file/ui/UploadFileModal";
import { AsyncSection } from "@/shared/ui/AsyncSection";
import { SectionCard } from "@/shared/ui/SectionCard";
import { useFilesDashboard } from "@/views/files-dashboard/model/useFilesDashboard";
import { AlertTable } from "@/widgets/alert-table/ui/AlertTable";
import { FileTable } from "@/widgets/file-table/ui/FileTable";

export function FilesDashboard() {
  const { files, alerts, isLoading, error, refresh, reload } = useFilesDashboard();
  const upload = useUploadFile({ onUploaded: () => reload({ silent: true }) });

  return (
    <Container fluid className="py-4 px-4 bg-light min-vh-100">
      <Row className="justify-content-center">
        <Col xxl={10} xl={11}>
          <Card className="shadow-sm border-0 mb-4">
            <Card.Body className="p-4">
              <div className="d-flex justify-content-between align-items-start gap-3 flex-wrap">
                <div>
                  <h1 className="h3 mb-2">Управление файлами</h1>
                  <p className="text-secondary mb-0">
                    Загрузка файлов, просмотр статусов обработки и ленты алертов.
                  </p>
                </div>
                <div className="d-flex gap-2">
                  <Button variant="outline-secondary" onClick={refresh}>
                    Обновить
                  </Button>
                  <Button variant="primary" onClick={upload.open}>
                    Добавить файл
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>

          {error ? (
            <Alert variant="danger" className="shadow-sm">
              {error}
            </Alert>
          ) : null}

          <SectionCard title="Файлы" count={files.length} className="mb-4">
            <AsyncSection isLoading={isLoading}>
              <FileTable files={files} />
            </AsyncSection>
          </SectionCard>

          <SectionCard title="Алерты" count={alerts.length}>
            <AsyncSection isLoading={isLoading}>
              <AlertTable alerts={alerts} />
            </AsyncSection>
          </SectionCard>
        </Col>
      </Row>

      <UploadFileModal upload={upload} />
    </Container>
  );
}
