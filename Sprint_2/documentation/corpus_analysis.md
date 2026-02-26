# Corpus Analysis: Coleman Sports & Outdoors Reviews

## Corpus overview

Our processed corpus contains **31,349 reviews** about Coleman products from the Amazon Sports & Outdoors domain. The analysis below uses **reviewText only** (not title/description).

### Size + token statistics

* **Documents (reviews):** 31,349
* **Tokens:** 1,741,632
* **Types (unique word forms):** 21,539
* **Average word length:** 4.07 characters
* **Average review length:** 55.56 tokens
* **Median review length:** 28 tokens
* **TTR (10,000 tokens):** 0.1755

**Interpretation:** The large gap between mean (55.6) and median (28) suggests a **right-skewed distribution**: many short reviews plus a smaller number of very long reviews (e.g., detailed complaint narratives / multi-update posts).

---

## Lexical diversity comparison (TTR) vs reference corpora

We computed **type-token ratio (TTR)** over the first 10,000 tokens for comparability across corpora:

| Corpus              |    Tokens |  Types | Avg word length |        TTR |
| ------------------- | --------: | -----: | --------------: | ---------: |
| **coleman_reviews** | 1,741,632 | 21,539 |            4.07 | **0.1755** |
| brown               | 1,161,192 | 49,815 |            4.28 |     0.2507 |
| treebank            |   100,676 | 11,387 |            4.41 |     0.2580 |
| reuters             | 1,720,901 | 31,078 |            4.00 |     0.2142 |
| webtext             |   396,733 | 17,414 |            3.55 |     0.1767 |
| movie_reviews       | 1,583,820 | 39,768 |            3.93 |     0.2554 |

### What this tells us

* **Coleman reviews (0.1755)** are **much less lexically diverse** than *Brown*, *Treebank*, *Reuters*, and *Movie Reviews*.
  This is expected for a **domain-specific product review corpus**, where many reviews repeat similar vocabulary (e.g., “tent”, “cooler”, “stove”, “leak”, “durable”, “easy”, etc.).

* Coleman’s TTR is **very close to WebText** (0.1767).
  This suggests that (at least at the 10k-token slice) our review language has similar diversity to “web conversational text,” though the topic distribution is far narrower.

**Conclusion:** our corpus has **moderate** lexical diversity for its size, consistent with being a specialized review dataset; this is desirable for training attribute-level sentiment models because vocabulary is relatively stable and tied to a coherent domain.

---

## Ratings distribution

| Rating | # Reviews |
| -----: | --------: |
|      1 |     1,439 |
|      2 |     1,144 |
|      3 |     2,530 |
|      4 |     6,114 |
|      5 |    20,122 |

**Interpretation:** The corpus is **strongly positive-skewed** (5-star reviews dominate). This is common in consumer review datasets, but it matters for modeling and annotation because negative examples are rarer.

Practical consequence for annotation/modeling:

* We should **ensure enough negative coverage** during annotation (e.g., ensure balanced annotation batches).

---

## Review length vs rating (metadata interaction)

### Review length by rating

| Rating | Mean tokens | Median tokens |   Std |
| -----: | ----------: | ------------: | ----: |
|      1 |        71.0 |            44 |  90.7 |
|      2 |        78.4 |            46 | 100.3 |
|      3 |        74.8 |            44 | 101.1 |
|      4 |        72.1 |            38 | 111.0 |
|      5 |        45.7 |            23 |  76.9 |

And the overall correlation:

* **Pearson corr(overall, review_len_tokens) = -0.1217**

### Interpretation

* The negative correlation (≈ **-0.12**) is **small but worth noting**: higher ratings tend to be **shorter** reviews.
* 5-star reviews have much shorter typical length (median **23 tokens**) than 1–3 star reviews (median **44–46 tokens**).

This might imply a pattern: satisfied customers often write brief praise (“works great”), while dissatisfied customers explain failure modes, usage context, and troubleshooting, resulting in longer reviews.

Practical consequence for attribute-level annotation:

* Short 5-star reviews may contain **fewer explicit attribute mentions** (sometimes just generic positivity).
* Longer low-star reviews often contain **multiple attributes** and complex narratives, which can be rich for annotation but also increases annotation time.


---

## Summary of key takeaways

1. **Corpus size is robust** (31k docs, 1.74M tokens), meeting “large corpus” expectations.
2. **Lexical diversity is moderate** (TTR ≈ 0.176), consistent with domain-specific reviews.
3. **Ratings are heavily skewed positive**, so annotation should intentionally include more low-star reviews to avoid label imbalance.
4. **Lower ratings correlate with longer reviews**, meaning negative reviews may supply richer multi-attribute evidence.