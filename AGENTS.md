# Project Working Rules

These instructions apply to the entire repository.

## Required project orientation

- At the start of every task in this repository, read `README.md`, inspect the current repository structure, and review every project diagram before making changes or drawing conclusions about the implementation.
- Review both diagram sources and rendered assets. This includes every `.puml` file and all architecture, wiring, state-machine, state-transition, and control-flow diagrams. Open rendered image files when necessary; do not rely only on filenames or README descriptions.
- Use the diagrams together with the implementation files to build project context. Treat diagrams as useful context, but verify behavior against the current source code before changing it.

## Keep diagrams synchronized

- Update all affected diagrams in the same change whenever project structure, component responsibilities, hardware wiring, interfaces, data flow, business logic, thresholds, calibration behavior, error handling, recovery behavior, or state-machine logic changes.
- Treat PlantUML source files as the editable source of truth. Keep each affected `.puml` file and its generated `.png` image synchronized and committed together.
- Update README diagram references and explanatory text whenever a diagram is added, removed, renamed, or materially changed.
- Regenerate every affected PNG with PlantUML, validate that each PUML file renders without errors, and visually inspect the generated image for readability and correctness before completing the task.
- Do not consider an architecture or logic change complete while any related diagram is stale. If no diagram update is required, explicitly verify that the existing diagrams still describe the changed behavior accurately.
