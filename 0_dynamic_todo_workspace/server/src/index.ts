import { createApp } from "./app.js";
import { createRepository, type StorageDriver } from "./repository/index.js";

const PORT = Number(process.env.PORT ?? 8000);
const STORAGE = (process.env.STORAGE ?? "memory") as StorageDriver;

const repo = createRepository(STORAGE);
const app = createApp(repo);

app.listen(PORT, () => {
  console.log(`Dynamic Todo API listening on http://localhost:${PORT}`);
  console.log(`Storage driver: ${STORAGE}`);
  console.log(`SSE stream: GET /api/events`);
});
