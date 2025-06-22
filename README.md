# RushDB Examples

This repository contains comprehensive code samples and projects demonstrating quick integration with [RushDB](https://rushdb.com) across various use cases and programming languages.

## Available Examples

### Backend APIs

- **[Express REST API](./express-rushdb-sdk)**
  Complete REST API built with Express and TypeScript showcasing RushDB SDK integration.
  Features hierarchical data modeling (Company → Department → Employee), CRUD operations, advanced aggregation queries, and comprehensive endpoint examples with Postman collection.

### Frontend Applications

- **[Next.js Dynamic Filters Demo](./nextjs-filters-rushdb-sdk)**
  Interactive Next.js application demonstrating dynamic UI components with RushDB integration.
  Features real-time filtering, search functionality, server-side pagination, data grid visualization, and debug tools for tracking RushDB operations.

- **[Next.js CMS](./nextjs-cms)**
  Content Management System built with Next.js and RushDB.
  Features page management, post creation, media handling, and administrative dashboard functionality.

- **[Next.js Simple Waitlist](./nextjs-simple-waitlist)**
  Clean and responsive waitlist application built with Next.js and RushDB.
  Features email validation, duplicate prevention, RushDB integration for data storage.

- **[Vite React Form](./vite-react-useForm)**
  Professional registration form built with Vite, React, and TypeScript using React Hook Form and Zod validation.
  Features comprehensive form validation, dynamic skill management, complex nested data structures, mock data filling, and seamless RushDB integration for data storage.

### AI & RAG Applications

- **[Simple Python RAG](./python-simple-rag)**
  Minimal RAG (Retrieval-Augmented Generation) implementation using RushDB for vector storage.
  Features document ingestion, automatic chunking, vector embeddings with sentence transformers, semantic search, and FastAPI interface.

- **[Generic Books RAG API](./python-books-rag)**
  Advanced RAG system for processing any text records in RushDB.
  Features generic record vectorization, embedding integration directly into existing records, vector similarity search, and scalable FastAPI architecture.

### Data Import Utilities

- **[Python CSV Import](./python-import-csv)**
  Simple utility for importing CSV data into RushDB.
  Demonstrates bulk data import functionality and basic RushDB Python SDK usage.

## Technology Stack Coverage

- **Languages**: TypeScript, JavaScript, Python
- **Frameworks**: Express.js, Next.js, FastAPI, Vite
- **Features**: REST APIs, Vector Search, RAG Systems, Data Import, Real-time Filtering, Form Validation
- **Tools**: RushDB SDK, Postman Collections, UV Package Manager, React Hook Form, Zod

## Getting Started

Each example includes its own README with detailed setup instructions, API documentation, and usage examples. Most examples include:

- Environment configuration
- Dependency installation instructions
- API documentation or usage guides
- Postman collections (where applicable)
- Sample data for testing

Feel free to explore each example to see how RushDB can simplify data modeling, querying, and AI-powered applications for modern development.
