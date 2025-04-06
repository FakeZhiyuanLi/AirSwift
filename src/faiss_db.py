import faiss
import numpy as np
import uuid
from typing import List, Dict, Any, Optional
from openai import OpenAI
from utils import get_openai_key

class VectorDB:
    
    def __init__(self, index_name: str = "airswift"):
        self.index_name = index_name
        self.dimension = 1536
        self.embedding_model = "text-embedding-ada-002"
        self.openai_client = OpenAI(api_key=get_openai_key())
        self.index = self._initialize_faiss_index()
        self.id_to_metadata: Dict[str, Dict[str, Any]] = {}
        self.id_to_vector_id: Dict[str, int] = {}
        self.vector_id_to_id: Dict[int, str] = {}
        self.next_vector_id = 0

    def _initialize_faiss_index(self):
        base_index = faiss.IndexFlatIP(self.dimension)
        index = faiss.IndexIDMap(base_index)
        print("FAISS index initialized.")
        return index

    def _generate_embedding(self, text: str) -> List[float]:
        print(text)
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=[text]
        )
        embedding_values = response.data[0].embedding
        embedding_array = np.array(embedding_values, dtype=np.float32)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_array = embedding_array / norm
        response = embedding_array.tolist()
        #print(f"The array.tolist is: {response}")
        return response

    def add_document(self, document: str) -> str:
        document_id = str(uuid.uuid4())
        document_embedding = self._generate_embedding(document)
        vector = np.array([document_embedding], dtype='float32')
        vector_id = self.next_vector_id
        self.next_vector_id += 1
        self.index.add_with_ids(vector, np.array([vector_id], dtype='int64'))
        self.id_to_metadata[document_id] = {"document_text": document}
        self.id_to_vector_id[document_id] = vector_id
        self.vector_id_to_id[vector_id] = document_id
        return document_id

    def add_documents(self, documents: List[str]) -> List[str]:
        document_ids = []
        vectors = []
        vector_ids = []
        for document in documents:
            document_id = str(uuid.uuid4())
            document_ids.append(document_id)
            document_embedding = self._generate_embedding(document)
            vectors.append(document_embedding)
            vector_id = self.next_vector_id
            self.next_vector_id += 1
            vector_ids.append(vector_id)
            self.id_to_metadata[document_id] = {"document_text": document}
            self.id_to_vector_id[document_id] = vector_id
            self.vector_id_to_id[vector_id] = document_id
        vectors_np = np.array(vectors, dtype='float32')
        vector_ids_np = np.array(vector_ids, dtype='int64')
        self.index.add_with_ids(vectors_np, vector_ids_np)
        return document_ids

    def get_document_by_id(self, document_id: str) -> Optional[str]:
        if document_id in self.id_to_metadata:
            return self.id_to_metadata[document_id].get("document_text")
        else:
            print(f"Document with ID {document_id} not found")
            return None

    def delete_document(self, document_id: str) -> bool:
        if document_id in self.id_to_vector_id:
            vector_id = self.id_to_vector_id[document_id]
            try:
                self.index.remove_ids(np.array([vector_id], dtype='int64'))
                del self.id_to_metadata[document_id]
                del self.id_to_vector_id[document_id]
                del self.vector_id_to_id[vector_id]
                print(f"Deleted document {document_id}")
                return True
            except Exception as e:
                print(f"Error deleting document: {e}")
                return False
        else:
            print(f"Document with ID {document_id} not found")
            return False

    def search_documents(self, context: str, top_k: int) -> List[Dict[str, Any]]:
        try:
            context_embedding = self._generate_embedding(context)
            vector = np.array([context_embedding], dtype='float32')
            D, I = self.index.search(vector, top_k)
            results = []
            for score, vector_id in zip(D[0], I[0]):
                if vector_id == -1:
                    continue
                document_id = self.vector_id_to_id.get(vector_id)
                metadata = self.id_to_metadata.get(document_id, {})
                results.append({
                    'id': document_id,
                    'document': metadata.get("document_text", ""),
                    'score': float(score)
                })
            return results
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []

    def search_with_context(self, context: str):
        matching_documents = self.search_documents(context=context, top_k=3)
        if len(matching_documents) >= 3:
            print(f"Top matches:\n1: {matching_documents[0]}\n2: {matching_documents[1]}\n3: {matching_documents[2]}")
        return matching_documents[0] if matching_documents else None
