# Design System Specification: The Intelligence Protocol

## 1. Overview & Creative North Star
**Creative North Star: "The Digital Panopticon"**
This design system is built to convey absolute authority, surgical precision, and the weight of high-stakes intelligence. It moves beyond the "friendly SaaS" aesthetic into a realm of technical brutalism—where information density is a feature, not a flaw. 

The system breaks the standard "grid of boxes" by utilizing **Intentional Asymmetry** and **Detective Board Logic**. Elements are connected via structural nodes and "Ghost Lines," mimicking a high-fidelity investigative workspace. It is designed to feel like a redacted document coming to light: dark, layered, and profoundly intentional.

---

## 2. Colors: Tonal Depth & Tactical Accents
The palette is rooted in the "Midnight" spectrum, using deep charcoals to minimize eye strain during long-form data analysis.

### The "No-Line" Rule
Traditional 1px solid borders are strictly prohibited for sectioning. Boundaries must be defined through:
- **Background Shifts:** Placing a `surface-container-low` (#191C1F) element against a `surface` (#111417) backdrop.
- **Luminance Steps:** Using tonal transitions to imply a change in context rather than a physical stroke.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical "intel folders" stacked on a dark desk.
*   **Base:** `surface` (#111417)
*   **The "Work Desk":** `surface-container-low` (#191C1F) for large content areas.
*   **The "Pinned Document":** `surface-container-high` (#272A2D) for active cards.
*   **The "Analyst Focus":** `surface-bright` (#37393D) for hover states or high-priority modules.

### Signature Textures & Accents
*   **The "Glow" Token:** Use `primary` (#A7C8FF) with a 15% opacity drop-shadow (blur: 12px) to signify "Live" data points.
*   **The Crimson Alert:** Use `tertiary-container` (#FF544E) for critical failures or "Unverified" intelligence.
*   **Tactical Glass:** For floating command bars, use `surface-container-highest` (#323538) at 70% opacity with a `20px` backdrop-blur.

---

## 3. Typography: Technical Authority
We use a dual-font strategy to balance editorial impact with technical legibility.

*   **Display & Headlines (`Space Grotesk`):** This is our "Editorial Voice." It should be used for high-level summaries and data headers. It feels modern, slightly eccentric, and authoritative. 
    *   *Scale Example:* `display-lg` (3.5rem) should be used for singular, impactful metrics.
*   **Body & Labels (`Inter`):** This is our "Intelligence Voice." Use this for all dense data, analytical descriptions, and system logs.
    *   *Scale Example:* `label-sm` (0.6875rem) in all-caps with 0.05rem letter-spacing is the standard for metadata and timestamps.

---

## 4. Elevation & Depth: Tonal Layering
We reject traditional shadows in favor of **Luminance Stacking**.

*   **The Layering Principle:** To lift a card, do not add a shadow. Instead, increase the surface tier. A `surface-container-highest` card sitting on a `surface-container-low` background creates a natural, "sharp" lift.
*   **Ambient Shadows:** If a "floating" element (like a modal) is required, use a tinted shadow: `rgba(0, 0, 0, 0.6)` with a `40px` blur and `0px` offset.
*   **The "Ghost Border" Fallback:** If accessibility requires a container boundary, use `outline-variant` (#414752) at **15% opacity**. It should be felt, not seen.

---

## 5. Components: Tactical Modules

### The Truthfulness Rose (Signature Component)
A multi-axis radar chart inspired by CliftonStrengths.
*   **Style:** Sharp vertices (0px radius).
*   **Fill:** `primary-container` (#4491F4) at 20% opacity.
*   **Stroke:** `primary` (#A7C8FF) at 1px.
*   **Nodes:** Each vertex features a 4px square node that glows on hover.

### Buttons & Inputs
*   **Primary Button:** `surface-bright` background, `on-surface` text, 0px border radius. Hover state: `primary-container` background with a subtle cyan outer glow.
*   **Tactical Inputs:** Bottom-border only (Ghost Border style). Focus state: The entire background shifts to `surface-container-highest`.
*   **Cards:** No dividers. Use `Spacing 12` (2.75rem) to separate internal card sections.

### Detective Board Elements (Connectors)
*   **Nodes:** 6px x 6px squares (Color: `secondary`).
*   **Lines:** 1px width, `outline-variant` (#414752). Use 45-degree angles only for a "schematic" feel.

---

## 6. Do's and Don'ts

### Do
*   **DO** use sharp corners (`0px`) for everything. Roundness suggests consumer-grade softness; sharpness suggests professional-grade precision.
*   **DO** use monospacing for all numerical data and timestamps (using `Inter` or a system mono fallback).
*   **DO** leave immense "Negative Space." High-density data requires large gutters (`Spacing 20` or `24`) to remain readable.

### Don't
*   **DON'T** use 100% white (#FFFFFF) for body text. Use `on-surface-variant` (#C1C6D5) to reduce glare.
*   **DON'T** use standard "Drop Shadows." They muddy the technical clarity of the interface.
*   **DON'T** use "Success Green." Use `primary` (#A7C8FF) for "Active/Healthy" and `tertiary` (#FFB3AD) for "Critical." The system is about intelligence, not traffic lights.

---

## 7. Spacing Logic
The spacing scale is aggressive. Use `Spacing 2` (0.4rem) for tight technical groupings (labels to values) and `Spacing 16` (3.5rem) for major section shifts. This "tight-wide" juxtaposition creates the editorial, high-end feel of an intelligence dossier.
