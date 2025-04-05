import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import uuid
from typing import List, Dict, Any, Optional

class VectorDB:
    
    def __init__(self, index_name: str = "expungement-questions"):
        self.index_name = index_name
        self.dimension = 384
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = self._initialize_faiss_index()  # FAISS requires float32 arrays.
        self.id_to_metadata: Dict[str, Dict[str, Any]] = {} # Dictionaries to map between our UUIDs and FAISS numeric IDs, and to store metadata.
        self.id_to_vector_id: Dict[str, int] = {}
        self.vector_id_to_id: Dict[int, str] = {}
        self.next_vector_id = 0  # counter for unique integer IDs

    def _initialize_faiss_index(self):
        # Use IndexFlatIP for cosine similarity. We wrap it in an IndexIDMap for ID management.
        base_index = faiss.IndexFlatIP(self.dimension)
        index = faiss.IndexIDMap(base_index)
        print("FAISS index initialized.")
        return index

    def _generate_embedding(self, text: str) -> List[float]:
        embedding = self.embedding_model.encode(text) 
        embedding = np.array(embedding, dtype='float32') # Convert embedding to a numpy array of type float32.
        norm = np.linalg.norm(embedding) # Normalize to unit length so that inner product equals cosine similarity.
        if norm > 0:
            embedding = embedding / norm
        return embedding.tolist()

    def add_question(self, question: str) -> str:
        question_id = str(uuid.uuid4())
        question_embedding = self._generate_embedding(question)
        vector = np.array([question_embedding], dtype='float32')
        # Use the next available integer as the FAISS vector ID.
        vector_id = self.next_vector_id
        self.next_vector_id += 1
        self.index.add_with_ids(vector, np.array([vector_id], dtype='int64'))
        # Store metadata and mappings.
        self.id_to_metadata[question_id] = {"question_text": question}
        self.id_to_vector_id[question_id] = vector_id
        self.vector_id_to_id[vector_id] = question_id
        return question_id

    def add_questions(self, questions: List[str]) -> List[str]:
        question_ids = []
        vectors = []
        vector_ids = []
        for question in questions:
            question_id = str(uuid.uuid4())
            question_ids.append(question_id)
            question_embedding = self._generate_embedding(question)
            vectors.append(question_embedding)
            vector_id = self.next_vector_id
            self.next_vector_id += 1
            vector_ids.append(vector_id)
            # Store metadata and mappings.
            self.id_to_metadata[question_id] = {"question_text": question}
            print(f"The metadata is this?: {self.id_to_metadata[question_id]}")
            self.id_to_vector_id[question_id] = vector_id
            self.vector_id_to_id[vector_id] = question_id
        #Batches embeddings to FAISS
        vectors_np = np.array(vectors, dtype='float32')
        vector_ids_np = np.array(vector_ids, dtype='int64')
        self.index.add_with_ids(vectors_np, vector_ids_np)
        return question_ids

    def get_question_by_id(self, question_id: str) -> Optional[str]:
        if question_id in self.id_to_metadata:
            return self.id_to_metadata[question_id].get("question_text")
        else:
            print(f"Question with ID {question_id} not found")
            return None

    def delete_question(self, question_id: str) -> bool:
        if question_id in self.id_to_vector_id:
            vector_id = self.id_to_vector_id[question_id]
            try:
                # FAISS supports deletion via remove_ids; we pass an array of IDs.
                self.index.remove_ids(np.array([vector_id], dtype='int64'))
                # Clean up our internal mappings.
                del self.id_to_metadata[question_id]
                del self.id_to_vector_id[question_id]
                del self.vector_id_to_id[vector_id]
                print(f"Deleted question {question_id}")
                return True
            except Exception as e:
                print(f"Error deleting question: {e}")
                return False
        else:
            print(f"Question with ID {question_id} not found")
            return False

    def search_questions(self, context: str, top_k: int) -> List[Dict[str, Any]]:
        try:
            context_embedding = self._generate_embedding(context)
            vector = np.array([context_embedding], dtype='float32')
            # Perform the search; D holds similarity scores, I holds FAISS vector IDs.
            D, I = self.index.search(vector, top_k)
            print(type(D))
            print(f"{D} holds similarity scores and {I} are the vector IDs")
            results = []
            for score, vector_id in zip(D[0], I[0]):
                if vector_id == -1:  # -1 indicates no result.
                    continue
                question_id = self.vector_id_to_id.get(vector_id)
                metadata = self.id_to_metadata.get(question_id, {})
                results.append({
                    'id': question_id,
                    'question': metadata.get("question_text", ""),
                    'score': float(score)
                })
            return results
        except Exception as e:
            print(f"Error searching questions: {e}")
            return []

    def search_with_context(self, context: str):
        matching_questions = self.search_questions(context=context, top_k=3)
        print(f"Matching questions of 0 is {matching_questions[0]} and matching questions of 1 is {matching_questions[1]} and 3 {matching_questions[2]}")
        return matching_questions[0] if matching_questions else None #could just return the matching_questions array, need to change the variable type on other end
