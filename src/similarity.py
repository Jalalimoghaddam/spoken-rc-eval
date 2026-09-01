import re
from sentence_transformers import SentenceTransformer, util


model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_numbers(text):
    text = re.sub(r'(\d),(\d{3})', r'\1\2', text)
    numbers = re.findall(r'\d+', text)
    return set(numbers)



def hybrid_similarity(reference_answer, transcript, model):
    semantic_sim = util.cos_sim(model.encode(reference_answer), model.encode(transcript)).item()

    ref_numbers = extract_numbers(reference_answer)
    trans_numbers = extract_numbers(transcript)

    if len(ref_numbers) == 0:
        return semantic_sim
    else:
        if ref_numbers == trans_numbers:
            return 1.0
        else:
            return 0

if __name__ == "__main__":
   
    result = hybrid_similarity("It was founded in 1852", "The museum opened in 1852", model)
    print(f"Similarity: {result:.3f}")