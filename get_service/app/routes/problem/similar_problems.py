# import openai
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import numpy as np
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

model = SentenceTransformer('all-MiniLM-L6-v2')
class VectorStore:
    def __init__(self, dim:int=384, index_path:str="/faiss_data/problems.index"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index_path = index_path
        self.dim = dim
        self.index = faiss.IndexFlatL2(self.dim)
        self.id_map = {}  # maps FAISS idx to DB id

    def embed(self, text: str) -> np.ndarray: # type: ignore
        return self.model.encode([text])[0]# type: ignore

    def add(self, db_id: int, text: str):# type: ignore
        vector = self.embed(text).astype("float32")# type: ignore
        faiss_id = self.index.ntotal# type: ignore
        self.index.add(np.array([vector]))# type: ignore
        self.id_map[faiss_id] = db_id# type: ignore

    def search(self, text: str, problem_id:int, k:int=5)->List[int]:
        vector = self.embed(text).astype("float32")# type: ignore
        D, I = self.index.search(np.array([vector]), k)# type: ignore
        return [self.id_map[i] for i in I[0] if i in self.id_map and self.id_map[i]!=problem_id]# type: ignore

    def save(self):
        faiss.write_index(self.index, self.index_path)# type: ignore

    def load(self)->None:
        self.index = faiss.read_index(self.index_path)# type: ignore

vector_store = VectorStore()