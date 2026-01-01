# Component 2: Page Layout Classification Service

## Purpose

Determine the structural archetype of a page to route it to the correct downstream extraction logic.

## Inputs

* Normalised single‑page image

## Outputs

* Page layout classification
* Confidence score

## Supported Layout Archetypes

There should be a way to add new archetypes as they are discovered.
As a starting point, use the following:

* `SingleAccountDense`
* `MultiAccountSummary`
* `MixedLayout`
* `DenseTransactions`
* `Unknown`

## Confidence

Each archetype should have metrics against which the component can assess whether
the scanned image matches the archetype. These metrics will then be used to
determine an overall confidence score of image-archetype match.

* Confidence scores should be preserved / stored for each archetype, for each pass.
* The 'winning' archetype can be returned as the most likely.

This lets the user answer questions like:

> “Was this page always ambiguous, or did the new model make it worse?”

## Classification

Where a human enters a different classification (overrides), the AI classification
should be retained but the human classification should always be used if present.

When a model is updated / upgraded the image should only be re-classified on when
requested by a user.

## Processing Approach

* Low‑cost AI vision pass or heuristic hybrid
* Features may include:

  * Ink density distribution
  * Presence of large calligraphic headings
  * Count and spacing of ruled lines

## Storage

* Layout classification stored against page ID
  * Used only for routing; may be overridden manually
* Classification model used stored against page ID
