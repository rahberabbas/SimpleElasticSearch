# SimpleElasticSearch

A lightweight search engine inspired by Elasticsearch, with inverted indexing and TF-IDF ranking.

## Features

- **Document Indexing**: Create and maintain an inverted index for efficient text searching
- **TF-IDF Ranking**: Results ranked by Term Frequency-Inverse Document Frequency algorithm
- **Phrase Queries**: Support for exact phrase matching
- **Field-Specific Search**: Target specific document fields in your queries
- **Query Caching**: Improved performance through phrase query caching
- **RESTful API**: Simple API endpoints for indexing and searching
- **Scalable Architecture**: Designed with scalability in mind

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/simpleelasticsearch.git
cd simpleelasticsearch
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

4. Apply migrations:
```bash
python manage.py migrate
```

5. Run the development server:
```bash
python manage.py runserver
```

## API Usage

### Indexing Documents

To index a document:

```http
POST /index/
Content-Type: application/json

{
  "id": "1",
  "title": "quick fox",
  "data": "A fox is usually quick and brown."
}
```

Response:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": "1",
  "title": "quick fox",
  "data": "A fox is usually quick and brown."
}
```

### Searching Documents

#### Basic Search

```http
GET /search/?q=quick%20fox
```

Response:
```json
[
  {
    "id": "1",
    "title": "quick fox",
    "data": "A fox is usually quick and brown."
  },
  {
    "id": "2",
    "title": "lazy dog",
    "data": "A quick brown fox jumped over lazy dog. A fox is always jumping."
  }
]
```

#### Field-Specific Search

```http
GET /search/?q=fox&field=title
```

Response:
```json
[
  {
    "id": "1",
    "title": "quick fox",
    "data": "A fox is usually quick and brown."
  }
]
```

#### Phrase Search

```http
GET /search/?q="lazy%20dog"&phrase=true
```

Response:
```json
[
  {
    "id": "2",
    "title": "lazy dog",
    "data": "A quick brown fox jumped over lazy dog. A fox is always jumping."
  }
]
```

## How It Works

### Architecture

The system is built on three main components:

1. **Indexer**: Processes documents, extracts terms, and builds the inverted index.
2. **Storage**: Manages on-disk storage of documents and index data.
3. **Searcher**: Performs search operations and ranks results.

### Indexing Process

1. Documents are tokenized, with stopwords and punctuation removed.
2. Each term's frequency (TF) is calculated for scoring.
3. Terms are mapped to documents in the inverted index.
4. Document frequencies are tracked for IDF calculation.

### Search Process

1. The search query is tokenized and preprocessed.
2. Terms are looked up in the inverted index.
3. Results are ranked using TF-IDF scoring.
4. For phrase queries, positional information is used to verify adjacent terms.

## Scalability Considerations

The system is designed with scalability in mind:

- **Document Storage**: Each document is stored in a separate file for efficient access
- **Memory Management**: Index structures are optimized for memory efficiency
- **Concurrency**: Thread-safe operations for multiple simultaneous requests
- **Distributed Potential**: The architecture allows for sharding by term partitioning

## Technical Details

### TF-IDF Calculation

The system uses TF-IDF (Term Frequency-Inverse Document Frequency) to rank search results:

- **Term Frequency (TF)**: How often a term appears in a document
- **Inverse Document Frequency (IDF)**: How rare a term is across all documents

The formula used is:
```
Score = TF × IDF
where:
TF = (Term count in document) / (Total terms in document)
IDF = log(Total documents / Documents containing term)
```

### Inverted Index Structure

The inverted index maps terms to documents, with additional information for scoring:

```
{
  "term1": {
    "doc1": {"title_tf": 0.1, "data_tf": 0.05},
    "doc2": {"title_tf": 0.0, "data_tf": 0.03}
  },
  "term2": {
    "doc1": {"title_tf": 0.05, "data_tf": 0.02}
  }
}
```

## Future Improvements

- Implement stemming/lemmatization for better matching
- Add support for fuzzy search and typo correction
- Implement document boosting and query weighting
- Add distributed indexing and search capabilities
- Support for more complex boolean queries (AND, OR, NOT)
