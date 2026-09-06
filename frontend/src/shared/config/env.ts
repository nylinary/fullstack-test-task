/**
 * Runtime configuration.
 *
 * The API origin used to be hard-coded in the page component, which made the
 * app impossible to deploy anywhere but a developer's laptop.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ?? "http://localhost:8000";

/** How often the dashboard re-checks files that are still being processed. */
export const PROCESSING_POLL_INTERVAL_MS = 2000;
