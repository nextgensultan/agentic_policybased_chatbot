from typing import List, Dict, Any
import numpy as np
import faiss
from langchain_huggingface import HuggingFaceEndpoint
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

RETURN_POLICIES = [
    {
        "id": "general_policy",
        "title": "General Return Policy",
        "content": """
        General Return Policy:
        - Items can be returned within 30 days of purchase for a full refund.
        - Items must be in original condition with all original packaging and tags.
        - Return shipping fees are the customer's responsibility unless the item is defective or was shipped incorrectly.
        - Gift returns will be issued as store credit to the recipient.
        """
    },
    {
        "id": "refund_process",
        "title": "Refund Process & Timeframes",
        "content": """
        Refund Process & Timeframes:
        - Refunds are processed within 5-7 business days after receipt of returned items.
        - Original payment method will be refunded when possible.
        - Store credit will be issued if original payment method is unavailable or expired.
        - Shipping costs are non-refundable unless the item was defective or incorrect.
        - Expedited shipping fees are non-refundable even if the item is returned.
        """
    }
]

class FAISSReturnPolicyKnowledgeBase:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", "!", "?", ";", ":", " ", ""]
        )
        
        self.document_chunks = []
        
        for policy in RETURN_POLICIES:
            # Split the policy content into chunks
            chunks = text_splitter.split_text(policy["content"])
            
            # Add each chunk to our list
            for chunk in chunks:
                self.document_chunks.append({
                    "content": chunk.strip(),
                    "source": policy["id"],
                    "title": policy["title"]
                })

        # Create FAISS index
        self._create_faiss_index()
        
        print(f"Created FAISS knowledge base with {len(self.document_chunks)} chunks from {len(RETURN_POLICIES)} policy documents")
    
    def _create_faiss_index(self):
        if not self.document_chunks:
            raise ValueError("No document chunks to index")
            
        # Generate embeddings for all chunks
        texts = [chunk["content"] for chunk in self.document_chunks]
        self.embeddings = self.embedding_model.encode(texts)
        
        # Normalize the vectors
        faiss.normalize_L2(self.embeddings)
        
        self.dimension = self.embeddings.shape[1]  # Get the embedding dimension
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(self.embeddings)
    
    def search_policy(self, query: str, k: int = 3) -> List[Dict[str, Any]]:

        query_embedding = self.embedding_model.encode([query])[0]
        faiss.normalize_L2(np.array([query_embedding]))
        distances, indices = self.index.search(np.array([query_embedding]), k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.document_chunks):
                chunk = self.document_chunks[idx]
                results.append({
                    "content": chunk["content"],
                    "source": chunk["source"],
                    "title": chunk["title"],
                    "score": float(distances[0][i])  
                })
        
        return results
    
    def get_all_policies(self) -> List[Dict[str, str]]:
        return RETURN_POLICIES

# Create a singleton instance of the knowledge base
return_policy_kb = None

def get_return_policy_kb():
    global return_policy_kb
    if return_policy_kb is None:
        return_policy_kb = FAISSReturnPolicyKnowledgeBase()
    return return_policy_kb

def search_return_policy(query: str) -> dict:

    kb = get_return_policy_kb()
    results = kb.search_policy(query)
    
    if not results:
        return {"policy": "No specific policy information found for your query."}
    
    # Format the response
    response = {"policy": []}
    for result in results:
        response["policy"].append({
            "content": result["content"].strip(),
            "category": result["title"],
            "relevance_score": result["score"]
        })
    
    return response