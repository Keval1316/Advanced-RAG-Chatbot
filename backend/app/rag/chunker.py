import uuid
from typing import List
from backend.app.core.config import settings
from backend.app.rag.parser import PageContent
from backend.app.schemas.document import ChunkMetadata


class RecursiveChunker:
    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
        separators: List[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        final_chunks = []
        if not separators:
            return [text]

        separator = separators[0]
        new_separators = separators[1:]

        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)

        current_doc = []
        total = 0

        for s in splits:
            s_len = len(s) + (len(separator) if current_doc else 0)
            if total + s_len <= self.chunk_size:
                current_doc.append(s)
                total += s_len
            else:
                if current_doc:
                    joined = separator.join(current_doc)
                    if joined.strip():
                        final_chunks.append(joined.strip())
                    
                    # Compute overlap from previous chunks
                    overlap_doc = []
                    overlap_len = 0
                    for prev in reversed(current_doc):
                        if overlap_len + len(prev) + len(separator) <= self.chunk_overlap:
                            overlap_doc.insert(0, prev)
                            overlap_len += len(prev) + len(separator)
                        else:
                            break
                    current_doc = overlap_doc
                    total = overlap_len

                if len(s) > self.chunk_size and new_separators:
                    sub_chunks = self._split_text(s, new_separators)
                    final_chunks.extend(sub_chunks)
                else:
                    current_doc.append(s)
                    total += len(s)

        if current_doc:
            joined = separator.join(current_doc)
            if joined.strip():
                final_chunks.append(joined.strip())

        return final_chunks

    def chunk_pages(
        self,
        pages: List[PageContent],
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        filename: str
    ) -> List[ChunkMetadata]:
        all_chunks: List[ChunkMetadata] = []
        chunk_idx = 0

        for page in pages:
            text_chunks = self._split_text(page.text, self.separators)
            for raw_chunk in text_chunks:
                clean_chunk = raw_chunk.strip()
                if not clean_chunk:
                    continue

                chunk_id = f"{document_id}_p{page.page_number}_c{chunk_idx}"
                metadata = ChunkMetadata(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    user_id=user_id,
                    knowledge_base_id=knowledge_base_id,
                    filename=filename,
                    page_number=page.page_number,
                    chunk_index=chunk_idx,
                    text=clean_chunk
                )
                all_chunks.append(metadata)
                chunk_idx += 1

        return all_chunks


chunker = RecursiveChunker()
