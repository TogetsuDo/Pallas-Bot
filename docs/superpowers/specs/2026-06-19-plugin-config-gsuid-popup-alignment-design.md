# Plugin Config GSUID Popup Alignment

## Scope

This change only aligns the plugin config item list, help popups, and edit popups in `PluginConfigWorkspace` with the interaction shape used by `gsuid_hub`.

Out of scope:

- runtime control panel
- command permission matrix
- command cooldown editor
- plugin governance API or backend field model
- page-level masthead, tabs, or plugin catalog layout

## Goals

1. Make each config item read as a compact row/card instead of an inline form block.
2. Separate "view help" from "edit value" clearly.
3. Make the edit popup feel lightweight and focused, closer to `gsuid_hub` popover/dialog usage.
4. Preserve the existing Pallas config data flow and field renderer behavior.
5. Keep mobile behavior usable at `<=560px`.

## Target Interaction

### Config Item List

Each config item shows:

- config name
- optional short summary
- current value summary
- `?` help trigger

The main value area is clickable and opens the edit popup.
The `?` button only opens help content and never edits.

### Help Popup

The help popup is a compact informational surface anchored near the trigger.

It shows:

- config display name
- description
- type label
- default value
- env key

It should feel smaller and lighter than the current generic modal treatment.

### Edit Popup

The edit popup is a focused lightweight panel:

- title: config name
- optional one-line description
- field renderer body
- compact action row with confirm/cancel

JSON fields keep the current editing capability, but the popup chrome should visually match the rest of the config-item editing experience.

## Visual Direction

The popup surfaces should move closer to `gsuid_hub` in feel:

- tighter padding
- smaller and cleaner header
- less "full generic modal" feeling
- stronger separation between info popup and edit popup
- compact chips/meta instead of large supporting blocks

The list itself should remain grouped by current Pallas groups, but the inner item presentation should prioritize:

- name
- current value
- direct edit affordance

over verbose inline metadata.

## Implementation Plan

### Files

Primary:

- `Pallas-Bot-WebUI/src/components/PluginConfigWorkspace.vue`
- `Pallas-Bot-WebUI/src/utils/pluginConfigWorkspaceModel.ts`

Possible minor support updates if needed:

- `Pallas-Bot-WebUI/src/components/config/ConfigFieldRenderer.vue`
- `Pallas-Bot-WebUI/src/components/JsonTextareaField.vue`

### Expected Changes

1. Refine config item card layout to read as GSUID-style rows/cards.
2. Refine help popup sizing and meta layout.
3. Refine edit popup shell and action area.
4. Keep existing field rendering logic and backend request flow unchanged.
5. Adjust mobile popup sizing/positioning for narrow screens.

## Verification

Frontend verification:

- `npm run build`

Manual behavior to inspect:

- clicking `?` only opens help
- clicking value area opens editor
- confirm updates local draft value correctly
- JSON editor still works
- mobile width layout remains operable

## Risks

1. Over-styling the popup could regress JSON editing affordances.
2. Changing item density too aggressively could reduce readability for long descriptions.
3. Mobile popup positioning must avoid clipping or off-screen placement.

## Chosen Constraints

1. No backend contract changes.
2. No route or tab restructuring.
3. No governance panel redesign in this task.
