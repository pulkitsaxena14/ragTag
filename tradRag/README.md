# Traditional RAG Pipeline

A lightweight Retrieval-Augmented Generation (RAG) system for question answering over PDF documents. The pipeline extracts content from PDF files, performs section-aware chunking, generates embeddings, and stores them in a vector database. At query time, a custom query rewriter enhances user queries before retrieving relevant content through a hybrid retrieval strategy that combines semantic vector search and BM25 keyword search. Retrieved results are then reranked using a BGE reranker before being used to generate answers.

---

## Features

* **PDF Parsing** using Docling
* **Section-Based Chunking** to preserve document structure and context
* **Embedding Generation** for semantic retrieval
* **Vector Database Storage** for efficient similarity search
* **Custom Query Rewriter** for retrieval optimization
* **Hybrid Search**

  * Dense vector similarity search
  * BM25 keyword-based retrieval
* **BGE Reranker** for improved relevance ranking
* **Context-Aware Answer Generation**

---

## Prerequisites

* Python 3.10+
* Conda (recommended)

---

## Installation

### 1. Activate the Conda Environment

```bash
conda activate ragTag
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Step 1: Parse PDF Documents

Extract and process PDF content using Docling.

```bash
python src/parse_pdfs.py
```

### Step 2: Build the Retrieval Index

Generate embeddings and index document chunks in the vector database.

```bash
python src/index_documents.py
```

### Step 3: Start the RAG Application

Launch the question-answering pipeline.

```bash
python src/main.py
```
---
## Tests

> **Test Query**: "Top research priorities/areas/domains/projects"