import { Router } from "express";
import { validatePipelineGraph } from "../graph/validate.js";

export function createGraphRouter(): Router {
  const router = Router();

  /** POST /api/validate — check schema + acyclicity (Kahn). */
  router.post("/validate", (req, res) => {
    const result = validatePipelineGraph(req.body);
    const status = result.valid ? 200 : 400;
    res.status(status).json(result);
  });

  return router;
}
