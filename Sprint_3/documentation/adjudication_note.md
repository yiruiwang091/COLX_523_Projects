## Adjudication Procedure for Deriving Final Annotations

After both annotators in a pair completed their annotations, we ran an adjudication script `adjudication.py` to produce one final annotation set per review. The goal of adjudication was to generate a single “best final annotation” for each item while applying the same rules consistently across the whole dataset.

### 1. Input structure and annotator handling

The adjudication script operates on the raw annotation export for each pair. Each review appears twice in the input: once for each annotator in that pair. Before adjudication begins, the script applies one correction to the annotator metadata: any annotation recorded under annotator ID `1` is reassigned to annotator `2`. This fixes the known labeling mistake in the original exports and ensures that all records are grouped under the correct annotators.

The script then filters the input so that only the expected annotators for that pair are used in adjudication. This prevents unrelated or incorrectly assigned records from entering the final output.

### 2. Normalization before comparison

Before comparing the two annotators’ work, the script normalizes the annotations so that they can be adjudicated systematically.

Attribute labels are standardized by:

* converting them to lowercase,
* replacing spaces with underscores,
* collapsing repeated underscores.

This ensures that superficially different versions of the same label, such as “Ease of Use” and “ease_of_use”, are treated as identical.

For review text spans, sentiment labels are also normalized to lowercase.

### 3. Annotation units used in adjudication

The script adjudicates annotations separately for three text regions:

* title,
* description,
* review text.

Each annotation is converted into a normalized item consisting of:

* the span start index,
* the span end index,
* the attribute label,
* and, for review text only, the sentiment label.

This means that adjudication is performed at the level of annotated spans, not at the level of the whole review.

### 4. Grouping by review

All annotations are grouped by `review_id`. For each review, the script retrieves the two annotator records and compares their title, description, and review annotations separately.

Within each section, annotations are organized by span `(start, end)`. The adjudication process therefore first asks whether both annotators marked the same character span, and then asks whether they assigned the same label and sentiment to that span.

### 5. When both annotators agree

If both annotators marked the same span and assigned at least one matching attribute label to it, that shared label is preserved in the final annotation.

For review text spans, if both annotators also assigned the same sentiment to that shared label, the shared sentiment is kept directly.

This is the simplest case: exact overlap in span and agreement in label results in the annotation being carried over unchanged to the adjudicated output.

### 6. When the span appears in only one annotation

If a span appears in only one annotator’s record and not in the other’s, the script keeps that annotation in the final output. In other words, the adjudication uses a union strategy for one-sided spans rather than dropping them.

This choice is meant to preserve potentially useful information rather than losing it simply because the second annotator did not mark the same span. These cases are still logged as disagreement cases, but the annotation itself is retained.

### 7. When both annotators marked the same span but chose different labels

If both annotators selected the same span but assigned different attribute labels, the script resolves the conflict deterministically using a sequence of tie-breaking rules.

#### Rule 1: Prefer more specific labels over generic ones

Some labels are treated as overly broad or generic, including:
`design`, `overall`, `performance`.

If one annotator chose a generic label and the other chose a more specific label for the same span, the more specific label is selected. This rule is intended to make the final corpus more semantically informative and useful for downstream modeling.

#### Rule 2: Prefer the label that appears more often in the pair’s data

If neither label is generic, or both are equally generic/non-generic, the script compares how often each label appears across the pair’s annotations overall. The more frequent label is chosen.

This acts as a corpus-level prior: if one label is more commonly used across the annotations, it is treated as the more likely intended category.

#### Rule 3: Prefer the longer label name

If the two labels are still tied after frequency comparison, the script chooses the label with the longer string length. This again tends to favor more specific labels over shorter, more general ones.

#### Rule 4: Lexicographic tie-break

If the labels are still tied after all previous checks, the script resolves the conflict alphabetically. This is simply a deterministic final fallback so that the same input always produces the same result.

### 8. How sentiment disagreements are resolved

Sentiment adjudication applies only to review text annotations. When two annotators agree on the attribute label for a span but disagree on the sentiment, the script resolves the disagreement using another deterministic sequence.

#### Case 1: One side is missing

If one annotator provided a sentiment and the other did not, the available sentiment is kept.

#### Case 2: Prefer non-unknown over unknown

If one sentiment is `unknown` and the other is a defined sentiment such as `positive`, `negative`, or `neutral`, the non-unknown value is selected.

#### Case 3: Prefer polar sentiment over neutral

If one annotator chose `neutral` and the other chose a polar sentiment (`positive` or `negative`), the script keeps the polar sentiment. This reflects the assumption that a more directional judgment is more informative than a neutral one when the two conflict.

#### Case 4: Remaining unresolved conflicts become unknown

If the conflict cannot be resolved by any of the above rules, the final sentiment is set to `unknown`.

This ensures that unresolved disagreements are not forced into a potentially misleading polarity label.

### 9. Ordering and output format

After adjudication, the selected annotations are sorted by span start, span end, and label so that the output is stable and reproducible. The script then reconstructs the final annotation fields for each review:

* span locations,
* attribute labels,
* and sentiment values where applicable.

If enabled, it also fills in the text substring corresponding to each span by slicing the original title, description, or review text. This makes the adjudicated output easier to inspect manually.

The final outputs include:

* a JSON file of adjudicated annotations,
* a JSONL version of the same data,
* and a CSV conflict log.

### 10. Conflict logging and transparency

The adjudication script logs disagreement cases so that the process remains transparent. Three main types of cases are recorded:

* `label_conflict`: both annotators marked the same span but used different labels,
* `sentiment_conflict`: both annotators agreed on the span and label but differed in sentiment,
* `span_only_one_annotator`: only one annotator marked the span.

For each logged case, the script records the competing values, the final chosen value, and the rule used to resolve the disagreement. This makes the adjudication process auditable and reproducible.

### 11. Overall adjudication philosophy

The adjudication strategy is designed to balance three goals.

First, it preserves agreement directly whenever possible. If both annotators independently selected the same information, that annotation is retained with minimal intervention.

Second, it avoids unnecessary data loss. When only one annotator marked a span, the annotation is usually kept rather than discarded.

Third, when disagreements occur, the script applies deterministic and interpretable rules that favor specificity, consistency, and informativeness. This makes the final dataset reproducible and suitable for downstream analysis, while still reflecting the kinds of disagreements that arose during human annotation.

### 12. Summary

In summary, the final adjudicated annotation for each review is produced by comparing the two annotators’ span-level annotations, preserving exact agreement, keeping one-sided spans, and resolving conflicts through fixed tie-breaking rules. Label conflicts are resolved by preferring non-generic, more frequent, and more specific labels, while sentiment conflicts are resolved by preferring defined and more informative sentiment values. Because all decisions are rule-based and logged, the adjudication process is fully reproducible and transparent.
