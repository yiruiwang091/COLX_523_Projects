# COLX 523 Project Proposal: Customer Reviews Annotated Corpus with Browser Interface

## 1) Project overview & motivation

Customer reviews contain rich signals about how products perform in real use. However, extracting actionable insights (e.g., *what* attribute is being discussed and *how* customers feel about it) typically requires manual reading at scale. Our overarching two-course project aims to support a “product data analyst” workflow by automatically monitoring reviews and extracting attribute-level sentiment (e.g., durability, ease of setup, design.)

In this course, our goal is to build an annotated corpus with a browser interface for non-experts. The corpus will be large enough to support later modeling and will be annotated with attribute-level sentiment labels that are meaningful, learnable, and useful for downstream applications in the second course.


## 2) Data source

**Primary source:** *Amazon Review Data (2018) by Ni et al.*  
**Website:** https://nijianmo.github.io/amazon/index.html

This source provides publicly downloadable review and metadata dumps by category. We will use two datasets from the **Sports & Outdoors** category:

- **Reviews (5-core)**: dense subset where each remaining user and item has at least k reviews. Fields include: `reviewerID`, `asin`, `reviewerName`, `vote`, `style`, `reviewTime`, `image`, `reviewText`, `overall`, `summary`, `unixReviewTime`.
- **Product metadata**: product-level info including `asin`, `title`, `feature`,
`description`, `price`, `imageURL` / `imageURLHighRes`, `related`, `salesRank`,
`brand`, `categories`, `tech1`, `tech2`, `similar`.

**Collection / “small scraper” requirement:**  
Although the dataset can be downloaded directly, we will still build a scraper pipeline that:

- programmatically retrieves the relevant category files from the Ni et al. website (e.g., the Sports & Outdoors review dump and metadata dump),
- validates checksums/expected size where possible,
- decompresses/parses the raw dumps into structured JSONL, and
- produces a reproducible “data acquisition” script (so the corpus can be rebuilt from scratch without manual steps).

This satisfies the requirement that we still build a scraper while relying on a legally accessible research dataset instead of scraping Amazon product pages directly.


## 3) Corpus description & structure/metadata

**Text type**: consumer product reviews (short-form opinionated text)  
**Language**: English  
**Genre/register**: informal evaluative writing; concrete, scenario-based narratives (“camping trip,” “rain,” “setup”), mixed with short descriptive statements and comparisons.  
**Topic/content**: outdoor and camping products under the Coleman brand (e.g., tents, coolers, stoves, sleeping bags, lanterns)  
**Who wrote the texts**: Amazon reviewers (general public)  
**Document length**: average review length: 55

The corpus is structured through product grouping (by `asin`):
    
    Product (asin A)

       ├── Review 1
       ├── Review 2
       ├── Review 3
       ...

    Product (asin B)

       ├── Review 1
       ├── Review 2
       ...

and contains metadata:

- **Review-level**: overall star rating, review text
- **Product-level**: product title, sub-categories (e.g., `"cat_l5"`), price, description, product image, sales rank.

      {
        "asin": "B002BZX8Z6",
        "overall": 4.0,
        "reviewText": "Good quality product and works as expected.",
        "title": "Coleman Sundome 4-Person Tent",
        "price": "$89.99",
        "description": "Spacious 4-person tent with WeatherTec system and easy setup design.",
        "rank": "1,245 in Sports & Outdoors",
        "imageURL": [
          "https://images-na.ssl-images-amazon.com/images/I/81aZLz3h5bL._AC_SL1500_.jpg"
        ],
        "cat_l1": "Sports & Outdoors",
        "cat_l2": "Outdoor Recreation",
        "cat_l3": "Camping & Hiking",
        "cat_l4": "Tents & Shelters",
        "cat_l5": "Tents"
      }

## 4) Targeting/filtering strategy & corpus size

We will target a specific subset: **Coleman** within the Sports & Outdoors category.

**Reasons:**

