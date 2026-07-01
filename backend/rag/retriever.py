from langchain_community.vectorstores import (
    FAISS
)

from backend.rag.vectorstore import (
    get_embeddings
)


class KnowledgeRetriever:

    def __init__(self):

        self.db = FAISS.load_local(
            "vectorstore",
            get_embeddings(),
            allow_dangerous_deserialization=True
        )

    def retrieve(
        self,
        query: str,
        k: int = 3
    ) -> str:

        docs = self.db.similarity_search(
            query,
            k=k
        )

        return "\n\n".join(
            [
                doc.page_content
                for doc in docs
            ]
        )