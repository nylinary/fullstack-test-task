import { Badge, Card } from "react-bootstrap";

type Props = {
  title: string;
  count?: number;
  children: React.ReactNode;
  className?: string;
};

export function SectionCard({ title, count, children, className }: Props) {
  return (
    <Card className={`shadow-sm border-0 ${className ?? ""}`}>
      <Card.Header className="bg-white border-0 pt-4 px-4">
        <div className="d-flex justify-content-between align-items-center">
          <h2 className="h5 mb-0">{title}</h2>
          {count !== undefined ? <Badge bg="secondary">{count}</Badge> : null}
        </div>
      </Card.Header>
      <Card.Body className="px-4 pb-4">{children}</Card.Body>
    </Card>
  );
}
