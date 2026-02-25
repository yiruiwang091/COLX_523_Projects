# Annotation Plan

## Annotation Task Description

The objective of this annotation project is to construct a **fine-grained, attribute-level sentiment resource for product analysis**. By systematically identifying product attributes and associating them with their corresponding sentiment polarity, we aim to enable more precise modeling of consumer opinions beyond overall product-level sentiment. This form of structured annotation supports downstream tasks such as aspect-based sentiment analysis, opinion summarization.

To achieve this objective, annotation will be conducted along two complementary dimensions:

1. **Product Attribute Annotation:** Annotators are required to identify and extract product attributes mentioned in the product metadata (including title and description) as well as in user reviews. Attributes may be explicitly stated (e.g., “battery life,” “material quality”) or implicitly implied through descriptive language. All identifiable attribute mentions should be captured at the mention level, ensuring that each occurrence is annotated in context. The product attribute annotation is designed to be **open-ended**, meaning that annotators are not restricted to a predefined attribute list and may extract attributes that are not explicitly provided in advance. This approach ensures a more comprehensive and faithful coverage of the attributes expressed in the data. If the resulting attribute space becomes overly sparse, clustering techniques may subsequently be applied to group semantically similar attributes for consolidation and analysis.
2. **Sentiment Annotation at the Attribute Level:** For each annotated attribute mention appearing in user reviews, annotators will determine the sentiment polarity expressed toward that specific attribute. Sentiment should be assigned based on the local linguistic context and is categorized according to **predefined polarity labels** (positive, negative, neutral, unknown). The annotation focuses on the relationship between a specific attribute mention and the sentiment expressed toward it.

Attributes for one product may appear across multiple textual sources: product titles, descriptions, and review texts. Annotators must consider cross-textual references when identifying attribute mentions. 

## Annotation Platform and Workflow

To ensure a structured, efficient, and auditable annotation process, we will conduct all annotation tasks using Label Studio. Label Studio provides a flexible interface that supports span-level annotation, relation labeling, and collaborative project management, which are essential for attribute-level and sentiment-relation annotation. The platform also enables version control, quality monitoring, and adjudication workflows, thereby facilitating consistent and transparent data curation.

All annotations will be performed by trained human annotators. Human judgment is central to this task, as identifying implicit attributes and accurately interpreting sentiment polarity often requires contextual understanding and nuanced reasoning beyond rule-based extraction.

## **Annotators**

The annotation will be carried out by four trained human annotators. All annotators meet the following criteria:

- Fluent in the annotation language;
- Familiar with product review texts and their typical linguistic characteristics;
- Have formally agreed to participate in the annotation tasks.

The use of four annotators allows us to compute inter-annotator agreement (IAA) metrics, thereby quantitatively assessing annotation reliability and consistency. Prior to the commencement of formal annotation, all annotators will participate in structured training sessions using sample data. These sessions are designed to ensure a shared understanding of the annotation guidelines, attribute definitions, and sentiment labeling criteria.

Annotators are permitted to use automation-assisted labeling tools, such as large language models (LLMs) or other pre-annotation systems to improve efficiency and consistency. Such tools may provide draft annotations or suggestions. However, these outputs are strictly advisory. Each annotator is required to carefully review, validate, and revise any automatically generated labels as necessary. Final responsibility for annotation accuracy and quality rests entirely with the human annotators, ensuring that all submitted annotations reflect informed human judgment.

## **Annotation Strategy and Annotator Overlap**

### **Annotator Recruitment**

The annotation will be conducted by four human annotators: Yirui, Leah, Freya and Wei. All annotators have formally agreed to participate in the project prior to the start of the annotation process. In accordance with best practices for reliability assessment, we ensure that more than two annotators are involved so that inter-annotator agreement (IAA) can be computed.

Prior to formal annotation, all annotators will complete structured training sessions using pilot data. The purpose of these sessions is to calibrate interpretations of attribute boundaries, implicit attribute mentions, and sentiment polarity assignments, thereby minimizing systematic disagreement.

### **Annotator Overlap and Workload Distribution**

We plan to annotate 1000 reviews in total (randomly drawn from original dataset with uniform distribution). To ensure annotation reliability, each data instance will be annotated by two independent annotators. Inter-annotator agreement will be calculated on the overlapping subset of the data.

| Annotator | Total Reviews Assigned |
| --------- | ---------------------- |
| Yirui     | 500                    |
| Leah      | 500                    |
| Freya     | 500                    |
| Wei       | 500                    |

**Overlap Design:**

- Annotators Yirui and Wei overlap on 250 samples.
- Annotators Leah and Freya overlap on 250 samples.

Under this design, each annotator labels 500 items in total, with 250 of those items overlapping with another annotator. This results in an approximate 50% overlap within each annotator pair. Inter-annotator agreement metrics will be computed on the overlapping subsets to quantitatively evaluate annotation consistency and reliability.

In cases of substantial disagreement, a discussion-based adjudication process will be conducted to determine the final gold-standard label and to identify potential ambiguities in the guidelines.

### **Expected Annotation Volume Before the Next Sprint**

