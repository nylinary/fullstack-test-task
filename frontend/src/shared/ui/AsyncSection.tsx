import { Spinner } from "react-bootstrap";

/** Renders a spinner while loading, otherwise the children. */
export function AsyncSection({ isLoading, children }: { isLoading: boolean; children: React.ReactNode }) {
  if (isLoading) {
    return (
      <div className="d-flex justify-content-center py-5">
        <Spinner animation="border" />
      </div>
    );
  }

  return <>{children}</>;
}
