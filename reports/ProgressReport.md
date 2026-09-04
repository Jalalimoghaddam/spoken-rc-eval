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

### Phase 4 — Semantic Similarity

**Task 9 — Install Sentence-BERT**
- Confirmed `sentence-transformers` was already installed (from Task 1's initial setup) and loaded a pretrained model, `all-MiniLM-L6-v2` — a lightweight, CPU-friendly Sentence-BERT model.
- Generated a first sentence embedding and confirmed its shape: a 384-dimensional vector representing the sentence's meaning numerically.
- Tested cosine similarity (the standard method for comparing embeddings by the angle between them, not raw magnitude) between:
  - A reference answer and an ASR-style near-miss (e.g., "Saint Bernadette Soubirous" vs. "Saint Bernadette Sabirus") → similarity ≈ 0.83, correctly identified as highly similar despite the textual difference
  - The same reference answer and a completely unrelated sentence → similarity ≈ 0.07, correctly identified as unrelated
- This confirmed the core mechanism the project depends on: semantic similarity distinguishes meaning-preserving variation from true mismatches, unlike exact-text matching.

**Task 10 — Similarity Experiment**
- Systematically tested Sentence-BERT's cosine similarity across three categories using real answers from `eval_set.csv`:
  - **Paraphrases** (same meaning, different wording, hand-written): similarity scores ranged **0.552–0.796**
  - **Unrelated answers** (answer paired with an unrelated answer from a different question): similarity scores ranged **-0.041–0.177**
  - A clear gap exists between these two ranges, suggesting a threshold somewhere around 0.3–0.4 could reasonably separate correct from incorrect answers (to be tuned properly in Task 13)
- **Key finding — a significant limitation was discovered:** a third category, **"near-miss" answers** (same sentence structure and most wording, but with a critical factual detail changed — e.g., a different year, measurement, or number), was tested and produced unexpectedly *high* similarity scores that overlapped with or exceeded the paraphrase range. For example, "45–60 nanometers across" vs. "20–30 nanometers across" scored **0.943** — higher than any correct paraphrase — despite being factually wrong.
  - **Cause:** Sentence-BERT appears to weight overall sentence structure and topic similarity heavily, but does not specifically verify that numeric values (dates, quantities, measurements) match — since numbers are treated as just another token rather than an exact fact to check.
  - **Implication for the project:** semantic similarity alone is likely insufficient for grading answers where the reference answer is a number, date, or measurement. A possible mitigation (to revisit during Phase 5/6) is adding a supplementary exact-match or tolerance-based check specifically for numeric content, combined with (not replacing) the semantic similarity score — e.g., a weighted combination, or question-type-aware scoring rules.
- Saved all experiment results to `data/similarity_experiment.csv` for reference during later threshold tuning and error analysis.

---

## VG-Level Extension: Hybrid Similarity Scoring

Following the numeric-answer limitation discovered in Task 10, a solution was designed and implemented to specifically address it, going beyond the base task requirements.

**Problem recap:** Sentence-BERT's semantic similarity treats numbers as ordinary tokens rather than facts requiring exact matching, causing factually wrong answers with matching sentence structure (e.g., a different date or measurement) to score misleadingly high — sometimes higher than genuinely correct paraphrases.

**Solution implemented — `hybrid_similarity()`:** a wrapper function that combines semantic similarity with an exact-match check on numeric content:
1. Computes the standard Sentence-BERT cosine similarity between the reference answer and the transcript.
2. Extracts all numbers from both texts using a regular expression, with number-format normalization (removing thousands-separator commas via a targeted regex pattern, `(\d),(\d{3})`, rather than blindly stripping all commas — this specifically avoids incorrectly merging comma-separated lists of distinct numbers, e.g., "1,2,3", into a single number).
3. Decision logic: if the reference answer contains no numbers, the semantic similarity score is used unchanged. If it does contain numbers, the transcript's numbers must match exactly (as a set, so order doesn't matter) — if they match, the semantic score is used as-is; if they don't match, the similarity is forced to 0, regardless of how high the semantic score was.
4. A stricter (rather than partial-credit/weighted) penalty was deliberately chosen for mismatched numbers, as a reasonable trade-off between correctness and implementation complexity for this project's scope.

