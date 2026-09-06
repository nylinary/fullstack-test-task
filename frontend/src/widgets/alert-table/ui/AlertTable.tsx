import { getLevelVariant } from "@/entities/alert/model/level";
import type { AlertItem } from "@/entities/alert/model/types";
import { DataTable } from "@/shared/ui/DataTable";
import { StatusBadge } from "@/shared/ui/StatusBadge";
import { formatDate } from "@/shared/lib/format";

const COLUMNS = ["ID", "File ID", "Уровень", "Сообщение", "Создан"];

export function AlertTable({ alerts }: { alerts: AlertItem[] }) {
  return (
    <DataTable
      columns={COLUMNS}
      rows={alerts}
      emptyMessage="Алертов пока нет"
      renderRow={(alert) => (
        <tr key={alert.id}>
          <td>{alert.id}</td>
          <td className="small">{alert.file_id}</td>
          <td>
            <StatusBadge variant={getLevelVariant(alert.level)}>{alert.level}</StatusBadge>
          </td>
          <td>{alert.message}</td>
          <td>{formatDate(alert.created_at)}</td>
        </tr>
      )}
    />
  );
}
