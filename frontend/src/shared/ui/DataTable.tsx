import { Table } from "react-bootstrap";

type Props<T> = {
  columns: string[];
  rows: T[];
  emptyMessage: string;
  renderRow: (row: T) => React.ReactNode;
};

export function DataTable<T>({ columns, rows, emptyMessage, renderRow }: Props<T>) {
  return (
    <div className="table-responsive">
      <Table hover bordered className="align-middle mb-0">
        <thead className="table-light">
          <tr>
            {columns.map((column, index) => (
              <th key={`${column}-${index}`}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-4 text-secondary">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            rows.map(renderRow)
          )}
        </tbody>
      </Table>
    </div>
  );
}