**Verified results:**
| Comparison | Raw semantic similarity | Hybrid similarity |
|---|---|---|
| "45–60 nanometers across" vs. "20–30 nanometers across" (wrong number) | 0.943 (misleadingly high) | **0** (correctly rejected) |
| "It was founded in 1852" vs. "The museum opened in 1852" (correct paraphrase, matching number) | 0.625 | **0.625** (unaffected) |
| "considerable impact" vs. "a significant effect" (no numbers involved) | 0.670 | **0.670** (unaffected) |

This confirms the fix directly resolves the Task 10 finding without disrupting normal paraphrase scoring, and will be incorporated into the main pipeline in Task 11.

**Task 11 — Build `similarity.py`**
- Created `src/similarity.py`, a standalone, reusable script implementing the reference-answer → student-answer → similarity-score pipeline.
- Structured the file following the established project pattern of loading expensive resources (the Sentence-BERT model) once at module load time rather than repeatedly inside a function, avoiding unnecessary reloading when the function is called many times (as it will be in Task 12, across all 50 evaluation rows).
- Incorporated the `hybrid_similarity()` function (including the numeric-mismatch fix from the VG extension) as the pipeline's core scoring logic, along with the supporting `extract_numbers()` helper.
- Used Python's `if __name__ == "__main__":` pattern to include a self-contained test that runs only when the script is executed directly, while keeping the functions cleanly importable from other scripts (e.g., for Task 12).
- Verified correct behavior by running the script directly and confirming expected output.

### Phase 5 — Complete Pipeline

**Task 12 — Complete Pipeline**
- Connected the full pipeline by applying `hybrid_similarity()` (imported from `src/similarity.py`) across all 50 rows of `transcript.csv`, comparing each reference answer against its Whisper-generated transcript.
- Saved the combined results — including passage, question, answer, transcript, and the new `similarity` score — to `data/pipeline_results.csv`.
- Resolved a module import path issue (`ModuleNotFoundError: No module named 'similarity'`) by adding the project's `src/` directory to Python's module search path (`sys.path.append("../src")`) from within the notebook, since notebooks and scripts don't share a working directory by default.
- Reviewed the resulting similarity scores across all 50 rows and found the pipeline behaves as expected: near-perfect transcriptions scored close to 1.0, minor spelling variations (e.g., "Bert Bolin" vs. "Bert Bollin") scored appropriately high via the semantic path, and the earlier VG numeric-mismatch fix correctly zeroed out a genuinely wrong near-miss case.
- **New edge case discovered:** one row (2% of the evaluation set) produced an unexpected false negative — "10,000 m2" (reference) vs. "10,000 square meters" (transcript) scored **0**, despite being semantically identical. This happened because the unit abbreviation "m2" contains a digit ("2"), which `extract_numbers()` treats as a separate number to match; since the transcript's spelled-out form ("square meters") has no digit, the number sets didn't match, and the hybrid scoring logic correctly-but-overzealously rejected it.
  - **Decision:** given this occurred in only 1 of 50 rows, it was deliberately left unresolved for now and documented as a known limitation, following the same cost/benefit reasoning applied in Task 10 — the fix (e.g., distinguishing "unit-attached" digits from meaningful standalone numbers) would add non-trivial complexity for a low-frequency edge case, and is noted here as a candidate for future improvement rather than immediate action.

### Phase 6 — Evaluation (in progress)

