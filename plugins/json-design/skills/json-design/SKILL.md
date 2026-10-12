---
name: json-design
description: Design or review JSON payload contracts and JSON Schemas. Use for defining or evolving data exchanged between producers and consumers, including schema validation and compatibility review.
---

# JSON design

Preserve existing dialects, naming, wire formats, and consumer expectations. Apply the defaults below to new contracts you control; identify compatibility implications before changing an established contract. Apply schema guidance to schemas and payload guidance to payloads.

## Schema authoring

- Declare `$schema` and `title`; default new schemas to Draft 2020-12 when the validator supports it. Add a stable `$id` for published schemas.
- Close fixed-shape objects with `additionalProperties: false`. For composed objects, use `unevaluatedProperties: false` at the composition boundary when the dialect and validator support it; keep reusable component schemas open for extension. Model intentional maps or extension points explicitly.
- Declare types and required fields. Constrain values with meaningful bounds, patterns, and closed-set enums. Treat `format` as advisory unless the validator is configured to assert it.
- Reuse sub-schemas with `$defs` and `$ref`, using the equivalent keywords supported by an existing dialect.
- Describe every property; add examples for values whose meaning or representation is unclear.

## Payload design

- Use one naming style, defaulting to `snake_case`. Keep structure flat unless nesting expresses a parent-child relationship. Prefer arrays of objects for record collections; use maps when keyed lookup is part of the contract.
- Use ISO 8601 UTC timestamps, string IDs, integer minor units or decimal strings for money, and descriptive lowercase `snake_case` string enums.
- Document one absence convention: omit optional fields or represent absence with `null` and allow it in the schema. Give omission and `null` distinct documented meanings only when the domain requires both.
- Version contracts you control with an integer `version` or a versioned schema `$id`. Check compatibility against actual producers and consumers: field additions can break closed-schema consumers, and new required fields or tighter constraints can reject existing payloads. Coordinate a version change for breaking changes.
- Give errors a stable `code`, human-readable `message`, and optional `details`. Consumers branch on the code.

## Output and verification

- Emit strict JSON with 2-space indentation, UTF-8, and a trailing newline. Use JSONC only where the consuming tool documents support for it.
- Parse emitted JSON and, when a schema is available, validate representative accepted and rejected instances with the consuming validator. Cover required fields, unknown properties, constraints, and absence semantics. Distinguish checks actually run from compatibility assumptions and unavailable validation.
