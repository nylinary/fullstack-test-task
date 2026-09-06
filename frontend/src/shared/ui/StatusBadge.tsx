import { Badge } from "react-bootstrap";

export type BadgeVariant = "primary" | "secondary" | "success" | "danger" | "warning" | "info";

export function StatusBadge({ variant, children }: { variant: BadgeVariant; children: React.ReactNode }) {
  return <Badge bg={variant}>{children}</Badge>;
}
