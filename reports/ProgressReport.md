# Progress Report
## Spoken Reading Comprehension Evaluation using ASR + Semantic Similarity

**Author:** Ava Jalalimoghaddam
**Repository:** https://github.com/Jalalimoghaddam/spoken-rc-eval

---

## Overview

This project builds a pipeline that automatically evaluates short spoken answers to reading comprehension questions, using automatic speech recognition (Whisper) and semantic similarity (Sentence-BERT) instead of rigid exact-match grading. Work is organized into 8 phases and 22 tasks.

### The problem

Reading comprehension is usually tested with multiple-choice questions because they're easy to grade — but they don't really show how well a student understood the material, since answers can be guessed. A better test is to have students answer **in their own words, out loud**. The challenge is that automatically grading spoken answers is hard: the same correct idea can be expressed in countless different ways, and speech adds transcription errors on top of that.

### How the pipeline solves it

1. **Speech recognition (ASR) — Whisper.** Converts the student's spoken answer into text.
2. **Semantic similarity — Sentence-BERT.** Compares the transcribed text to the reference answer based on *meaning*, not exact wording — so a differently-phrased but correct answer still scores well.
3. **Threshold-based decision.** The similarity score (e.g., 0–1) is turned into a label: **Correct / Incorrect / Borderline**, based on a chosen cutoff.

This helps students get faster, fairer feedback (since paraphrasing isn't penalized) and helps teachers by partially automating grading.

### Data source

**SQuAD v1.1** — a widely-used dataset of roughly 100,000 question-answer pairs built from Wikipedia articles. Each item provides a **passage** (the reading material), a **question**, and a **reference answer**.

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

**Task 5 — Small Evaluation Dataset**
- Analyzed the distribution of reference answer lengths in the dev set (mean ~3 words, median 2 words, range 1–29 words) to inform a balanced selection strategy.
- Split candidate questions into three length-based buckets — short (1 word), medium (2–4 words), and long (5+ words) — to ensure the evaluation set covers a variety of answer types rather than being dominated by short factual answers.
- Hand-picked 50 questions with good topical and question-type variety (who/what/when/where/how many), drawn from random candidate pools within each bucket: 15 short, 25 medium, 10 long.
- Combined the selections into a single evaluation set and saved it as `data/eval_set.csv`, which will serve as the fixed benchmark for later human-vs-system comparison (Phase 6 evaluation).
- Resolved a Jupyter/Python environment mismatch (notebook was running Anaconda's Python instead of the project's virtual environment), by registering the venv as a proper Jupyter kernel — an important fix to avoid confusing package errors later in the project.

**Phase 2 (Dataset) is now complete.**

### Phase 3 — Speech Recognition

**Task 6 — Install Whisper**
- Loaded the `tiny` Whisper model via `faster-whisper` (choosing the smallest model first to validate the pipeline quickly on CPU before optimizing for accuracy with larger models later).
- Confirmed models are cached automatically by Hugging Face's caching system (outside the project folder, in the standard shared cache location) rather than needing manual download management.
- Ran a first real transcription test on a sample audio file (an airport-announcement listening exercise), successfully producing accurate, timestamped, multi-segment transcription output — including correctly identifying the spoken language with high confidence.
- Debugged a working-directory mismatch between notebook sessions (the same class of issue encountered in Task 5), reinforcing the practice of verifying paths with `os.getcwd()` before troubleshooting further.
- Implemented a custom timestamp formatter to convert raw seconds into the `HH:MM:SS,mmm` format, and used it to export the transcription as a properly structured `.srt` subtitle file — the task's "save transcript" requirement.

**Task 7 — Prepare Spoken Answers**
- Decided on a fully text-to-speech (TTS) approach for generating spoken versions of the 50 evaluation answers, favoring feasibility over the higher realism (but much higher effort) of self-recording.
- Split the 50 answers into two batches of 25 (shuffled first to keep a fair mix of short/medium/long answers in each half), generating audio with two different TTS engines for source variety:
  - **gTTS** (Google Text-to-Speech, online, more natural-sounding) — `data/audio/gtts/`
  - **pyttsx3** (offline, uses Windows system voices) — `data/audio/pyttsx3/`
- Debugged a missing Windows dependency (`pywin32`/`pywintypes`) required by `pyttsx3`'s offline speech engine, and a follow-up `NameError` caused by a Jupyter kernel restart clearing previously imported modules and variables.
- Built `data/audio_manifest.csv`, a mapping file linking every generated audio file back to its passage, question, reference answer, and answer length — this will be the key input for Task 8's batch transcription.

**Task 8 — Batch Transcription**
- Built a reusable `transcribe_audio()` function that runs Whisper on a single audio file and concatenates its timestamped segments into one clean transcript string.
- Wrote a loop that applies this function to all 50 audio files listed in `data/audio_manifest.csv`, adding the results as a new `transcript` column, and saved the result as `data/transcript.csv`.
- Resolved a working-directory path issue affecting both the manifest file and the individual audio file paths referenced inside it (the same class of relative-path issue encountered in earlier tasks, now appearing in two places within the same script).
- Reviewed the actual transcription output against the reference answers and identified concrete ASR error patterns that will be directly relevant to later semantic similarity testing, including:
  - Misheard proper nouns/technical terms (e.g., "Lower Lorraine" transcribed as "Lower the rain"; "cilia" heard as "sillier")
  - Notation expanded into natural language (e.g., "10,000 m2" transcribed as "10,000 square meters" — correct in meaning, different in exact text)
  - Minor phonetic misspellings of names (e.g., "Bert Bolin" → "Bert Bollin")
- These real transcription imperfections form the actual test conditions that the semantic similarity model (Phase 4) will need to handle — validating the project's core premise before that.

**Phase 3 (Speech Recognition) is now complete.**

---

## Next Steps

- **Task 9** — Install Sentence-BERT, download a pretrained model, and test generating embeddings.
- **Phase 4** — Semantic Similarity: compare identical answers, paraphrases, and wrong answers to understand how similarity scores behave before building the full scoring pipeline.

---

## Working Method

Progress is tracked against a 22-task checklist, worked one task per session (~60 minutes each), with short breaks between sessions to maintain steady, sustainable progress.