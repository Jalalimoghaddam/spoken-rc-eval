import torch
import numpy as np
import pandas as pd
import sklearn
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer

print("Python packages OK")
print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())