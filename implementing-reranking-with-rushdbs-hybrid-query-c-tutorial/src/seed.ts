/**
 * Database seeding script
 * 
 * Creates sample articles with embeddings for the reranking demo.
 * Run with: npm run seed
 * 
 * This script is idempotent - safe to run multiple times.
 */

import * as dotenv from 'dotenv';
import RushDB from '@rushdb/javascript-sdk';

// Load environment variables
dotenv.config();

// Sample article data
const ARTICLE_TEMPLATES = [
  {
    title: 'Introduction to Machine Learning Fundamentals',
    body: 'Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. This comprehensive guide covers the fundamental concepts including supervised learning, unsupervised learning, and reinforcement learning. We explore algorithms like linear regression, decision trees, and neural networks.',
    summary: 'A beginner-friendly introduction to core machine learning concepts and algorithms.',
    category: 'technology',
    tags: ['ml', 'ai', 'data-science']
  },
  {
    title: 'Deep Learning Architectures Overview',
    body: 'Deep learning has revolutionized artificial intelligence with architectures like convolutional neural networks (CNNs) for image processing, recurrent neural networks (RNNs) for sequential data, and transformers for natural language processing. This article explores ResNet, LSTM, BERT, and GPT architectures.',
    summary: 'Exploring modern deep learning architectures and their applications.',
    category: 'research',
    tags: ['deep-learning', 'ai', 'nlp']
  },
  {
    title: 'Python Data Processing Guide',
    body: 'Python dominates data science with libraries like pandas for data manipulation, NumPy for numerical computing, and Matplotlib for visualization. This guide covers efficient data cleaning, transformation, and analysis techniques using modern Python tooling.',
    summary: 'Comprehensive guide to data processing with Python libraries.',
    category: 'tutorials',
    tags: ['python', 'data-science']
  },
  {
    title: 'Natural Language Processing with Transformers',
    body: 'Transformers have become the dominant architecture for NLP tasks. We cover attention mechanisms, self-attention, and how models like BERT and GPT-3 achieve state-of-the-art results on tasks including text classification, named entity recognition, and machine translation.',
    summary: 'Understanding transformers and their application in NLP tasks.',
    category: 'technology',
    tags: ['nlp', 'deep-learning', 'ai']
  },
  {
    title: 'Computer Vision Applications in 2024',
    body: 'Computer vision has advanced dramatically with deep learning. Applications include object detection, semantic segmentation, facial recognition, and autonomous driving. We review YOLO, Mask R-CNN, and modern vision transformers.',
    summary: 'Current state of computer vision technology and its applications.',
    category: 'technology',
    tags: ['computer-vision', 'deep-learning', 'ai']
  },
  {
    title: 'Building Production ML Pipelines',
    body: 'Deploying machine learning models to production requires careful consideration of monitoring, scaling, and maintenance. This guide covers MLOps practices, model versioning, A/B testing, and continuous training for production ML systems.',
    summary: 'Best practices for deploying and maintaining ML models in production.',
    category: 'tutorials',
    tags: ['ml', 'devops', 'python']
  },
  {
    title: 'Cloud Machine Learning Services Comparison',
    body: 'AWS SageMaker, Google Cloud AI Platform, and Azure Machine Learning offer comprehensive ML services. We compare their capabilities, pricing, ease of use, and best use cases for each platform.',
    summary: 'Comparing major cloud providers for machine learning workloads.',
    category: 'technology',
    tags: ['cloud', 'ml', 'ai']
  },
  {
    title: 'Database Optimization Techniques',
    body: 'Database performance is critical for application scalability. This article covers indexing strategies, query optimization, connection pooling, and caching techniques for both SQL and NoSQL databases.',
    summary: 'Essential techniques for optimizing database performance.',
    category: 'technology',
    tags: ['database', 'performance', 'api']
  },
  {
    title: 'API Security Best Practices',
    body: 'Securing APIs requires multiple layers of protection. We cover authentication methods (OAuth 2.0, JWT), rate limiting, input validation, CORS configuration, and monitoring for security threats.',
    summary: 'Comprehensive guide to securing APIs against common threats.',
    category: 'tutorials',
    tags: ['security', 'api', 'devops']
  },
  {
    title: 'JavaScript Performance Optimization',
    body: 'Modern JavaScript applications need to be fast and responsive. This guide covers bundle optimization, code splitting, lazy loading, memory management, and using Web Workers for heavy computations.',
    summary: 'Techniques for building high-performance JavaScript applications.',
    category: 'tutorials',
    tags: ['javascript', 'performance', 'web']
  },
  {
    title: 'The Future of AI in Healthcare',
    body: 'Artificial intelligence is transforming healthcare with applications in medical imaging, drug discovery, personalized medicine, and clinical decision support. We explore current applications, challenges, and future possibilities.',
    summary: 'How AI is revolutionizing healthcare and medicine.',
    category: 'opinion',
    tags: ['ai', 'ml', 'research']
  },
  {
    title: 'DevOps Automation Strategies',
    body: 'Modern DevOps relies heavily on automation for continuous integration and deployment. We cover infrastructure as code, container orchestration with Kubernetes, and automated testing pipelines.',
    summary: 'Automation strategies for modern DevOps practices.',
    category: 'tutorials',
    tags: ['devops', 'cloud', 'performance']
  },
  {
    title: 'Time Series Forecasting with Python',
    body: 'Time series forecasting is essential for demand prediction, financial modeling, and anomaly detection. We explore ARIMA, Prophet, and deep learning approaches using PyTorch and TensorFlow.',
    summary: 'Methods and tools for time series forecasting in Python.',
    category: 'tutorials',
    tags: ['python', 'data-science', 'ml']
  },
  {
    title: 'Microservices Architecture Patterns',
    body: 'Microservices offer scalability and flexibility but introduce complexity. We discuss service decomposition, inter-service communication, API gateways, service mesh, and observability.',
    summary: 'Patterns and practices for building microservices systems.',
    category: 'technology',
    tags: ['api', 'devops', 'cloud']
  },
  {
    title: 'Graph Neural Networks Explained',
    body: 'Graph neural networks (GNNs) extend deep learning to graph-structured data. Applications include social network analysis, molecular property prediction, and knowledge graph completion.',
    summary: 'Introduction to graph neural networks and their applications.',
    category: 'research',
    tags: ['deep-learning', 'ai', 'data-science']
  },
  {
    title: 'Data Visualization with Python',
    body: 'Effective data visualization is crucial for communicating insights. We cover Matplotlib, Seaborn, Plotly, and how to create interactive dashboards that tell compelling stories with data.',
    summary: 'Tools and techniques for creating effective data visualizations.',
    category: 'tutorials',
    tags: ['python', 'data-science', 'visualization']
  },
  {
    title: 'Kubernetes for Data Scientists',
    body: 'Data scientists can benefit from understanding container orchestration. This guide introduces Kubernetes concepts, deploying ML models as containers, and managing compute resources.',
    summary: 'Kubernetes essentials for data science workloads.',
    category: 'tutorials',
    tags: ['devops', 'cloud', 'ml']
  },
  {
    title: 'Reinforcement Learning Tutorial',
    body: 'Reinforcement learning enables agents to learn through interaction with environments. We cover Markov decision processes, Q-learning, policy gradients, and implement examples with OpenAI Gym.',
    summary: 'Hands-on introduction to reinforcement learning fundamentals.',
    category: 'tutorials',
    tags: ['ml', 'ai', 'python']
  },
  {
    title: 'The State of Open Source AI Models',
    body: 'The AI landscape is shifting with越来越多 open source models becoming available. We review Llama, Mistral, Falcon, and how they compare to proprietary models like GPT-4 and Claude.',
    summary: 'Overview of the growing open source AI model ecosystem.',
    category: 'opinion',
    tags: ['ai', 'ml', 'nlp']
  },
  {
    title: 'SQL vs NoSQL: Making the Right Choice',
    body: 'Choosing between SQL and NoSQL databases depends on your data model, query patterns, and scaling requirements. We compare ACID properties, data modeling approaches, and performance characteristics.',
    summary: 'Guide to choosing between SQL and NoSQL databases.',
    category: 'technology',
    tags: ['database', 'api']
  },
  {
    title: 'Building RAG Applications',
    body: 'Retrieval-augmented generation (RAG) combines information retrieval with language models. We cover document chunking, embedding strategies, vector databases, and building production RAG systems.',
    summary: 'Tutorial on building retrieval-augmented generation applications.',
    category: 'tutorials',
    tags: ['ai', 'nlp', 'python']
  },
  {
    title: 'Feature Engineering for ML Models',
    body: 'Feature engineering is crucial for model performance. We cover handling missing values, encoding categorical variables, creating interaction features, and automated feature engineering.',
    summary: 'Techniques for creating effective features for machine learning.',
    category: 'research',
    tags: ['ml', 'data-science', 'python']
  },
  {
    title: 'Real-time Data Streaming Architectures',
    body: 'Processing data in real-time requires different architectures than batch processing. We cover Apache Kafka, Apache Flink, and designing streaming applications for low-latency insights.',
    summary: 'Building architectures for real-time data processing.',
    category: 'technology',
    tags: ['database', 'devops', 'cloud']
  },
  {
    title: 'Bias in Machine Learning Models',
    body: 'Machine learning models can perpetuate and amplify biases present in training data. We discuss identifying bias, fairness metrics, mitigation strategies, and ethical considerations.',
    summary: 'Understanding and addressing bias in ML systems.',
    category: 'opinion',
    tags: ['ai', 'ml', 'ethics']
  },
  {
    title: 'WebAssembly for High Performance',
    body: 'WebAssembly enables near-native performance in browsers. We explore use cases, Rust integration, and how WASM is changing web application capabilities.',
    summary: 'Introduction to WebAssembly for web performance optimization.',
    category: 'technology',
    tags: ['javascript', 'performance', 'web']
  },
  {
    title: 'Quantum Computing for Developers',
    body: 'Quantum computing is approaching practical applications. We introduce quantum bits, superposition, entanglement, and how developers can start experimenting with quantum circuits.',
    summary: 'Getting started with quantum computing concepts and tools.',
    category: 'research',
    tags: ['quantum', 'computing', 'future']
  },
  {
    title: 'Model Evaluation and Metrics',
    body: 'Choosing the right evaluation metrics is essential for model development. We cover accuracy, precision, recall, F1 score, AUC-ROC, and domain-specific metrics for different ML tasks.',
    summary: 'Guide to evaluating machine learning models effectively.',
    category: 'tutorials',
    tags: ['ml', 'data-science', 'python']
  },
  {
    title: 'Edge Computing with Machine Learning',
    body: 'Running ML models on edge devices enables real-time inference without cloud connectivity. We discuss model compression, quantization, TensorFlow Lite, and ONNX runtime.',
    summary: 'Deploying ML models to edge devices efficiently.',
    category: 'technology',
    tags: ['ml', 'iot', 'performance']
  },
  {
    title: 'The Rise of Large Language Models',
    body: 'Large language models have transformed AI capabilities. We trace the evolution from GPT to GPT-4, discuss scaling laws, emergent capabilities, and future directions.',
    summary: 'Understanding the development and impact of LLMs.',
    category: 'opinion',
    tags: ['ai', 'nlp', 'ml']
  },
  {
    title: 'Testing Machine Learning Systems',
    body: 'Testing ML systems is different from traditional software testing. We cover unit tests for data processing, validation tests for models, and integration tests for ML pipelines.',
    summary: 'Best practices for testing machine learning systems.',
    category: 'tutorials',
    tags: ['ml', 'devops', 'python']
  },
  {
    title: 'Fraud Detection with Machine Learning',
    body: 'Financial institutions use ML for fraud detection. We explore anomaly detection algorithms, feature engineering for transaction data, and handling class imbalance.',
    summary: 'Building fraud detection systems with ML techniques.',
    category: 'research',
    tags: ['ml', 'ai', 'data-science']
  },
  {
    title: 'Serverless Architecture Patterns',
    body: 'Serverless computing offers automatic scaling and reduced operational overhead. We cover AWS Lambda, Azure Functions, design patterns, and when serverless is the right choice.',
    summary: 'Patterns for building serverless applications.',
    category: 'technology',
    tags: ['cloud', 'devops', 'api']
  },
  {
    title: 'Recommendation Systems Deep Dive',
    body: 'Recommendation systems power content discovery across platforms. We explore collaborative filtering, content-based methods, matrix factorization, and deep learning approaches.',
    summary: 'Building and evaluating recommendation systems.',
    category: 'research',
    tags: ['ml', 'ai', 'data-science']
  },
  {
    title: 'Monitoring ML Models in Production',
    body: 'Model monitoring ensures deployed models continue to perform well. We cover data drift detection, concept drift, performance degradation alerts, and setting up observability.',
    summary: 'Practices for monitoring ML models post-deployment.',
    category: 'tutorials',
    tags: ['ml', 'devops', 'python']
  },
  {
    title: 'Anomaly Detection Techniques',
    body: 'Anomaly detection identifies unusual patterns in data. Applications include fraud detection, network security, and equipment monitoring. We cover statistical, ML, and deep learning approaches.',
    summary: 'Methods for detecting anomalies in various data types.',
    category: 'research',
    tags: ['ml', 'ai', 'data-science']
  },
  {
    title: 'API Design Principles',
    body: 'Well-designed APIs are crucial for developer experience and system maintainability. We cover REST principles, versioning strategies, error handling, and documentation best practices.',
    summary: 'Principles for designing great APIs.',
    category: 'tutorials',
    tags: ['api', 'web', 'best-practices']
  },
  {
    title: 'Transfer Learning in Practice',
    body: 'Transfer learning enables models to leverage knowledge from related tasks. We cover pre-trained models, fine-tuning strategies, and common architectures like ResNet and BERT.',
    summary: 'Applying transfer learning to your ML projects.',
    category: 'tutorials',
    tags: ['ml', 'deep-learning', 'python']
  },
  {
    title: 'Container Security Best Practices',
    body: 'Containers introduce security considerations at multiple levels. We cover image scanning, least privilege principles, secrets management, and runtime security monitoring.',
    summary: 'Securing containerized applications.',
    category: 'tutorials',
    tags: ['devops', 'security', 'cloud']
  },
  {
    title: 'Bayesian Machine Learning',
    body: 'Bayesian approaches provide uncertainty quantification and principled handling of small data. We cover Bayesian inference, probabilistic programming with PyMC, and Bayesian neural networks.',
    summary: 'Introduction to Bayesian methods in machine learning.',
    category: 'research',
    tags: ['ml', 'ai', 'python']
  },
  {
    title: 'Frontend Performance Optimization',
    body: 'Fast web applications are essential for user experience. We cover Core Web Vitals, lazy loading, image optimization, caching strategies, and measuring performance metrics.',
    summary: 'Techniques for optimizing frontend performance.',
    category: 'tutorials',
    tags: ['javascript', 'performance', 'web']
  },
  {
    title: 'Neural Network Architectures Comparison',
    body: 'Different neural network architectures excel at different tasks. We compare MLPs, CNNs, RNNs, LSTMs, GRUs, and Transformers with analysis of when to use each.',
    summary: 'Comparing neural network architectures for various tasks.',
    category: 'research',
    tags: ['deep-learning', 'ai', 'ml']
  },
  {
    title: 'Event-Driven Architecture Patterns',
    body: 'Event-driven architecture enables loosely coupled, scalable systems. We cover event sourcing, CQRS, message queues, and designing for eventual consistency.',
    summary: 'Patterns for building event-driven systems.',
    category: 'technology',
    tags: ['api', 'devops', 'cloud']
  },
  {
    title: 'Interpretable Machine Learning',
    body: 'Understanding why models make predictions is crucial for trust and debugging. We cover SHAP values, LIME, attention visualization, and building inherently interpretable models.',
    summary: 'Methods for interpreting and explaining ML models.',
    category: 'research',
    tags: ['ml', 'ai', 'data-science']
  },
  {
    title: 'GitOps and Infrastructure as Code',
    body: 'GitOps brings Git workflows to infrastructure management. We cover Terraform, Pulumi, declarative configurations, and automated drift detection.',
    summary: 'Implementing GitOps practices with IaC tools.',
    category: 'tutorials',
    tags: ['devops', 'cloud', 'automation']
  },
  {
    title: 'Self-Supervised Learning Advances',
    body: 'Self-supervised learning reduces reliance on labeled data. We explore contrastive learning, masked modeling, and how these techniques power foundation models.',
    summary: 'Understanding self-supervised learning approaches.',
    category: 'research',
    tags: ['deep-learning', 'ai', 'ml']
  },
  {
    title: 'Caching Strategies for Web Applications',
    body: 'Effective caching dramatically improves application performance. We cover CDN caching, browser caching, application-level caching, and cache invalidation strategies.',
    summary: 'Implementing caching at all layers of web applications.',
    category: 'tutorials',
    tags: ['performance', 'web', 'api']
  },
  {
    title: 'Multimodal AI Systems',
    body: 'Multimodal AI combines different data types like text, images, and audio. We explore CLIP, DALL-E, GPT-4V, and the challenges of training and evaluating multimodal models.',
    summary: 'Introduction to multimodal AI systems.',
    category: 'research',
    tags: ['ai', 'deep-learning', 'computer-vision']
  },
  {
    title: 'Building CI/CD Pipelines',
    body: 'CI/CD pipelines automate the software delivery process. We cover Jenkins, GitHub Actions, GitLab CI, pipeline design, testing strategies, and deployment patterns.',
    summary: 'Building effective CI/CD pipelines for modern development.',
    category: 'tutorials',
    tags: ['devops', 'cloud', 'automation']
  },
  {
    title: 'Federated Learning Overview',
    body: 'Federated learning enables training on distributed data without centralization. We cover privacy benefits, challenges, frameworks like TensorFlow Federated, and use cases.',
    summary: 'Understanding federated learning for privacy-preserving ML.',
    category: 'research',
    tags: ['ml', 'ai', 'security']
  },
  {
    title: 'GraphQL vs REST API Design',
    body: 'Choosing between GraphQL and REST depends on your use case. We compare query flexibility, caching, typing, and when each approach provides advantages.',
    summary: 'Comparing GraphQL and REST for API design.',
    category: 'technology',
    tags: ['api', 'web', 'javascript']
  }
];

