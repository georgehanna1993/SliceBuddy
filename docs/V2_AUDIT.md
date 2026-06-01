# SliceBuddy V2 Audit

## Current Product

SliceBuddy is a useful prototype with a deterministic LangGraph pipeline:

1. Validate that the user provided a meaningful print-planning request.
2. Analyze the uploaded STL.
3. Build a beginner-friendly model overview.
4. Normalize dimensions and description.
5. Ask for environment, purpose, and expected-load context.
6. Recommend material, orientation, slicer settings, and risk mitigations.
7. Produce a structured plan.
8. Optionally enrich the explanation with RAG and an LLM.

The deterministic core is the right product foundation. It makes the planning
logic inspectable and allows the application to work without an external AI
service.

## Stabilization Completed

- Added an offline deterministic explanation path.
- Made LLM and RAG enrichment optional and failure-tolerant.
- Added bounded STL uploads with extension, empty-file, and mesh validation.
- Added a `/health` endpoint and API metadata.
- Added configurable CORS origins, API URL, and upload limit.
- Restored the documented CLI entrypoint.
- Added backend regression tests and GitHub Actions CI.
- Added frontend lint and production build checks.
- Removed the frontend's network-bound Google Fonts build dependency.
- Upgraded Next.js from `16.1.6` to `16.2.6`.
- Added a guided deterministic clarification loop for environment, purpose, and
  expected load.
- Added conservative automotive and safety-critical use warnings.

## Next Priorities

### P1: Planning Accuracy

- Add printer profiles: bed dimensions, maximum Z height, nozzle diameter, and
  supported materials.
- Make the STL unit assumption explicit. STL files are unitless; the current
  analyzer assumes millimeters.
- Evaluate candidate rotations instead of only analyzing the uploaded
  orientation. Current orientation advice is heuristic and does not simulate
  alternative placements.
- Weight overhang analysis by surface area and add bridge-specific checks.
- Add more intent signals such as load direction, visual priority, and preferred
  material. Environment, flexibility, and expected load are now collected.
- Add a confidence level and explain which recommendations are geometry-backed
  versus keyword-backed.

### P1: User Experience

- Add drag-and-drop upload, a model preview, and analysis progress states.
- Persist print plans. The current recent-plans sidebar is session-only, and
  selecting an older title does not restore its previous conversation.
- Add export for a human-readable report and slicer presets.
- Surface assumptions alongside warnings so users can correct incorrect inputs.
- Add a printer-fit result before presenting slicer recommendations.

### P1: Runtime Reliability

- Move STL analysis into a bounded worker job with a timeout. A small but
  pathological mesh can still consume substantial CPU.
- Add structured logs, request IDs, and error monitoring.
- Version the API response with Pydantic models.
- Split required backend packages from optional AI/RAG and development
  dependencies. The current `requirements.txt` is much larger than the offline
  planner needs.
- Add browser automation for a complete upload-to-plan flow.

### P2: Deployment and Security

- Add authentication, rate limiting, and persistent storage before exposing the
  API publicly.
- Add deployment configuration for frontend and backend environments.
- Review and refresh the technical-guide PDF after the v2 API contract settles.
- Track the remaining upstream Next.js/PostCSS advisory and upgrade when a
  compatible fixed Next.js release is available.

## Recommended Delivery Order

1. Printer profiles and explicit STL units.
2. Versioned API models and printer-fit validation.
3. Rotation scoring and confidence-backed recommendations.
4. Persistent plans, model preview, and exports.
5. Worker isolation, observability, and deployment hardening.
