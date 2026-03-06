### Annotation input generation

#### Stage 1 — Sample 1,000 unique reviews (master file)

We use `Sprint_2/src/make_annotation_input.py` to sample from the processed corpus (`Sprint_2/data/processed/`) and output a Label Studio tasks JSON plus a human-readable CSV. The script supports `.jsonl` input (recommended) and can stratify by star rating for diversity. 

```bash
mkdir -p Sprint_3/data/annotation_intermediary

python Sprint_2/src/make_annotation_input.py \
  --input Sprint_2/data/processed/sports_outdoors_joined_Coleman.jsonl \
  --n 1000 --seed 523 \
  --out-json Sprint_3/data/annotation_intermediary/master_1000_labelstudio.json \
  --out-csv  Sprint_3/data/annotation_intermediary/master_1000.csv \
  --stratify-by-rating
```

**Outputs**

* `Sprint_3/data/annotation_intermediary/master_1000_labelstudio.json` (**.json**) — Label Studio tasks (list of dicts)
* `Sprint_3/data/annotation_intermediary/master_1000.csv` (**.csv**) — inspection-friendly table view

#### Stage 2 — Split into per annotator pair sets

We then split the master file using `Sprint_3/src/split_annotation_sets.py`. Our design uses **two annotator pairs**, where each pair processes 500 unique samples. Each annotator within a pair labels the same 500 samples, ensuring **every one of the 1,000 samples receives two passes (100% overlap)**. 

```bash
mkdir -p Sprint_3/data/annotation_intermediary/annotation_input_sets

python Sprint_3/src/split_annotation_sets.py \
  --master-json Sprint_3/data/annotation_intermediary/master_1000_labelstudio.json \
  --out-dir     Sprint_3/data/annotation_intermediary/annotation_input_sets \
  --seed 523 \
  --pair1 yirui wei \
  --pair2 leah freya
```

**Outputs**

* `Sprint_3/data/annotation_intermediary/annotation_input_sets/pair1_yirui_wei_labelstudio.json`
* `Sprint_3/data/annotation_intermediary/annotation_input_sets/pair1_yirui_wei.csv`
* `Sprint_3/data/annotation_intermediary/annotation_input_sets/pair2_leah_freya_labelstudio.json`
* `Sprint_3/data/annotation_intermediary/annotation_input_sets/pair2_leah_freya.csv`
* `splits_manifest.json`


