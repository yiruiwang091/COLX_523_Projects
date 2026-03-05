---
editor_options: 
  markdown: 
    wrap: 72
---

# Adjudication Notes

This document summarizes how we converted two-annotator outputs into a
single final annotation set (**500 reviews per pair**) and how
disagreements were resolved.

## Inputs / outputs

-   **Inputs:** paired annotation JSON files (one record per annotator
    per review).
-   **Outputs:** one adjudicated file per pair (500 reviews), plus a
    conflict log used for auditing.

## Pre-processing / normalization

Before comparing or merging annotations, we normalized labels and
cleaned known edge cases:

### 1) Label normalization

-   Stripped leading/trailing whitespace (e.g., `"brand "` → `"brand"`).
-   Lowercased labels and normalized spacing to underscores when needed.

### 2) Remove excluded labels

-   Removed the attribute labels `brand` and `product_type` (and their
    corresponding spans) from **all sections**.

### 3) Fix malformed structures (rare)

-   In a small number of cases, a span-like dict appeared inside
    `*_attr_name`.
-   We treated this as a formatting error and moved the `start/end` info
    to `*_attr_span`, while keeping the label text in `*_attr_name`
    before adjudication.

## What counts as an “item”

For each section (title / description / review), we treat each
annotation as:

-   a span defined by `(start, end)`, paired with
-   an attribute label
-   **(review spans only)** a sentiment value aligned to the span

## Merge strategy

We use a **union-based merge** with conflict resolution:

### Same span, same label (agreement)

-   Keep the annotation.
-   For review spans, if sentiments differ, apply the sentiment rule
    below.

### Same span, different label (label conflict)

-   Choose one label using the tie-break rules below.

### Span appears in only one annotator’s file

-   Keep it (union). This preserves coverage and avoids dropping valid
    mentions.

## Tie-break rules for label conflicts

When two annotators assign different labels to the same span, we select
a single label using:

### Prefer more specific labels over generic ones

-   If one label is generic (e.g., `design`, `quality`, `performance`)
    and the other is more specific, choose the more specific one.

### Prefer labels that are more consistent globally

-   If both are similarly specific, choose the label that appears more
    frequently in the dataset (as a proxy for consistent team usage).

### Stable fallback

-   If still tied, choose the longer / more specific label name; if
    still tied, use a deterministic alphabetical tie-break.

## Sentiment resolution (review spans only)

Sentiment is only recorded for spans in the **review text**.

If sentiments disagree: - Prefer a non-`unknown` value over `unknown`. -
Prefer `positive`/`negative` over `neutral` when one annotator is
neutral and the other is polar. - Otherwise set to `unknown`
(conservative default).

## Auditing

We export a conflict log that records: - label conflicts, - sentiment
conflicts, - spans present in only one annotator, - missing second
annotator (if applicable).

This log was used to sanity-check adjudication and to support
reproducibility.
