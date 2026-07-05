from pathlib import Path

try:
    # pyrefly: ignore [missing-import]
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

BASE_DIR = Path(__file__).resolve().parent.parent


class IngestionPipeline:
    """Ingestion pipeline that loads documents, splits them, and stores embeddings in FAISS."""

    def __init__(self, data_dir=None, persist_dir=None, embeddings_model="sentence-transformers/all-MiniLM-L6-v2"):
        self.data_dir = Path(data_dir or BASE_DIR / "data")
        self.persist_dir = Path(persist_dir or BASE_DIR / "db")
        self.embeddings_model = embeddings_model

    def run(self):
        """Execute the ingestion pipeline."""
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data source path does not exist: {self.data_dir}")

        documents = []
        if self.data_dir.is_file():
            files_to_load = [self.data_dir]
        else:
            files_to_load = list(self.data_dir.glob("**/*"))

        for file_path in files_to_load:
            if not file_path.is_file():
                continue
            suffix = file_path.suffix.lower()
            if suffix == ".txt":
                try:
                    loader = TextLoader(str(file_path), encoding="utf-8")
                    documents.extend(loader.load())
                except Exception as e:
                    print(f"Error loading TXT file {file_path}: {e}")
            elif suffix == ".pdf":
                try:
                    loader = PyPDFLoader(str(file_path))
                    documents.extend(loader.load())
                except Exception as e:
                    print(f"Error loading PDF file {file_path}: {e}")

        if not documents:
            raise ValueError(f"No documents found to load in {self.data_dir}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = splitter.split_documents(documents)

        print(f"Generating embeddings using {self.embeddings_model}...")
        embeddings = HuggingFaceEmbeddings(model_name=self.embeddings_model)
        vectorstore = FAISS.from_documents(chunks, embeddings)

        self.persist_dir.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(self.persist_dir))

        print(f"Ingestion Pipeline Complete: Stored {len(chunks)} chunks in {self.persist_dir}")
        return vectorstore


def ingest_documents(data_path=None, persist_dir=None):
    """Wrapper function for backward compatibility."""
    pipeline = IngestionPipeline(data_dir=data_path, persist_dir=persist_dir)
    return pipeline.run()


if __name__ == "__main__":
    pipeline = IngestionPipeline()
    pipeline.run()