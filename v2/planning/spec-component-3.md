# Component 3: Block Segmentation & Structural Analysis ("Block Bot")

## Purpose

Segment a page into meaningful structural blocks and identify relationships between them.

## Inputs

* Normalised page image
* Page layout classification

## Outputs

* Set of block images
* Block metadata
* Block relationship graph

## Block Types (Initial Set)

* AccountTitle
* TableBody
* TableHeader
* SubtotalOrTotal
* BalanceForward
* ClosingStroke
* NotesOrMarginalia
* Unknown

## Processing Steps

1. **Block Detection**

   * Identify candidate regions based on layout
   * Use ruled lines, whitespace, and text density

2. **Geometry Capture**

   * Store block geometry as polygons (not just rectangles)
   * Blocks are allowed to overlap (ambiguous overlaps over premature split)

3. **Block Typing**

   * Assign block type with confidence

4. **Relationship Inference**

   * Create directed links such as:

     * Title → Table
     * Table → Subtotal
     * Debit ↔ Credit (paired accounts)
     * Continuation / carry‑forward

## Storage

For each block:

* Block ID
* Page ID
* Polygon coordinates
* Block type
* Confidence
* References to source images

For relationships:

* From block ID
* To block ID
* Relationship type

## Human Interaction

* Blocks are editable in UI
* Users may split, merge, re‑type blocks
