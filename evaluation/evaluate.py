import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

df = pd.read_csv("data/pipeline_results.csv")

# Borderline رو جزو Correct حساب می‌کنیم
df["final_prediction"] = df["prediction"].apply(lambda p: 1 if p in ["Correct", "Borderline"] else 0)

accuracy = accuracy_score(df["human_label"], df["final_prediction"])
precision = precision_score(df["human_label"], df["final_prediction"])
recall = recall_score(df["human_label"], df["final_prediction"])
f1 = f1_score(df["human_label"], df["final_prediction"])

print(f"Accuracy:  {accuracy:.3f}")
print(f"Precision: {precision:.3f}")
print(f"Recall:    {recall:.3f}")
print(f"F1 Score:  {f1:.3f}")