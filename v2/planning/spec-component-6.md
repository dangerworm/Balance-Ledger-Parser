# Component 6: Explorer & Review UI

## Purpose

Provide users with full visibility, control, and authority over the digitisation process.

## Core Features

* Page browser with status indicators
* High‑resolution zoomable page viewer
* SVG overlay for blocks and evidence
* Expose confidence visually, not just numerically.
  * colour saturation on blocks
  * warning icons on suspect totals
  * subtle cues rather than dashboards

## Workflow

1. Select page
2. On page view, associated actions are 'locked'
3. Run Block Bot
4. Review and adjust blocks
5. Run Transcribe Bot
6. Review extracted data
7. View validation results
8. Mark page status:

   * New
   * Processed
   * In Review
   * Reviewed
   * Complete
   * Cursed

### Multiple Users

If ever deployed as a multi-user tool, we should warn the user that the page
is in the process of being reviewed / edited. This could be as simple as checking
the latest timestamp for related actions in the database and returning whether
that time was more than a defined period of, say, 5 minutes ago.

If page is in use, allow viewing but warn that features may be unavailable. When
a feature is called, back end checks either acts or refuses if page had a related action by another user within the defined period.

### Reverting

* Users can revert changes
* This 'rolls back' the last action
  * If results from a previous action exist:
    * Use correlation ID (cID) to find associated records
    * Copies of those records are created with the same data and new cIDs
    * The original records are marked IsSuperseded
    * The UI is updated with the new (i.e. previous) records' data

## Editing Capabilities

* Adjust block boundaries
* Re‑type blocks
* Edit extracted values
* Trigger block‑level reprocessing

## Authority

* Human edits override AI output
* Overrides are stored as canonical truth
