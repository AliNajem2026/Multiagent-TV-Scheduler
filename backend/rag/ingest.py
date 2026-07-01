from pathlib import Path

from langchain_core.documents import Document

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from backend.rag.vectorstore import (
    create_vectorstore
)


DATA_DIR = Path("data")


def load_documents():

    documents = []

    for file in DATA_DIR.glob("*.txt"):

        content = file.read_text(
            encoding="utf-8"
        )

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "source": file.name
                }
            )
        )

    return documents


def ingest():

    docs = load_documents()

    splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
    )

    chunks = splitter.split_documents(
        docs
    )

    create_vectorstore(chunks)

    print(
        f"Indexed {len(chunks)} chunks"
    )


if __name__ == "__main__":

    ingest()