Given the availability of our four recruited annotators and the requirement that each item be annotated by two annotators for inter-annotator agreement calculation, we provide the following feasibility estimate.

We assume that each annotator is willing to spend several hours on annotation tasks during the sprint period. Based on pilot timing, we estimate that annotating one product instance (including attribute extraction and sentiment labeling) takes approximately 1–2 minutes, depending on text length and complexity. Under a conservative estimate of 1.5 minutes per instance, an annotator can complete approximately 40 items per hour.

If each annotator contributes approximately 6–8 hours during the sprint, this corresponds to roughly 240–320 annotated instances per annotator. This volume is considered feasible given our current human resource constraints and the requirement that all annotated items be double-coded for reliability assessment. We will adjust the target upward if annotators progress faster than anticipated.

## **Annotation Schema**

This section describes the formal annotation schema, specifying the units of annotation, label categories, and the procedural steps annotators are expected to follow. The schema is designed to support fine-grained, attribute-level sentiment analysis while maintaining clarity, consistency, and reproducibility.

### **Units of Annotation**

Annotation will be conducted at two interconnected levels:

1. **Attribute Mention Level**
   The basic unit of annotation is an *attribute mention*, defined as a span of text that refers to a specific product characteristic. Attribute mentions may occur in product titles, product descriptions, or user reviews.
   - Mentions may be **explicit** (e.g., “battery life,” “material quality”) or **implicit** (e.g., “lasts all day” implying battery life).
   - Each mention should be annotated as a minimal contiguous span that captures the attribute expression.
   - Repeated mentions of the same attribute within a single review should be annotated separately if they appear in distinct contexts.
2. **Attribute–Sentiment Relation Level**
   For each attribute mention occurring in a user review, annotators will assign a sentiment polarity label reflecting the opinion expressed toward that attribute. This establishes a directed relation between an attribute mention and its corresponding sentiment.

### **Label Categories**

**Attribute Labels (Open-Ended):**
Attribute categories are not restricted to a predefined closed list. Annotators may introduce new attribute types as needed to ensure comprehensive coverage of product characteristics. Later-stage clustering may be applied to consolidate semantically similar attributes.

**Sentiment Polarity Labels:**

Each attribute mention in review text will receive one of the following sentiment labels:

- **Positive** – The attribute is evaluated favorably.
- **Negative** – The attribute is evaluated unfavorably.
- **Neutral** – The attribute is mentioned without clear evaluative polarity.

If no sentiment is expressed toward an attribute (e.g., purely descriptive metadata), no polarity label is assigned.

### **Annotation Procedure**

For each product instance, annotators will proceed as follows:

1. Read the product title and description to identify potential attributes.
2. Annotate all identifiable attribute mentions across metadata and review text.
3. For each attribute mention appearing in a review, determine whether a sentiment is expressed.
4. Assign the appropriate sentiment polarity label where applicable.
5. Review all annotations for consistency before submission.

### **Consistency Guidelines**

- Attribute boundaries should capture only the minimal span necessary to represent the attribute.
- Sentiment assignment must be grounded in explicit contextual evidence within the review text.
- In cases of ambiguity, annotators should rely on guideline definitions established during training and document uncertain cases for later adjudication.
- Provided Prompt for LLM for annotation advisory

```python
'''You are an expert linguistic annotator for fine-grained product attribute and sentiment annotation.

Your task is to perform attribute-level annotation according to the following schema:

ANNOTATION REQUIREMENTS

1. Attribute Mention Level
- Identify all product attribute mentions in:
  (a) product title
  (b) product description
  (c) user review text
- Attributes may be explicit (e.g., "battery life") or implicit (e.g., "lasts all day" → battery life).
- Extract the minimal contiguous text span that expresses the attribute.
- The attribute schema is open-ended. You may introduce new attribute names if necessary.
- Repeated mentions should be annotated separately if they occur in different contexts.

2. Attribute–Sentiment Relation Level
- For each attribute mention appearing in the review text:
    - Determine whether sentiment is expressed toward that attribute.
    - Assign one of the following polarity labels:
        "positive"
        "negative"
        "neutral"
- If no sentiment is expressed, use: null
- Do NOT assign sentiment to attributes that only appear in metadata (title/description).

GUIDELINES

- Sentiment must be grounded in explicit contextual evidence.
- Use minimal span boundaries.
- Avoid hallucinating attributes that are not supported by text.
- Do not infer sentiment beyond what is linguistically expressed.

OUTPUT FORMAT

Return ONLY valid JSON with the following structure:

{
  "product_id": "<id if provided>",
  "annotations": [
    {
      "attribute_mention": "<exact text span>",
      "attribute_category": "<normalized attribute name>",
      "source": "title | description | review",
      "sentiment": "positive | negative | neutral | null"
    }
  ]
}

If no attributes are found, return:
{
  "product_id": "<id if provided>",
  "annotations": []
}

Now annotate the following input:

Product Title:
{TITLE}

Product Description:
{DESCRIPTION}

Review Text:
{REVIEW}
'''
```



This schema ensures that annotation is systematic, transparent, and suitable for quantitative reliability evaluation and downstream modeling tasks.