

import json
import pandas as pd

def load_squad(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for article in data["data"]:
        for paragraph in article["paragraphs"]:
            for qa in paragraph["qas"]:
                # same three lines + append you already wrote
                passage_text = paragraph["context"]
                            # 2. get the question text from `qa`
                question_text = qa["question"]
                            # 3. get the first answer's text from `qa`
                answer_text = qa["answers"][0]["text"]
                            # 4. append a row (e.g. a dictionary) to `rows`
                rows.append({
                                "passage": passage_text,
                                "question": question_text,
                                "answer": answer_text
                            })

    return pd.DataFrame(rows)
train_df = load_squad("data/train-v1.1.json")
train_df.to_csv("data/squad_train.csv", index=False)

dev_df = load_squad("data/dev-v1.1.json")
dev_df.to_csv("data/squad_dev.csv", index=False)

print(train_df.shape)
print(dev_df.shape)
