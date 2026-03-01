"""
Document Processor — extracts and chunks text from uploaded files
"""

import io
from typing import Optional


class Document:
    def __init__(self, filename: str, content: str, doc_type: str):
        self.filename = filename
        self.content = content
        self.doc_type = doc_type  # financial | legal | news | esg | other

    def __repr__(self):
        return f"Document({self.filename}, {len(self.content)} chars, {self.doc_type})"


def detect_doc_type(filename: str, content: str) -> str:
    name = filename.lower()
    text = content.lower()

    if any(k in name for k in ["financial", "annual", "10k", "10-k", "balance", "income", "revenue", "earnings"]):
        return "financial"
    if any(k in name for k in ["legal", "filing", "lawsuit", "contract", "regulatory", "sec", "compliance"]):
        return "legal"
    if any(k in name for k in ["news", "article", "press", "media", "release"]):
        return "news"
    if any(k in name for k in ["esg", "sustainability", "environment", "governance", "social"]):
        return "esg"

    # Content-based detection
    financial_keywords = ["revenue", "net income", "ebitda", "cash flow", "balance sheet", "earnings per share"]
    legal_keywords = ["whereas", "hereby", "plaintiff", "defendant", "litigation", "regulatory", "compliance"]
    news_keywords = ["according to", "reported", "announced", "sources say", "ceo said"]
    esg_keywords = ["carbon", "emissions", "diversity", "governance", "sustainability", "environmental"]

    scores = {
        "financial": sum(1 for k in financial_keywords if k in text),
        "legal": sum(1 for k in legal_keywords if k in text),
        "news": sum(1 for k in news_keywords if k in text),
        "esg": sum(1 for k in esg_keywords if k in text),
    }

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


class DocumentProcessor:
    def process_files(self, file_data: list) -> list[Document]:
        documents = []
        for f in file_data:
            try:
                content = self._extract_text(f["filename"], f["content"], f.get("content_type", ""))
                if content.strip():
                    doc_type = detect_doc_type(f["filename"], content)
                    documents.append(Document(
                        filename=f["filename"],
                        content=content[:50000],  # cap at 50k chars per doc
                        doc_type=doc_type
                    ))
            except Exception as e:
                print(f"Error processing {f['filename']}: {e}")
        return documents

    def _extract_text(self, filename: str, content: bytes, content_type: str) -> str:
        name = filename.lower()

        if name.endswith(".pdf") or "pdf" in content_type:
            return self._extract_pdf(content)
        elif name.endswith(".txt") or "text" in content_type:
            return content.decode("utf-8", errors="ignore")
        elif name.endswith(".json"):
            import json
            data = json.loads(content.decode("utf-8", errors="ignore"))
            return json.dumps(data, indent=2)
        else:
            # Try as plain text
            return content.decode("utf-8", errors="ignore")

    def _extract_pdf(self, content: bytes) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            texts = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    texts.append(t)
            return "\n\n".join(texts)
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""
