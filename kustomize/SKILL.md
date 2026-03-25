---
name: kustomize
description: Kustomize patterns for base/overlay resource management. Use when structuring kustomize overlays, patching resources across environments, or refactoring kustomize projects.
user-invocable: false
---

# Kustomize Patterns

Reusable patterns for structuring kustomize base/overlay projects.

## Variants

- **Overlay inline patches**: See [overlay-inline-patches.md](overlay-inline-patches.md)
  When: A resource lives in base with prod values, and lower/dev overlays patch it inline rather than duplicating the file.
