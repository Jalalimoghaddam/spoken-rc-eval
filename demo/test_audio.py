import gradio as gr

def test_audio(audio_path):
    print("Received:", audio_path)
    return str(audio_path)

demo = gr.Interface(
    fn=test_audio,
    inputs=gr.Audio(sources=["microphone"], type="filepath"),
    outputs="text"
)

demo.launch()