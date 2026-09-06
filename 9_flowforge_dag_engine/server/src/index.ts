import { createApp } from "./app.js";

const PORT = Number(process.env.PORT ?? 8009);

const app = createApp();

app.listen(PORT, () => {
  console.log(`FlowForge DAG engine listening on http://localhost:${PORT}`);
});