**Task 13 — Threshold Tuning (started, not yet complete)**
- Began building a human-labeled ground truth for the 50 pipeline results, since evaluating candidate thresholds requires knowing which answers are *actually* correct (independent of the system's own similarity score) — otherwise the evaluation would circularly validate the system against itself.
- Reviewed all 50 rows of `data/pipeline_results.csv` (answer, transcript, and similarity score) to prepare for manual labeling.
- **New finding discovered while investigating an unexpected low score:** row 25 ("1893" vs. Whisper's transcript "1,893") scored only **0.193** despite being numerically identical. Debugging traced this to the *semantic similarity component itself* (not the hybrid numeric-matching logic, which correctly identified the numbers as equal) — `util.cos_sim(model.encode("1893"), model.encode("1,893"))` alone returns 0.193.
  - **Likely cause:** Sentence-BERT appears to be unreliable for very short, standalone numeric strings with minimal surrounding context — a single formatting character (a thousands-separator comma) can disproportionately affect the embedding when there's little other text to anchor the meaning.
  - **Implication:** this is a second, distinct case (alongside the earlier "m2" unit-abbreviation issue) where the current pipeline produces a false negative on a numerically-identical answer. Both cases involve numbers, but have different root causes: the "m2" case was a number-extraction issue (a unit abbreviation being misread as a number), while this case is a pure embedding-quality issue with short numeric-only text.
  - This will be taken into account when manually labeling ground truth for threshold selection (row 25 should be labeled as correct despite its low similarity score), and is worth discussing in the final report's limitations section.
- **Fix implemented:** `hybrid_similarity()` in `src/similarity.py` was revised so that when the reference and transcript numbers match exactly, the function now returns a fixed score of **1.0** instead of the raw (and sometimes unreliably low) semantic similarity score. The reasoning: once the numeric content — typically the most important fact in a numeric-answer question — is confirmed correct, there's no need to trust Sentence-BERT's embedding quality for short, low-context numeric strings, which was shown to be unreliable (see the "1893" vs. "1,893" finding above).
  - The full pipeline (Task 12) was re-run with the updated function, regenerating `data/pipeline_results.csv`. Verified the fix directly: "1893" vs. "1,893" now scores 1.0 (previously 0.193), while previously-correct behavior for non-numeric and mismatched-numeric cases remains unaffected.

- Completed manual ground-truth labeling for all 50 rows, judged independently of the system's similarity score (correctness was assessed by comparing `answer` and `transcript` directly, without looking at the `similarity` column, to avoid circular evaluation). Labels were added as a `human_label` column in `data/pipeline_results.csv`.
  - Adopted a consistent labeling policy for borderline cases: proper nouns/names with close phonetic similarity but minor spelling differences (e.g., "Pleurobrachia" vs. "Plorobracia", "William Stranahan" vs. "William Strenohin") were labeled as correct, on the reasoning that they represent close ASR mishearings rather than genuine wrong answers.
- **Initial threshold sweep results** (accuracy against human labels, using `hybrid_similarity` scores from `pipeline_results.csv`):

| Threshold | Accuracy |
|---|---|
| 0.60 | **0.960** (best so far) |
| 0.70 | 0.920 |
| 0.75 | 0.900 |
| 0.80 | 0.880 |
| 0.85 | 0.880 |
| 0.90 | 0.840 |

  - Accuracy decreases as the threshold increases, since many genuinely correct (non-numeric) answers have raw semantic similarity scores well below 0.9, causing them to be incorrectly rejected at higher thresholds.
  - **Open question to resolve next session:** whether raw accuracy is the right metric for selecting the final threshold, or whether precision/recall trade-offs should be considered separately — since false rejections (marking a correct answer wrong) and false acceptances (marking a wrong answer correct) may not be equally costly in this application.

- **Resolved the accuracy-vs-precision/recall question** by computing precision and recall (not just accuracy) at each candidate threshold:

| Threshold | Accuracy | Precision | Recall |
|---|---|---|---|
| 0.60 | **0.960** | 0.977 | **0.977** |
| 0.70 | 0.920 | 0.976 | 0.930 |
| 0.75 | 0.900 | 0.975 | 0.907 |
| 0.80 | 0.880 | 0.974 | 0.884 |
| 0.85 | 0.880 | 1.000 | 0.860 |
| 0.90 | 0.840 | 1.000 | 0.814 |

  - A clear trade-off pattern emerged: higher thresholds improve precision (up to a perfect 1.000 at 0.85–0.90) but steadily reduce recall (down to 0.814 at 0.90), since stricter cutoffs increasingly reject genuinely correct answers whose raw semantic similarity happens to fall below the threshold.
  - **Decision rationale:** before choosing, the two error types were explicitly weighed — a false rejection (marking a correct spoken answer as wrong) unfairly penalizes an individual student, while a false acceptance (marking a wrong answer as correct) undermines the grading system's overall validity and could indirectly disadvantage other students. Both were judged as meaningful costs, with false rejection considered somewhat more directly unfair to the affected student.
  - **Final threshold selected: 0.60** — it achieves the highest accuracy and the best balance of precision and recall (both ≈0.977, nearly equal), avoiding the recall degradation seen at higher thresholds, consistent with prioritizing not unfairly rejecting correct answers.
  - **Limitation acknowledged:** this threshold was tuned on only 50 human-labeled examples; differences between candidate thresholds correspond to just 2–3 disagreements at this sample size, so the selection, while well-reasoned, is not highly statistically robust and could shift with a larger labeled evaluation set. This is noted as a direction for future work.

**Task 14 — Prediction Labels**
- Defined a three-way classification rule using the selected threshold (0.60) with a symmetric ±0.05 margin to create a "Borderline" band: similarity ≥ 0.65 → Correct, ≤ 0.55 → Incorrect, otherwise → Borderline.
- Applied this rule to all 50 rows, adding a `prediction` column to `data/pipeline_results.csv`. Distribution: 41 Correct, 7 Incorrect, 2 Borderline.
- **Validation of the Borderline definition:** the two rows classified as Borderline ("Pleurobrachia" vs. "Plorobracia", and "William Stranahan" vs. "William Strenohin") were exactly the two cases the human labeler had explicitly been uncertain about during manual labeling in Task 13 — proper nouns with close-but-imperfect phonetic matches. This is a meaningful sanity check: the system's numeric uncertainty band independently aligned with genuine human uncertainty, without the classifier having any access to that hesitation, suggesting the Borderline category is capturing genuinely ambiguous cases rather than being an arbitrary numeric band.

**Phase 5 (Complete Pipeline) is now complete.**

### Phase 6 — Evaluation

**Task 15 — Formal Evaluation Script**
- Created `evaluation/evaluate.py`, a standalone script computing accuracy, precision, recall, and F1 score by comparing the pipeline's final predictions against the human-labeled ground truth.
- Decided to treat "Borderline" predictions as "Correct" for the purpose of binary metric calculation, consistent with the project's established preference (from Task 13's threshold discussion) for erring toward not unfairly rejecting ambiguous answers.
- **Final evaluation results (50-example evaluation set):**

| Metric | Score |
|---|---|
| Accuracy | 0.960 |
| Precision | 0.977 |
| Recall | 0.977 |
| F1 Score | 0.977 |

  Precision and recall are nearly identical, reflecting the balanced threshold selection made in Task 13 — the system neither over-rejects correct answers nor over-accepts incorrect ones on this evaluation set.

**Task 16 — Error Analysis**
- Categorized all 9 non-Correct predictions (7 Incorrect, 2 Borderline) by root cause:

| Row | Answer | Transcript | Category |
|---|---|---|---|
| "Lower Lorraine" | → "Lower the rain." | ASR error |
| "10,000 m2" | → "10,000 square meters." | **Semantic/pipeline model error** (correctly transcribed, but the hybrid numeric-matching logic incorrectly rejected it — the known "m2" edge case) |
| "Beyoncé" | → "Be on say." | ASR error |
| "Pleurobrachia" | → "Plorobracia" | ASR error / Ambiguous (Borderline; also uncertain during human labeling) |
| "Mi'kmaq and the Abenaki" | → "Me, Kamek, and I'll be knocking." | ASR error |
| "gas turbines" | → "Gast her buns." | ASR error |
| "Thoreau" | → "Dora." | ASR error |
| "William Stranahan" | → "William Strenohin." | ASR error / Ambiguous (Borderline; also uncertain during human labeling) |
| "Nintendo" | → "念獵獵" (non-Latin script) | ASR error (severe, isolated failure — see investigation below) |

- **Summary: 8 of 9 errors (89%) were ASR errors**, meaning Whisper mistranscribed the spoken answer; only 1 of 9 was a pipeline/model error (the previously documented "m2" numeric-extraction edge case). This indicates the current bottleneck in system accuracy is primarily speech recognition quality (particularly on rare proper nouns and specialized terminology), not the semantic similarity or hybrid scoring logic.
- **Notable validation:** the two Borderline cases were also the two cases the human labeler was genuinely uncertain about, reinforcing that the Borderline category captures real ambiguity (also noted in Task 14).
- **Investigated the severe "Nintendo" → "念獵獵" failure**, hypothesizing it might relate to which TTS engine generated the audio (gTTS vs. pyttsx3). Cross-tabulating predictions by TTS source across all 50 rows showed only a small difference (gTTS: 21 Correct/3 Incorrect/1 Borderline; pyttsx3: 20 Correct/4 Incorrect/1 Borderline) — not a strong enough gap to support a systematic engine-quality effect at this sample size. The Nintendo failure is best characterized as an isolated outlier rather than evidence of a general pyttsx3 weakness.

**Task 17 — Summary Tables**
- Built a confusion matrix comparing final predictions (Correct/Borderline treated as positive) against human labels:

|  | Predicted: Incorrect | Predicted: Correct |
|---|---|---|
| **Actual: Incorrect** | 6 (True Negative) | 1 (False Positive) |
| **Actual: Correct** | 1 (False Negative) | 42 (True Positive) |

  Only 2 misclassifications out of 50 (one of each error type), reflecting the balanced threshold selected in Task 13.
- Consolidated the formal metrics table (Accuracy 0.960, Precision 0.977, Recall 0.977, F1 0.977) and a set of representative example predictions (correct, incorrect, and both borderline cases) alongside the confusion matrix.
- Saved all three as CSV files in `evaluation/`: `metrics_table.csv`, `confusion_matrix.csv`, and `example_predictions.csv`, ready for direct inclusion in the final report.

**Phase 6 (Evaluation) is now complete.**

### Phase 7 — Demo

**Task 18 — Gradio Demo**
- Chose Gradio over Streamlit for the interactive demo, since it is purpose-built for ML input/output types (audio, text) with minimal boilerplate, well-suited to this project's record → transcribe → score → predict workflow.
- Designed the demo around a dropdown of questions drawn from `data/eval_set.csv` (rather than free-text entry), so the reference answer, question, and passage are always consistent and don't require the user to type anything error-prone.
- Built `demo/app.py`, wiring together the full pipeline into a single interactive interface: a question dropdown, a microphone recorder, and five live outputs (passage, reference answer, transcript, similarity score, and Correct/Incorrect/Borderline prediction) using the same `hybrid_similarity()` and threshold logic developed in Phases 4–6.
- **Debugged a significant audio-recording issue:** the demo initially received `None` for every microphone recording, regardless of whether audio was successfully recorded and played back in the browser. Root-caused through a minimal isolated reproduction (a standalone test app with only an audio input) to two contributing factors:
  1. The Gradio app was initially being tested inside VS Code's embedded browser/preview rather than a full external browser — microphone access requires a genuine browser context, which embedded editor previews do not reliably provide.
  2. Explicitly specifying `format="wav"` on the `gr.Audio` component (rather than leaving the format unspecified) was needed for the recorded file to be correctly saved and passed through to the backend.
- Verified the working demo end-to-end with a live example: the reference answer was "1893", and a deliberately incorrect number ("1982") was spoken to test the pipeline's rejection behavior. Whisper correctly transcribed the spoken "1982", and the pipeline correctly scored this as 0.000 similarity and classified it as "Incorrect" — confirming `hybrid_similarity()`'s numeric-mismatch logic works correctly on live, real-time microphone input, not just the pre-recorded evaluation set.

---

## Next Steps

- **Task 19** — Improve the demo interface: better layout, error messages (e.g., handling when no audio is recorded), and a reset button.

---

## Working Method

Progress is tracked against a 22-task checklist, worked one task per session (~60 minutes each), with short breaks between sessions to maintain steady, sustainable progress.