# spoken-rc-eval
Spoken Reading Comprehension Evaluation using ASR + Semantic Similarity
# Spoken Reading Comprehension Evaluation

Automatically grading short **spoken** answers to reading comprehension questions using automatic speech recognition (Whisper) and semantic similarity (Sentence-BERT), rather than exact-text matching.

Full report (ACL format): [`report/report.pdf`](report/report.pdf)

## Overview

Students answer reading comprehension questions **out loud** instead of picking from multiple choice. The system:

1. Transcribes the spoken answer with **Whisper** (`faster-whisper`, `tiny` model)
2. Compares the transcript to a reference answer using **Sentence-BERT** (`all-MiniLM-L6-v2`) cosine similarity
3. Applies a hybrid scoring rule that additionally verifies any numbers in the answer exactly, since general-purpose sentence embeddings are unreliable at distinguishing correct numeric answers from incorrect ones with similar sentence structure (see report, Section 4.2)
4. Classifies the result as **Correct / Incorrect / Borderline**

## Project Structure

```
spoken-rc-eval/
├── data/                  # datasets, generated audio, and pipeline outputs (gitignored)
├── models/                # downloaded/fine-tuned model weights (gitignored)
├── notebooks/             # exploratory Jupyter notebooks
├── src/
│   ├── load_dataset.py    # SQuAD JSON -> flat CSV
│   ├── similarity.py      # hybrid_similarity() scoring function
│   └── finetune.py        # short Sentence-BERT fine-tuning run
├── evaluation/
│   └── evaluate.py        # accuracy / precision / recall / F1
├── demo/
│   └── app.py              # interactive Gradio demo
├── report/                 # ACL-format LaTeX report + compiled PDF
└── requirements.txt
```

## Setup

Requires Python 3.11+ and roughly 2 GB free disk space (PyTorch + model weights).

```bash
git clone https://github.com/Jalalimoghaddam/spoken-rc-eval.git
cd spoken-rc-eval

python -m venv venv
# Windows:
venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Everything runs on CPU; no GPU is required. Model weights (Whisper `tiny`, `all-MiniLM-L6-v2`) are downloaded automatically on first use via Hugging Face's cache.

## Data

This project uses **SQuAD v1.1**. Download the two splits into `data/`:

```bash
mkdir -p data
curl -o data/train-v1.1.json https://rajpurkar.github.io/SQuAD-explorer/dataset/train-v1.1.json
curl -o data/dev-v1.1.json https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v1.1.json
```

## Running the Pipeline

Run from the project root, in order:

```bash
# 1. Parse SQuAD JSON into flat train/dev CSVs
python src/load_dataset.py

# 2. Build the 50-question evaluation set (data/eval_set.csv)
#    — see notebooks/02_build_eval_set.ipynb for the selection process

# 3. Generate spoken answers (TTS) and transcribe them with Whisper
#    — see notebooks/03_test_whisper.ipynb and Task 7/8 notebooks

# 4. Score every answer with the hybrid similarity pipeline
python src/similarity.py

# 5. Run the full evaluation (metrics + confusion matrix)
python evaluation/evaluate.py
```

Each stage reads from and writes to CSV files in `data/`, so any stage can be re-run independently without repeating earlier ones (e.g., re-scoring after a change to `similarity.py` does not require re-transcribing audio).

## Fine-Tuning (short training run)

A short Sentence-BERT fine-tuning run on the 50 labeled evaluation examples, completing in under 3 seconds on CPU:

```bash
python src/finetune.py
```

This trains for 1 epoch on `data/pipeline_results.csv` and saves the result to `models/finetuned_sbert/`. As discussed in the report (Section 5.4), this small-scale run yields a null result — expected given the small amount of data — and is included to demonstrate a working, reproducible training procedure rather than to improve accuracy.

## Interactive Demo

```bash
python demo/app.py
```

Opens a local Gradio interface (default `http://127.0.0.1:7860`) where you can pick a question, record a spoken answer via microphone, and see the transcript, similarity score, and prediction live.

**Note:** open the link in a real browser window (not an embedded editor preview) for microphone access to work correctly.

## Results

On the 50-example evaluation set (see report for full details):

| Metric | Score |
|---|---|
| Accuracy | 0.960 |
| Precision | 0.977 |
| Recall | 0.977 |
| F1 | 0.977 |

## Deviations from the Original Project Plan

- **Text-to-speech instead of recorded human speech**: the original plan considered either recording spoken answers or generating them via TTS. TTS was used for all 50 evaluation answers (split across two engines, `gTTS` and `pyttsx3`) to make data collection feasible within the project's time budget. This is discussed as a limitation in the report (Ethical Considerations and Limitations sections): results may not fully generalize to real human speech, particularly across accents and speech patterns not represented in synthetic voices.
- **Gradio instead of Streamlit** for the demo: chosen for its built-in, low-code support for audio input/output, better suited to this project's record-transcribe-score workflow than Streamlit's more general-purpose components.

## License

This project is submitted as coursework and is not licensed for reuse.