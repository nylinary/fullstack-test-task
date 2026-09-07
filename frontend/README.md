# Фронтенд

Дашборд файлообменника на Next.js (App Router).

## Слои

Раньше это был один `page.tsx` на 400 строк, в котором лежали типы,
форматирование, маппинг статусов в цвета, вызовы `fetch`, обработка ошибок и
разметка. Теперь всё разбито по [Feature-Sliced Design](https://feature-sliced.design),
и импорты идут строго **вниз**:

```
app/       роутинг Next.js и корневой layout — больше ничего
  ↓
views/     целый экран: files-dashboard (поток данных в model/, вёрстка в ui/)
  ↓
widgets/   самодостаточные блоки: file-table, alert-table
  ↓
features/  пользовательское действие со своим состоянием: upload-file
  ↓
entities/  бизнес-объект: file, alert — его тип, его вызовы API, его правила отображения
  ↓
shared/    переиспользуемое и не знающее о домене: HTTP-клиент, конфиг, форматтеры, UI-примитивы
```

| Слайс | Зона ответственности |
| --- | --- |
| `shared/config/env.ts` | origin API из `NEXT_PUBLIC_API_URL` вместо зашитого в страницу `http://localhost:8000` |
| `shared/api/http.ts` | единственный модуль, который знает, как этот API сообщает об ошибках: проверяет `response.ok`, читает `detail`, бросает `ApiError` |
| `shared/lib/format.ts` | `formatDate`, `formatSize` |
| `shared/ui/` | `DataTable`, `SectionCard`, `AsyncSection`, `StatusBadge` — разметка таблиц, карточек и спиннеров, дублировавшаяся между двумя таблицами |
| `entities/file`, `entities/alert` | типы, вызовы эндпоинтов и маппинг статуса в вариант бейджа |
| `features/upload-file` | `useUploadFile` держит состояние формы и сценарий отправки, `UploadFileModal` его рисует |
| `views/files-dashboard` | `useFilesDashboard` держит загрузку, ошибки и обновление, `FilesDashboard` — только вёрстка |

`@/*` указывает на `src/*` (см. `tsconfig.json`).

## Что изменилось помимо разбиения

- `strict: true` в `tsconfig.json` (было `false`), плюс `noUncheckedIndexedAccess`
  и `noUnusedLocals`.
- Сборка Docker была сломана: она копировала `/app/.env.production` — файл,
  которого нет в репозитории, — поэтому `docker compose build frontend` падал.
- `next: "latest"` и остальные плавающие диапазоны зафиксированы по версиям из
  `package-lock.json`, чтобы сборка была воспроизводимой.
- Иконка ссылалась на `/public/favicon.ico` — такого пути не существует. Next
  раздаёт `public/favicon.ico` сам, теперь так и происходит.
- Ошибки формы загрузки показываются внутри модалки, а не за ней.
- Обработка идёт в фоновом воркере, поэтому только что загруженный файл в момент
  ответа ещё имеет статус `uploaded`. Дашборд теперь тихо опрашивает бэкенд
  (раз в 2 с), пока есть незавершённые файлы, и перестаёт, когда всё
  обработано, — вместо того чтобы оставлять пользователя жать *Обновить*.

## Разработка

```bash
npm install
npm run dev        # http://localhost:3000/test
npm run typecheck
npm run build
```

Нужен Node 20.9+ (Next 16).
