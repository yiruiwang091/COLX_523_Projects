# Inter-Annotator Agreement (IAA) Analysis

## Evaluation Method

To assess the reliability and consistency of the annotations, we computed **Inter-Annotator Agreement (IAA)** between the two annotators for each review instance. The dataset contains span-level annotations identifying product attributes in both **product descriptions** and **user reviews**.

For each `review_id`, annotations from two annotators were compared using span matching and label agreement metrics.

### Span Matching

Each attribute mention is annotated as a **text span** with a start and end index. To determine whether two spans from different annotators refer to the same attribute mention, we used **Intersection over Union (IoU)** between spans:

IoU = Intersection(span_1, span_2)\Union(span_1, span_2)

 A pair of spans is considered a **match** if:

IoU > 0.5

This threshold allows small boundary differences while still capturing agreement on the same semantic span.

Matched spans are used to compute **Precision**, **Recall**, and **F1 score**.

### Span-Level Metrics

Let:

- **TP (True Positives)** = matched spans between annotators
- **|A|** = number of spans annotated by annotator A
- **|B|** = number of spans annotated by annotator B

The metrics are computed as:

**Precision**:
Precision = Matched spans / Predicted spans

Measures how many spans annotated by annotator A are also identified by annotator B.

**Recall**:

Recall = Matched spans / Gold spans 

Measures how many spans annotated by annotator B are also identified by annotator A.

**F1 Score**:

F1 = 2 * Precision * Recall / (Precision + Recall) 

F1 summarizes the overall span agreement between annotators.

### Label Agreement

After identifying matched spans, we evaluate whether the **attribute labels assigned to the spans are the same**.

Label agreement is computed as:

LabelAgreement = Matched spans with identical labels / Total matched spans

This metric evaluates whether annotators agree not only on **where the attribute is mentioned**, but also **what attribute category it represents**.

## Results

### Description Attribute Annotation

|     Metric      | Score |
| :-------------: | :---: |
|    Precision    | 0.899 |
|     Recall      | 0.890 |
|       F1        | 0.891 |
| Label Agreement | 0.669 |

### Review Attribute Annotation

|     Metric      | Score |
| :-------------: | :---: |
|    Precision    | 0.959 |
|     Recall      | 0.958 |
|       F1        | 0.957 |
| Label Agreement | 0.614 |

## Interpretation

### Span Identification Agreement

The **span-level agreement is very high** for both annotation tasks.

- Description attribute **F1 = 0.891**
- Review attribute **F1 = 0.957**

These results indicate that annotators generally agree on **where attribute mentions appear in the text**.

The agreement is **higher for reviews** than for descriptions. One possible explanation is that:

- Review texts often contain **clear and direct opinions about product features** (e.g., "easy to set up", "very portable"), making attribute spans easier to identify.
- Product descriptions may contain **longer, more complex sentences with multiple features**, which can lead to slight differences in span boundaries.

Overall, span-level F1 scores above **0.85** indicate **strong annotation consistency**.

------

### Label Agreement

While span agreement is high, **label agreement is lower**:

- Description label agreement: **0.669**
- Review label agreement: **0.614**

This indicates that annotators frequently agree on **the text span**, but sometimes assign **different attribute categories**.

Several factors may explain this pattern:

#### Attribute category ambiguity

Some attribute mentions may belong to multiple plausible categories.

Example:

```
"easy to set up in five minutes"
```

This span could be labeled as:

- **ease_of_use**
- **setup_time**

Different annotators may interpret such phrases differently.

------

#### Overlapping attribute semantics

Certain attributes in the schema are conceptually related:

- **stability**
- **durability**
- **wind resistance**

This semantic overlap can lead to disagreements even when annotators identify the same span.

------

#### Description complexity

Product descriptions often list **multiple features in a single sentence**, increasing the difficulty of deciding which attribute category best fits a span.

------

### Overall Dataset Reliability

Despite moderate label disagreement, the dataset shows **strong overall annotation reliability**.

Key observations:

- Span detection agreement is **very high (F1 > 0.89)**.
- Annotators consistently identify the same attribute mentions.
- Label disagreement mainly arises from **category interpretation**, rather than span detection.

This suggests that the annotation guidelines are generally effective, but **attribute category boundaries could potentially be clarified** to further improve label consistency.

------

## Summary

The inter-annotator agreement analysis shows that:

- Annotators strongly agree on **where attribute mentions occur in text**.
- Label assignment shows **moderate agreement**, likely due to semantic overlap between attribute categories.
- Overall, the dataset demonstrates **high reliability for span-level attribute extraction tasks**.

These results indicate that the annotated dataset is suitable for training and evaluating models for **attribute extraction and sentiment analysis in product reviews and descriptions**.