- **Suitable for non-expert corpus browsers:** familiar everyday products and concrete scenario-based language of reviews make the corpus intuitive and easy for non-experts to browse, search, and understand without a technical background.  
- **Strong for attribute-level sentiment modeling:** reviews naturally talk in attribute phrases that are easy to label and model, e.g., durability, ease of setup, size/space, weight/portability, weather resistance, comfort, value, build quality, design, reliability.

**Filtering procedure:**

1. Load Sports & Outdoors product metadata.
2. Filter products where `brand == "Coleman"`
3. Join reviews to the filtered products via `asin`.
4. Keep reviews with non-empty `reviewText` (and optionally a minimal length threshold to remove near-empty content) and their `overall` ratings for later sentiment analyses.

**Size**: Coleman subset contains 31,366 reviews and approximately 1,726,718 tokens. This meets and exceeds the Brown-sized corpus guideline (~1M tokens), providing enough material for meaningful browsing and later modeling.


## 5) Preliminary annotation plan

We propose an attribute-level sentiment annotation that is easy for non-experts to understand but rich enough to train downstream systems.

**Unit of annotation (instance):** a span within a review that expresses an opinion about a specific product attribute. Annotators will highlight the relevant text span and assign labels.

**Labels (initial proposal):**

- **Attribute category (multi-class):**
  - durability/build quality
  - ease of setup/use
  - size/space/capacity
  - weight/portability
  - weather resistance/insulation
  - comfort
  - reliability/functionality
  - design/appearance
  - value/price

- **Sentiment polarity (\~3 ways):**
  - positive
  - negative
  - neutral

**Why this is appropriate and not trivial:**

- It goes beyond review-level sentiment by linking sentiment to what is being evaluated.
- It supports a concrete downstream task: predicting (attribute, polarity) from text spans and aggregating over products.
- It is feasible for non-expert annotators like us because camping/outdoor attributes are intuitive and reviews are concrete.

**Annotation scale and overlap requirement:**

Target ~1000 annotated instances (attribute-sentiment spans). We will
design sampling so that:

- each instance is annotated by at least two annotators;
- annotators each label ~500 spans;
- we include a mix of product types to avoid overfitting to a single product


## 6) Corpus storage & Browser interface

We will keep the corpus reproducible and easy to use by storing:

- **Raw data (immutable):**
  - `raw/Sports_and_Outdoors_5.json.gz` (exactly as acquired)
  - `meta_Sports_and_Outdoors.json.gz` (exactly as acquired)

- **Processed corpus (analysis-ready):**
  - JSONL for documents (reviews) with selected fields and the join key.
  - A stable unique `review_id` to link annotations.

- **Annotations:**
  - Stored separately as JSONL (or a lightweight database like SQLite) with:
    - `review_id`, `asin`
    - span offsets (`start_char`, `end_char`) and/or sentence index
    - `attribute_label`, `sentiment_label`
    - `annotator ID`, `timestamp`, and version of guidelines

The browser will support interactive exploration:
- **Browse by product:** show product title/image and a list of reviews; allow sorting/filtering by product sales rank.
- **Review view:** display full review text with sentence segmentation; allow span highlighting.
- **Annotation panel:** dropdowns for attribute + sentiment.
- **Export:** download annotation JSONL and summary stats (counts by attribute/sentiment).


## 7) Corpus applications

**Primary use** (aligned with overarching project):

- Train and evaluate models for attribute-level sentiment extraction from customer reviews to support product data analyses.

**Secondary uses**:

- Study comparative language and “failure narratives” (“broke after 2 trips”) in customer reviews.
- Build lexicons of domain-specific attribute expressions (e.g., “packs down small,” “leaks,” “rainfly”).
- Analyze relationships between star rating vs textual sentiment by attribute (e.g., 3-star reviews with strong negative durability mentions).
- Educational use: a browsable, intuitive corpus for teaching annotation, sentiment, and discourse.
