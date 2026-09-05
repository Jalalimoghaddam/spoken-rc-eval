import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# بارگذاری داده
df = pd.read_csv("data/pipeline_results.csv")

# ساخت نمونه‌های آموزشی
train_examples = []
for i, row in df.iterrows():
    example = InputExample(
        texts=[row["answer"], row["transcript"]],
        label=float(row["human_label"])
    )
    train_examples.append(example)

print(f"Number of training examples: {len(train_examples)}")


model = SentenceTransformer("all-MiniLM-L6-v2")

train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=8)
train_loss = losses.CosineSimilarityLoss(model)

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=1,
    warmup_steps=10,
    output_path="models/finetuned_sbert"
)

print("Fine-tuning complete!")