# Annotation Guidelines: Attribute-Level Sentiment (Coleman / Sports & Outdoors)

## 1. Goal of the annotation

We are creating a fine-grained resource for **attribute-level sentiment analysis** of Coleman product reviews: we identify **which product attribute** is being talked about and, if the attribute is mentioned in the review, **what sentiment** the reviewer expresses toward it. 

This supports downstream tasks like aspect-based sentiment modeling and product insight aggregation (e.g., “durability complaints are rising”). 

---

## 2. What to annotate

Each item has three text sources:

* **Title** (metadata)
* **Description** (metadata)
* **Review text** (user review)

### 2.1 Units of annotation

We annotate at two connected levels:

1. **Attribute Mention (span-level)**
   A *minimal contiguous span* that refers to a product characteristic. Mentions can be:

* **explicit** (“stakes”, “thin metal”, “too small”)
* **implicit** (“still hold up” → durability; “keeps things really cool” → cooling performance) 

Repeated mentions of the same attribute within one item can be annotated more than once if they appear in different contexts. 

2. **Attribute–Sentiment Relation (label on attribute mentions in reviews)**
   For every attribute mention that occurs in the **review text**, assign a sentiment polarity label reflecting the opinion expressed toward that attribute. 

**Important:** Do **not** assign sentiment to attribute mentions that only appear in title/description (metadata). If a span is purely metadata, sentiment is **N/A** (no label).  

---

## 3. Labels

### 3.1 Attribute label (open-ended)

Attribute categories are **open-ended**: you may introduce new attribute types as needed, based on semantic meaning, not a fixed closed list. 

#### Attribute naming rules (for consistency)

When you type/record an attribute label:

* Use **short, semantic names** in **lowercase** (optionally snake_case).
* Prefer *what it is* over *how it’s described*:

  * “weight” (not “heavy”), “size” (not “small”), “noise” (not “loud”)
* If it’s clearly about a component, name the component:

  * “mallet”, “stakes”, “battery_pack”
* If it’s about performance, name the performance aspect:

  * “cooling_performance”, “inflation_power”, “charging_safety”

**Team rule:** when you introduce a new attribute name, add it to a shared “attribute glossary” (a running list) so everyone reuses the same term going forward.

### 3.2 Sentiment polarity label (review-text mentions only)

For attribute mentions in **review text**, assign one of: 

* **positive**: attribute evaluated favorably
* **negative**: attribute evaluated unfavorably
* **neutral**: attribute mentioned with no clear evaluation
* **unknown**: sentiment cannot be determined from the text (sarcasm, incoherent, contradictory, or too ambiguous). 

**Do not infer sentiment from the star rating.** Sentiment must be grounded in what is actually written. 

---

## 4. How to annotate (procedure)

For each item: 

1. Read **title + description** to understand what the product is and what attributes it claims.
2. In **title/description/review**, highlight **attribute mention spans** (minimal contiguous text).
3. For attribute mentions in the **review text**, assign sentiment (positive/negative/neutral/unknown).
4. Double-check span boundaries and label consistency before submitting. 

---

## 5. Span boundary rules (important for agreement)

**Choose the smallest span that still identifies the attribute mention.** 

Good:

* “thin metal”
* “too small”
* “Obnoxiously loud”
* “still hold up”

Avoid (too long):

* Whole paragraphs
* Entire multi-sentence updates, unless you truly cannot isolate the mention

### Implicit attribute mentions

If the attribute is implied rather than named, highlight the phrase that expresses it:

* “still hold up” → attribute label: `durability`

### Multiple attributes in one sentence

Annotate each attribute separately:

* “loud, heavy … gets very hot … doesn’t have much air pressure” → 4 different attributes

### Mixed/updated opinions

If the review gives both positive and negative opinions about the same attribute in different places, annotate each mention separately (each with its own sentiment).

### Sarcasm / off-topic / joke reviews

If the text is clearly not evaluative in a normal sense, use:

* attribute mentions if they are still clearly referenced, and
* sentiment = **unknown** when you can’t justify polarity from the literal meaning.

---

