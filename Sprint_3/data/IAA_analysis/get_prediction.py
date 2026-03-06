import asyncio
import aiohttp
import json
from tqdm import tqdm

URL = "http://206.87.233.174:9090/predict"
INPUT_FILE = "/home/leah/MDSCL/COLX523/COLX523_Freya_Leah_Wei_Yirui/Sprint_3/data/annotation_final/pair_2.json"

CONCURRENCY = 20
BATCH_SIZE = 10


async def predict_batch(session, batch, sem):
    async with sem:
        payload = {
            "tasks": [{"data": item} for item in batch]
        }

        async with session.post(URL, json=payload) as resp:
            return await resp.json()


async def main():
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    batches = [
        data[i:i + BATCH_SIZE]
        for i in range(0, len(data), BATCH_SIZE)
    ]

    sem = asyncio.Semaphore(CONCURRENCY)

    results = []

    async with aiohttp.ClientSession() as session:
        # tqdm 进度条
        for batch in tqdm(batches, desc="Predicting"):
            res = await predict_batch(session, batch, sem)
            results.append(res)

    # flatten results
    predictions = []
    for r in results:
        if "results" in r:
            predictions.extend(r["results"])
        else:
            predictions.append(r)

    with open("pair_2_predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)

    print(f"\nDone. Saved {len(predictions)} predictions.")


if __name__ == "__main__":
    asyncio.run(main())