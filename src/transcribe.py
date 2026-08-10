import pandas as pd
from faster_whisper import WhisperModel

model = WhisperModel("tiny", device="cpu", compute_type="int8")

def transcribe_audio(audio_path, model):
    segments, info = model.transcribe(audio_path)
    text_pieces = []
    for segment in segments:
        text_pieces.append(segment.text.strip())
    full_text = " ".join(text_pieces)
    return full_text

manifest = pd.read_csv("data/audio_manifest.csv")

transcripts = []
for i, row in manifest.iterrows():
    audio_path = row["audio_path"]
    transcript = transcribe_audio(audio_path, model)
    transcripts.append(transcript)

manifest["transcript"] = transcripts
manifest.to_csv("data/transcript.csv", index=False)