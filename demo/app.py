import gradio as gr
import pandas as pd
import sys
sys.path.append("src")

from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer
from similarity import hybrid_similarity

# بارگذاری مدل‌ها و داده - فقط یک‌بار
whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
eval_set = pd.read_csv("data/eval_set.csv")

question_list = eval_set["question"].tolist()


def transcribe_audio(audio_path):
    segments, info = whisper_model.transcribe(audio_path)
    text_pieces = [seg.text.strip() for seg in segments]
    return " ".join(text_pieces)


def classify(similarity):
    if similarity >= 0.65:
        return "Correct"
    elif similarity <= 0.55:
        return "Incorrect"
    else:
        return "Borderline"


def process(selected_question, audio_path):
    
    print("DEBUG audio_path type:", type(audio_path))
    print("DEBUG audio_path value:", audio_path)

    row = eval_set[eval_set["question"] == selected_question].iloc[0]
    ...
    row = eval_set[eval_set["question"] == selected_question].iloc[0]
    reference_answer = row["answer"]
    passage = row["passage"]

    transcript = transcribe_audio(audio_path)
    similarity = hybrid_similarity(reference_answer, transcript, sbert_model)
    prediction = classify(similarity)

    return passage, reference_answer, transcript, f"{similarity:.3f}", prediction

demo = gr.Interface(
    fn=process,
    inputs=[
        gr.Dropdown(choices=question_list, label="Select a question"),
        gr.Audio(sources=["microphone"], type="filepath", format="wav", label="Record your answer"),
    ],
    outputs=[
        gr.Textbox(label="Passage"),
        gr.Textbox(label="Reference Answer"),
        gr.Textbox(label="Transcript (from Whisper)"),
        gr.Textbox(label="Similarity Score"),
        gr.Textbox(label="Prediction"),
    ],
    title="Spoken Reading Comprehension Evaluator",
    description="Select a question, record your spoken answer, and see how the system evaluates it.",
)

demo.launch()