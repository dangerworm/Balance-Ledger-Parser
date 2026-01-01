# Component 5: Validation & Consistency Engine

## Purpose

Detect likely transcription or arithmetic errors using accounting constraints.

> Validation rules may contradict historical reality and must therefore be advisory
> only. This protects future users from assuming “the system says this is wrong,
> therefore it is wrong”, which is a subtle but real danger in historical datasets.

## Validation Tiers

1. **In‑Block Validation**

   * Line totals vs subtotals
   * Debit/credit column consistency

2. **In‑Page Validation**

   * Account title proximity
   * Presence of closing strokes

3. **Cross‑Page Validation (Deferred)**

   * Balance forward / carry forward logic
   * Account state continuity
   * Uses 'bridge' data from component 1
     * Some pages have debit on the left and credit on the right
     * These pages' subtotals must still match

## Outputs

* Validation flags
* Severity levels
* Suggested review targets

## Future Development

It will be hugely beneficial if rules are configurable by users.

* **Pros**
  * Prevents need for re-deployment whenever a rule is added

* **Cons / Reason for leaving as future development**
  * Extremely difficult to create a meaningful way for them to do this

## Non‑Goals

* No automatic correction
* No historical reinterpretation
