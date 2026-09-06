import { Button } from "react-bootstrap";

import { downloadUrl } from "@/entities/file/api/fileApi";
import { getProcessingVariant, getScanVariant } from "@/entities/file/model/status";
import type { FileItem } from "@/entities/file/model/types";
import { DataTable } from "@/shared/ui/DataTable";
import { StatusBadge } from "@/shared/ui/StatusBadge";
import { formatDate, formatSize } from "@/shared/lib/format";

const COLUMNS = ["Название", "Файл", "MIME", "Размер", "Статус", "Проверка", "Создан", ""];

export function FileTable({ files }: { files: FileItem[] }) {
  return (
    <DataTable
      columns={COLUMNS}
      rows={files}
      emptyMessage="Файлы пока не загружены"
      renderRow={(file) => (
        <tr key={file.id}>
          <td>
            <div className="fw-semibold">{file.title}</div>
            <div className="small text-secondary">{file.id}</div>
          </td>
          <td>{file.original_name}</td>
          <td>{file.mime_type}</td>
          <td>{formatSize(file.size)}</td>
          <td>
            <StatusBadge variant={getProcessingVariant(file.processing_status)}>
              {file.processing_status}
            </StatusBadge>
          </td>
          <td>
            <div className="d-flex flex-column gap-1">
              <StatusBadge variant={getScanVariant(file)}>{file.scan_status ?? "pending"}</StatusBadge>
              <span className="small text-secondary">{file.scan_details ?? "Ожидает обработки"}</span>
            </div>
          </td>
          <td>{formatDate(file.created_at)}</td>
          <td className="text-nowrap">
            <Button as="a" href={downloadUrl(file.id)} variant="outline-primary" size="sm">
              Скачать
            </Button>
          </td>
        </tr>
      )}
    />
  );
}
