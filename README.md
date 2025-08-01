# RushDB Examples

[![RushDB Logo](https://raw.githubusercontent.com/rush-db/rushdb/main/rushdb-logo.svg)](https://rushdb.com)

> **The Instant Graph Database for Modern Apps**

This repository contains comprehensive code samples and projects demonstrating quick integration with [RushDB](https://rushdb.com) across various use cases and programming languages.

## About RushDB

RushDB transforms how you work with graph data — no schema required, no complex queries, just push your data and go. Built on top of Neo4j, RushDB provides:

- **🚀 Instant Setup**: Be productive in seconds, not days
- **📝 Push Any JSON**: Nested objects are automatically normalized into a graph
- **🔄 Fractal API**: Same query syntax everywhere - learn once, use everywhere
- **🔍 Vector Search**: Comprehensive similarity search for AI-powered applications
- **⚡ Zero Schema Headaches**: We handle the data structure so you can focus on building

### Key Links

- [🌐 Website](https://rushdb.com/)
- [📖 Documentation](https://docs.rushdb.com/)
- [☁️ Cloud Platform](https://app.rushdb.com/)
- [🐙 GitHub Repository](https://github.com/rush-db/rushdb)
- [🐦 Follow on X (Twitter)](https://x.com/RushDatabase)

## Prerequisites

Before running any examples, you'll need to obtain a RushDB API token:

### 1. Get Your RushDB API Token

1. **Sign up for RushDB Cloud** (Free tier available):

   - Visit [app.rushdb.com](https://app.rushdb.com/)
   - Create a new account or sign in with Google OAuth
   - Navigate to your workspace dashboard

2. **Create API Token**:

   - Go to your workspace settings
   - Generate a new API token
   - Copy the token (format: `rushdb_***`)

3. **Set Environment Variable**:

   ```bash
   export RUSHDB_API_TOKEN="your_token_here"
   ```

   Or create a `.env` file in your project:

   ```env
   RUSHDB_API_TOKEN=your_token_here
   ```

### 2. Alternative: Self-Hosted Setup

If you prefer to self-host RushDB:

```bash
docker run -p 3000:3000 \
  --name rushdb \
  -e NEO4J_URL='neo4j+s://your-instance.neo4j.io' \
  -e NEO4J_USERNAME='neo4j' \
  -e NEO4J_PASSWORD='password' \
  rushdb/platform
```

**Requirements for self-hosting:**

- Neo4j version 5.25.1 or higher
- APOC Plugin (required)
- Graph Data Science Plugin (for vector search)

## Available Examples

### Backend APIs

- **[Express REST API](./express-rushdb-sdk)** | [📝 README](./express-rushdb-sdk/README.md)

  Complete REST API built with Express and TypeScript showcasing RushDB SDK integration.
  Features hierarchical data modeling (Company → Department → Employee), CRUD operations, advanced aggregation queries, and comprehensive endpoint examples with Postman collection.

### Frontend Applications

- **[Next.js Dynamic Filters Demo](./nextjs-filters-rushdb-sdk)** | [📝 README](./nextjs-filters-rushdb-sdk/README.md)

  Interactive Next.js application demonstrating dynamic UI components with RushDB integration.
  Features real-time filtering, search functionality, server-side pagination, data grid visualization, and debug tools for tracking RushDB operations.

- **[Next.js CMS](./nextjs-cms)** | [📝 README](./nextjs-cms/README.md)

  Content Management System built with Next.js and RushDB.
  Features page management, post creation, media handling, and administrative dashboard functionality.

- **[Next.js Simple Waitlist](./nextjs-simple-waitlist)** | [📝 README](./nextjs-simple-waitlist/README.md)

  Clean and responsive waitlist application built with Next.js and RushDB.
  Features email validation, duplicate prevention, RushDB integration for data storage.

- **[Vite React Form](./vite-react-useForm)** | [📝 README](./vite-react-useForm/README.md)

  Professional registration form built with Vite, React, and TypeScript using React Hook Form and Zod validation.
  Features comprehensive form validation, dynamic skill management, complex nested data structures, mock data filling, and seamless RushDB integration for data storage.

- **[Nuxt Auth](./nuxt-auth-rushdb-sdk)** | [📝 README](./nuxt-auth-rushdb-sdk/README.md)

  A minimal Nuxt 3 application demonstrating user registration, login, protected routes, and data persistence using RushDB.
  Passwords are salted with HMAC-SHA256 (using an environment secret) and stored in RushDB. JWT tokens are set as HTTP-only cookies.

### AI & RAG Applications

- **[Simple Python RAG](./python-simple-rag)** | [📝 README](./python-simple-rag/README.md)

  Minimal RAG (Retrieval-Augmented Generation) implementation using RushDB for vector storage.
  Features document ingestion, automatic chunking, vector embeddings with sentence transformers, semantic search, and FastAPI interface.

- **[Generic Books RAG API](./python-books-rag)** | [📝 README](./python-books-rag/README.md)

  Advanced RAG system for processing any text records in RushDB.
  Features generic record vectorization, embedding integration directly into existing records, vector similarity search, and scalable FastAPI architecture.

- **[Express.js Generic Books RAG API](./express-books-rag)** | [📝 README](./express-books-rag/README.md)

  Advanced RAG system for processing any text records in RushDB based on TypeScript & Express.js.
  Features generic record vectorization, embedding integration directly into existing records, vector similarity search, and scalable FastAPI architecture.

### Data Import Utilities

- **[Python CSV Import](./python-import-csv)** | [📝 README](./python-import-csv/README.md)

  Simple utility for importing CSV data into RushDB.
  Demonstrates bulk data import functionality and basic RushDB Python SDK usage.

## Technology Stack Coverage

### Languages & Frameworks

- **Backend**: TypeScript, JavaScript, Python
- **Frontend**: Next.js, React, Vite
- **API**: Express.js, FastAPI, REST APIs
- **Database**: RushDB (Neo4j-based Graph Database)

### Key Features Demonstrated

- **🔄 CRUD Operations**: Complete Create, Read, Update, Delete workflows
- **🔍 Vector Search**: AI-powered similarity search and embeddings
- **🤖 RAG Systems**: Retrieval-Augmented Generation implementations
- **📊 Data Import**: Bulk data import and CSV processing
- **⚡ Real-time Filtering**: Dynamic UI components with live data
- **✅ Form Validation**: React Hook Form with Zod schema validation
- **📝 Content Management**: Full CMS with page and post management

### Tools & Libraries

- **SDKs**: [@rushdb/javascript-sdk](https://www.npmjs.com/package/@rushdb/javascript-sdk), [rushdb-python](https://pypi.org/project/rushdb/)
- **Testing**: Postman Collections included
- **Package Management**: npm, pnpm, UV Package Manager
- **Validation**: React Hook Form, Zod
- **AI/ML**: Sentence Transformers, Vector Embeddings
- **UI**: Tailwind CSS, shadcn/ui components

## Quick Start Example

Here's how simple it is to get started with RushDB:

### TypeScript/JavaScript

```typescript
import RushDB from "@rushdb/javascript-sdk";

const db = new RushDB(process.env.RUSHDB_API_TOKEN);

// Push nested JSON - auto-normalized into graph
await db.records.createMany({
  label: "COMPANY",
  payload: {
    name: "Tech Corp",
    DEPARTMENT: [
      {
        name: "Engineering",
        EMPLOYEE: [
          {
            name: "Alice Smith",
            role: "Senior Developer",
          },
        ],
      },
    ],
  },
});

// Query with relationship traversal
const developers = await db.records.find({
  labels: ["EMPLOYEE"],
  where: {
    role: { $contains: "Developer" },
    DEPARTMENT: { COMPANY: { name: "Tech Corp" } },
  },
});
```

### Python

```python
from rushdb import RushDB

db = RushDB(os.getenv("RUSHDB_API_TOKEN"))

# Same data structure, same simplicity
db.records.create_many("COMPANY", {
    "name": "Tech Corp",
    "DEPARTMENT": [{
        "name": "Engineering",
        "EMPLOYEE": [{
            "name": "Alice Smith",
            "role": "Senior Developer"
        }]
    }]
})

# Consistent query syntax across languages
developers = db.records.find({
    "labels": ["EMPLOYEE"],
    "where": {
        "role": {"$contains": "Developer"},
        "DEPARTMENT": {"COMPANY": {"name": "Tech Corp"}}
    }
})
```

## Getting Started

Each example includes its own README with detailed setup instructions, API documentation, and usage examples. Most examples include:

- **📋 Prerequisites**: Required dependencies and environment setup
- **⚙️ Environment Configuration**: `.env` file templates and variable explanations
- **📦 Installation Instructions**: Step-by-step dependency installation
- **🚀 Usage Guides**: How to run and test the application
- **📖 API Documentation**: Endpoint descriptions and request/response examples
- **📮 Postman Collections**: Ready-to-import API testing collections (where applicable)
- **🎯 Sample Data**: Test datasets and example records for immediate experimentation

### Recommended Learning Path

1. **Start Simple**: Begin with [Python CSV Import](./python-import-csv) to understand basic RushDB operations
2. **Build APIs**: Explore [Express REST API](./express-rushdb-sdk) for comprehensive backend development
3. **Create UIs**: Try [Next.js Dynamic Filters](./nextjs-filters-rushdb-sdk) for interactive frontend development
4. **Add AI**: Implement [Python RAG Systems](./python-simple-rag) for AI-powered applications
5. **Go Advanced**: Build a complete [CMS](./nextjs-cms) or complex [forms](./vite-react-useForm)

### Common Setup Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/rush-db/examples.git
   cd examples
   ```

2. **Navigate to your chosen example**:

   ```bash
   cd express-rushdb-sdk  # or any other example
   ```

3. **Follow the example-specific README** for detailed setup instructions

### Getting Help

- **📖 Documentation**: [docs.rushdb.com](https://docs.rushdb.com/)
- **💬 Community**: [GitHub Discussions](https://github.com/rush-db/rushdb/discussions)
- **🐛 Issues**: [Report bugs or request features](https://github.com/rush-db/rushdb/issues)
- **📧 Support**: Contact support through [app.rushdb.com](https://app.rushdb.com/)

Feel free to explore each example to see how RushDB can simplify data modeling, querying, and AI-powered applications for modern development.
