# Frontend

Next.js (App Router) dashboard for the file exchange service.

## Layers

The page used to be a single 400-line `page.tsx` holding types, formatting,
status-to-colour mapping, `fetch` calls, error handling and markup. It is now
split along [Feature-Sliced Design](https://feature-sliced.design) lines, with
imports only ever pointing **downwards**:

```
app/       Next.js routing and the root layout - nothing else
  ↓
views/     a whole screen: files-dashboard (data flow in model/, layout in ui/)
  ↓
widgets/   self-contained blocks: file-table, alert-table
  ↓
features/  a user action with its own state: upload-file
  ↓
entities/  a business object: file, alert - its type, its API calls, its display rules
  ↓
shared/    reusable and domain-agnostic: http client, config, formatters, UI primitives
```

| Slice | Responsibility |
| --- | --- |
| `shared/config/env.ts` | the API origin, read from `NEXT_PUBLIC_API_URL` instead of `http://localhost:8000` hard-coded in the page |
| `shared/api/http.ts` | the only module that knows how this API reports failures - checks `response.ok`, reads `detail`, throws `ApiError` |
| `shared/lib/format.ts` | `formatDate`, `formatSize` |
| `shared/ui/` | `DataTable`, `SectionCard`, `AsyncSection`, `StatusBadge` - the table/card/spinner markup that was duplicated between the two tables |
| `entities/file`, `entities/alert` | types, endpoint calls, and the status → badge-variant mapping |
| `features/upload-file` | `useUploadFile` owns the form state and the submit workflow; `UploadFileModal` renders it |
| `views/files-dashboard` | `useFilesDashboard` owns loading, errors and refresh; `FilesDashboard` is layout only |

`@/*` maps to `src/*` (see `tsconfig.json`).

## Changes beyond the split

- `strict: true` in `tsconfig.json` (it was `false`), plus `noUncheckedIndexedAccess`
  and `noUnusedLocals`.
- The Docker build was broken: it copied `/app/.env.production`, a file that is not
  in the repository, so `docker compose build frontend` failed outright.
- `next: "latest"` and the other floating ranges are pinned to the versions in
  `package-lock.json`, so a build is reproducible.
- The favicon pointed at `/public/favicon.ico`, which is not a served path. Next
  serves `public/favicon.ico` itself, and now does.
- Errors from the upload form are shown inside the modal rather than behind it.
- Processing happens in a background worker, so a freshly uploaded file is still
  `uploaded` when the response arrives. The dashboard now polls quietly (2 s)
  while any file is unfinished and stops once everything has settled, instead of
  leaving the user to press *Обновить*.

## Development

```bash
npm install
npm run dev        # http://localhost:3000/test
npm run typecheck
npm run build
```

Requires Node 20.9+ (Next 16).