## 6. Worked examples (10 records from Sprint 2 annotation input)

Below, each example lists suggested annotations as:
**span** → `attribute_label` / `sentiment` (sentiment only for spans in review text)

### Example 1 — review_id 18756 (Camping cot)

Review: “These are awesome… still hold up… Much better than an air mattress…”

* “awesome” → `overall_quality` / positive
* “still hold up” → `durability` / positive
* “Much better than an air mattress” → `comfort` / positive *(comparison implies favorable evaluation)*

### Example 2 — review_id 4944 (Tent kit)

Review: “I love the stakes… wish the mallet was a little smaller… weighs down my pack.”

* “stakes” → `stakes` / positive
* “stake remover” → `stake_remover` / positive
* “bag” → `carry_bag` / positive
* “mallet… a little smaller” → `size` / negative
* “weighs down my pack” → `weight` / negative

### Example 3 — review_id 2037 (Mess kit)

Review: “Price is good… really thin metal… afraid a hot campfire would burn through this… For the price you get what you pay for.”

* “Price is good” → `price` / positive
* “really really thin metal” → `material_thickness` / negative
* “burn through” → `heat_resistance` / negative *(fear/concern stated explicitly)*
* “For the price… you get what you pay for” → `value` / neutral *(reads as resigned rather than clearly pos/neg)*

### Example 4 — review_id 28219 (Marine cooler)

Review: “Keeps things really cool”

* “Keeps things really cool” → `cooling_performance` / positive

### Example 5 — review_id 3946 (Tent kit; off-topic/zombie)

Review is mostly joke scenario; no clear product evaluation.

* “stakes” → `stakes` / unknown
* “mallet” → `mallet` / unknown
* “broom” → `broom` / unknown

*(Rationale: mentions components but no real evaluative language about quality/performance; avoid using star rating.)*

### Example 6 — review_id 30950 (Lantern + battery packs; safety issue)

Review: long failure narrative + explicit safety hazard.

* “fail in a few years” → `reliability` / negative
* “battery packs failed” → `battery_pack_reliability` / negative
* “good light output” → `brightness` / positive
* “detachable flashlight is handy” → `usability` / positive
* “still won’t work” → `functionality` / negative
* “possible fire hazard” → `safety` / negative
* “fail during charging” → `charging_safety` / negative
* “heat has deformed the plastic” → `overheating` / negative

### Example 7 — review_id 9119 (Lantern carry case)

Review: “too small for nortstars!!”

* “too small” → `size` / negative
* “for nortstars” → `compatibility` / negative *(compatibility/fit with a specific lantern model)*

### Example 8 — review_id 16665 (100% DEET repellent)

Review: “Stains clothes beeare”

* “Stains clothes” → `staining` / negative

### Example 9 — review_id 28 (Rechargeable pump; mixed + updates)

Review: “Doesn’t fill… Obnoxiously loud… heavy… gets very hot… doesn’t seem to have much air pressure… no longer power on… battery was dead…”

* “Doesn’t fill… very well” → `inflation_performance` / negative
* “Obnoxiously loud” → `noise` / negative
* “heavy” → `weight` / negative
* “gets very hot” → `overheating` / negative
* “doesn’t… have much air pressure” → `air_pressure` / negative
* “will no longer power on” → `reliability` / negative
* “battery was dead” → `battery_life` / negative
* “now works better than it ever has” → `performance_after_repair` / positive *(post-repair statement; keep separate)*

### Example 10 — review_id 809 (Expandable water carrier)

Review: “flimsy… suppose to be collapsable… Comes in handy…”

* “very flimsy” → `build_quality` / negative
* “suppose to be collapsable” → `collapsibility` / neutral
* “Comes in handy” → `usability` / positive

---

## 7. What to do when unsure

* Choose **unknown** sentiment when polarity isn’t supportable from the text (sarcasm, unclear intent, etc.). 
* Leave a short note for adjudication in your team’s disagreement log (e.g., “sarcasm/off-topic; uncertain sentiment”).
* Follow the “minimal span + evidence-based sentiment” rule first.
