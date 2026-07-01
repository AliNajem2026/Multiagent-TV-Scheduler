from langchain_community.vectorstores import FAISS

from langchain_huggingface import (
    HuggingFaceEmbeddings
)


def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def create_vectorstore(documents):

    embeddings = get_embeddings()

    vectorstore = FAISS.from_documents(
        documents,
        embeddings
    )

    vectorstore.save_local(
        "vectorstore"
    )

    return vectorstore