const AUTHORS = [
  'Elena Rodriguez', 'Marcus Chen', 'Priya Sharma',
  'James Wilson', 'Sofia Andersson', 'Raj Patel'
];

/**
 * Generate random date within the last year
 */
function randomDate(): string {
  const now = new Date();
  const yearAgo = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
  const timestamp = yearAgo.getTime() + Math.random() * (now.getTime() - yearAgo.getTime());
  return new Date(timestamp).toISOString();
}

/**
 * Generate random view count with realistic distribution
 */
function randomViews(): number {
  // Most articles get few views, some go viral
  const base = Math.random();
  if (base < 0.7) return Math.floor(Math.random() * 5000);
  if (base < 0.9) return Math.floor(5000 + Math.random() * 50000);
  return Math.floor(50000 + Math.random() * 500000);
}

/**
 * Main seeding function
 */
async function seed(): Promise<void> {
  console.log('\n🌱 RushDB Seeding Script\n');
  console.log('This script creates sample articles for the reranking demo.\n');

  // Check for API key
  const apiKey = process.env.RUSHDB_API_KEY;
  if (!apiKey) {
    console.error('❌ Error: RUSHDB_API_KEY environment variable is not set');
    console.error('\nPlease create a .env file based on .env.example');
    console.error('Get your API key at: https://dash.rushdb.com\n');
    process.exit(1);
  }

  // Initialize RushDB client
  const db = new RushDB(apiKey, process.env.RUSHDB_URL ? { url: process.env.RUSHDB_URL } : undefined);

  try {
    // Check if data already exists
    const existing = await db.records.find({ labels: ['ARTICLE'], limit: 1 });
    if (existing.total > 0) {
      console.log(`⚠️  Database already contains ${existing.total} ARTICLE records.`);
      console.log('   Skipping seed. Delete existing records to reseed.\n');
      
      // Still create the index if it doesn't exist
      await ensureIndex(db);
      
      process.exit(0);
    }

    console.log('Creating vector index...');
    const indexId = await ensureIndex(db);

    console.log(`\nCreating ${ARTICLE_TEMPLATES.length} articles...\n`);

    // Create articles in batches
    const batchSize = 10;
    const articles: Array<{ record: Awaited<ReturnType<typeof db.records.create>>; embeddings: number[] }> = [];

    for (let i = 0; i < ARTICLE_TEMPLATES.length; i += batchSize) {
      const batch = ARTICLE_TEMPLATES.slice(i, i + batchSize);
      const tx = await db.transactions.begin();

      try {
        for (const template of batch) {
          const article = await db.records.create({
            label: 'ARTICLE',
            data: {
              title: template.title,
              body: template.body,
              summary: template.summary,
              category: template.category,
              tags: template.tags,
              author: AUTHORS[Math.floor(Math.random() * AUTHORS.length)],
              publishedAt: randomDate(),
              views: randomViews(),
              likes: Math.floor(randomViews() * 0.05),
              readingTimeMinutes: Math.floor(template.body.split(' ').length / 200) + 3
            }
          }, tx);

          articles.push({ record: article, embeddings: [] });
        }

        await tx.commit();
        console.log(`  Created batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(ARTICLE_TEMPLATES.length / batchSize)}`);
      } catch (err) {
        await tx.rollback();
        throw err;
      }
    }

    console.log('\n📊 Creating vector embeddings...');
    console.log('   (Using local sentence-transformers for embedding generation)\n');

    // Generate embeddings using sentence-transformers
    try {
      const { pipeline } = await import('@xenova/transformers');
      const embedder = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2');

      for (let i = 0; i < articles.length; i++) {
        const { record } = articles[i];
        const body = record.body as string;
        
        const output = await embedder(body, { pooling: 'mean', normalize: true }) as number[];
        articles[i].embeddings = Array.from(output);

        if ((i + 1) % 10 === 0) {
          console.log(`  Embedded ${i + 1}/${articles.length} articles`);
        }
      }

      console.log('\n💾 Upserting vectors to index...');

      // Upsert vectors in batches
      const vectorBatchSize = 25;
      for (let i = 0; i < articles.length; i += vectorBatchSize) {
        const batch = articles.slice(i, i + vectorBatchSize);
        
        await db.ai.indexes.upsertVectors(indexId, {
          items: batch.map(({ record, embeddings }) => ({
            recordId: record.id,
            vector: embeddings
          }))
        });

        console.log(`  Indexed ${Math.min(i + vectorBatchSize, articles.length)}/${articles.length} vectors`);
      }

    } catch (transformerError) {
      console.warn('\n⚠️  Could not generate embeddings with local transformers:');
      console.warn(`   ${transformerError}`);
      console.warn('\n   Articles created but vector search will use default scoring.');
      console.warn('   To enable vector search, ensure you have Node.js with WASM support.\n');
    }

    console.log('\n✅ Seeding complete!\n');
    console.log('   Run `npm start` to see the reranking demo.\n');

  } catch (error) {
    console.error('\n❌ Seeding failed:', error);
    process.exit(1);
  }
}

/**
 * Ensure vector index exists
 */
async function ensureIndex(db: RushDB): Promise<string> {
  // Check for existing index
  const indexes = await db.ai.indexes.find();
  const articleIndex = indexes.data.find(
    idx => idx.label === 'ARTICLE' && idx.propertyName === 'body'
  );

  if (articleIndex) {
    console.log(`  Using existing index: ${articleIndex.id}`);
    return articleIndex.id;
  }

  // Create new index
  const created = await db.ai.indexes.create({
    label: 'ARTICLE',
    propertyName: 'body',
    sourceType: 'external',
    dimensions: 384,
    similarityFunction: 'cosine'
  });

  console.log(`  Created new index: ${created.data.__id}`);
  return created.data.__id;
}

// Run the seed function
seed().catch(console.error);
