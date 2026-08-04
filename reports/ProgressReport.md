# Progress Report
## Spoken Reading Comprehension Evaluation using ASR + Semantic Similarity

**Author:** Ava Jalalimoghaddam
**Repository:** https://github.com/Jalalimoghaddam/spoken-rc-eval

---

## Overview

This project builds a pipeline that automatically evaluates short spoken answers to reading comprehension questions, using automatic speech recognition (Whisper) and semantic similarity (Sentence-BERT) instead of rigid exact-match grading. Work is organized into 8 phases and 22 tasks; this report covers progress through **Phase 2 (Dataset)**.

---

## Completed Tasks

### Phase 1 — Project Setup

**Task 1 — Create Project**
- Initialized a Git repository and Python virtual environment.
- Installed core dependencies: `faster-whisper`, `sentence-transformers`, `torch` (CPU), `scikit-learn`, `numpy`, `pandas`.
- Verified all imports run correctly.
- Resolved a package-installation issue caused by the project directory being OneDrive-synced (fixed by using `python -m pip` to ensure installs targeted the correct environment).
- Cleaned and pushed the initial commit to GitHub after correcting an early mistake where large PyTorch binaries were accidentally committed before `.gitignore` existed.

**Task 2 — Organize Project Structure**
- Created the project's folder structure: `data/`, `models/`, `notebooks/`, `src/`, `evaluation/`, `demo/`, `reports/`.
- Added `.gitkeep` placeholder files so empty folders are tracked by Git (Git does not track empty directories by default).
- Configured `.gitignore` to exclude `data/` and `models/` from version control, since these will contain large datasets and model weights that don't belong in Git history.

### Phase 2 — Dataset

**Task 3 — Download and Explore Dataset**
- Downloaded the SQuAD v1.1 dataset (train and dev splits) as raw JSON files, choosing direct download over a helper library in order to understand the data format firsthand.
- Explored and mapped the nested JSON structure:
  - File → list of **articles** → each article has a `title` and a list of **paragraphs**
  - Each paragraph has `context` (the passage text) and `qas` (question–answer pairs)
  - Each `qa` has a `question`, an `id`, and an `answers` list, where each answer includes both the answer `text` and its character position (`answer_start`) in the passage
- Understood the purpose of `answer_start`: it disambiguates *which occurrence* of a repeated phrase in the passage is the correct answer, rather than indicating grading leniency.
- Saved exploration work as a Jupyter notebook (`notebooks/01_explore_squad.ipynb`) and committed it to the repository.

**Task 4 — Dataset Loader**
- Built `src/load_dataset.py`, a reusable script that flattens the nested SQuAD JSON structure (article → paragraph → question/answer pairs) into a flat table using a triple-nested loop.
- Wrapped the loading logic in a function, `load_squad(json_path)`, so the same code could process both the train and dev splits without duplication.
- For each question, extracted the passage, question text, and the first reference answer, then converted the results into a pandas DataFrame and saved as CSV.
- Verified the output size against expectations: 87,599 rows for the train split and 10,570 rows for the dev split, matching the known size of SQuAD v1.1.
- Confirmed the generated CSVs (`data/squad_train.csv`, `data/squad_dev.csv`) stay untracked by Git as intended, while the script itself (`src/load_dataset.py`) was committed and pushed.

---

## Next Steps

- **Task 5** — Construct a small (~50 question) evaluation subset with reference answers for later testing.
- **Phase 3** onward — Integrate Whisper for speech recognition on spoken answers.

---

## Working Method

Progress is tracked against a 22-task checklist, worked one task per session (~60 minutes each), with short breaks between sessions to maintain steady, sustainable progress.