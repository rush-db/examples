"""
Seed script for Graph-Based Citation Networks demo.

Creates a mock academic citation network with:
- 20 papers across NLP, CV, and ML domains
- Realistic citation relationships (directed edges)
- Abstract vectors for semantic similarity search

Run this once before main.py to populate the database.
"""

import os
import random
from datetime import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

# Check for API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("❌ RUSHDB_API_KEY not found in environment")
    print("   Copy .env.example to .env and add your API key")
    exit(1)

from rushdb import RushDB

# Initialize RushDB client
db = RushDB(api_key)

# Initialize embedding model (all-MiniLM-L6-v2 for speed/quality balance)
print("Loading embedding model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_DIM = 384


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


# Define papers with their metadata and abstracts
PAPERS_DATA = [
    # Foundational NLP papers
    {
        "id": "word2vec",
        "title": "Word2Vec: Distributed Representations of Words and Phrases and their Compositionality",
        "abstract": "We propose several novel methods for learning high-quality distributed vector representations that capture a large number of precise syntactic and semantic word relationships. We introduce an efficiency improvement that makes use of subsampling of words for training which yields a 2x speedup and also produces more regular representations. We also show that subsampling of frequent words results in better PBIR representations. Finally we describe a simple alternative to the hierarchical softmax called negative sampling.",
        "year": 2013,
        "authors": ["Tomas Mikolov", "Ilya Sutskever", "Kai Chen", "Greg Corrado", "Jeffrey Dean"],
        "venue": "NeurIPS",
        "domain": "NLP"
    },
    {
        "id": "seq2seq",
        "title": "Sequence to Sequence Learning with Neural Networks",
        "abstract": "Deep Neural Networks have been shown to perform very well on many NLP tasks. However, DNNs require the input and output to be fixed-length vectors and they cannot model sequences. We propose a general end-to-end approach that uses a multilayered Long Short-Term Memory to map the input sequence to a vector space, and then another deep LSTM to decode the target sequence from the vector. Our main result is that on an English to French translation task from the WMT'14 dataset, the translations produced by the LSTM achieve a BLEU score of 34.8 on the entire test set.",
        "year": 2014,
        "authors": ["Ilya Sutskever", "Oriol Vinyals", "Quoc V. Le"],
        "venue": "NeurIPS",
        "domain": "NLP"
    },
    {
        "id": "attention_nmt",
        "title": "Neural Machine Translation by Jointly Learning to Align and Translate",
        "abstract": "Neural machine translation is a recently proposed approach to machine translation. Unlike the traditional statistical machine translation, the neural machine translation aims at building a single neural network that can be jointly tuned to maximize the translation performance. The neural network consists of an encoder and decoder. We propose a new neural network architecture that builds the sequence-to-sequence model using attention mechanism to find a soft alignment between the input and output sequences.",
        "year": 2014,
        "authors": ["Dzmitry Bahdanau", "Kyunghyun Cho", "Yoshua Bengio"],
        "venue": "ICLR",
        "domain": "NLP"
    },
    {
        "id": "lstm",
        "title": "Long Short-Term Memory",
        "abstract": "Learning to store information over extended time intervals by recurrent backpropagation takes a very long time, mostly because of insufficient, decaying error backflow. We briefly review Hochreiter's 1991 analysis of this problem, then address it by introducing a novel, efficient, gradient-based method called long short-term memory (LSTM). LSTM can learn to bridge minimal time lags in excess of 1000 discrete-time steps by enforcing constant error flow through специальные units.",
        "year": 1997,
        "authors": ["Sepp Hochreiter", "Jürgen Schmidhuber"],
        "venue": "Neural Computation",
        "domain": "ML"
    },
    {
        "id": "transformer",
        "title": "Attention Is All You Need",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and the decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
        "year": 2017,
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Łukasz Kaiser", "Illia Polosukhin"],
        "venue": "NeurIPS",
        "domain": "NLP"
    },
    {
        "id": "bert",
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.",
        "year": 2018,
        "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        "venue": "NAACL",
        "domain": "NLP"
    },
    {
        "id": "gpt2",
        "title": "Language Models are Unsupervised Multitask Learners",
        "abstract": "Natural language processing systems currently navigate a two-stage approach: first, a task-agnostic pretraining on large unlabeled text corpora, then task-specific supervised fine-tuning. This paper shows that language models can perform a wide range of tasks in a zero-shot setting by prompting the model with text descriptions of the task. We demonstrate that the unsupervised multitask learning approach can achieve competitive performance with task-specific supervised models.",
        "year": 2019,
        "authors": ["Alec Radford", "Jeffrey Wu", "Rewon Child", "David Luan", "Dario Amodei", "Ilya Sutskever"],
        "venue": "OpenAI Technical Report",
        "domain": "NLP"
    },
    {
        "id": "gpt3",
        "title": "Language Models are Few-Shot Learners",
        "abstract": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by task-specific fine-tuning. We show that scaling up language models greatly improves task-agnostic, few-shot performance. Specifically, we train GPT-3, an autoregressive language model with 175 billion parameters. Despite many findings, GPT-3 has limitations including the lack of ability to learn from new examples in context.",
        "year": 2020,
        "authors": ["Tom Brown", "Benjamin Mann", "Nick Ryder", "Melanie Subbiah", "Kaplan et al."],
        "venue": "NeurIPS",
        "domain": "NLP"
    },
    # Text classification papers
    {
        "id": "textcnn",
        "title": "Convolutional Neural Networks for Sentence Classification",
        "abstract": "We report on a series of experiments with convolutional neural networks (CNN) trained on top of pre-trained word vectors for sentence-level classification tasks. We show that a simple CNN with little hyperparameter tuning and static vectors achieves excellent results on multiple benchmarks. We further propose a simple modification to enhance the model's ability to capture fine-grained semantics.",
        "year": 2014,
        "authors": ["Yoon Kim"],
        "venue": "EMNLP",
        "domain": "NLP"
    },
    {
        "id": "attention_text",
        "title": "Attention-Based Bidirectional Long Short-Term Memory Networks for Relation Classification",
        "abstract": "Relation classification is an important NLP task. We propose an attention-based bidirectional long short-term memory network for relation classification. We first encode the sequence of tokens in a sentence into a sequence of vectors using a BiLSTM. Then we apply attention mechanism to capture the most important semantic information in the final representation. Experiments on the SemEval-2010 Task 8 dataset demonstrate that our model achieves competitive performance.",
        "year": 2016,
        "authors": ["Peng Zhou", "Wei Shi", "Jun Tian", "Zhengyan He"],
        "venue": "ACL",
        "domain": "NLP"
    },
    {
        "id": "lstm_text",
        "title": "LSTM Networks for Sequence Labeling in Natural Language Processing",
        "abstract": "Long short-term memory networks (LSTMs) have become the method of choice for many sequence labeling tasks. This paper analyzes the architecture of LSTMs for sequence labeling, proposing several modifications that improve performance. We demonstrate the effectiveness of LSTMs on part-of-speech tagging and named entity recognition, achieving state-of-the-art results on several benchmarks.",
        "year": 2017,
        "authors": ["Alan Graves", "Alex Graves"],
        "venue": "Springer",
        "domain": "NLP"
    },
    {
        "id": "bert_doc_class",
        "title": "BERT for Document Classification: A Comprehensive Study",
        "abstract": "We conduct an empirical study on applying BERT to document classification tasks. We explore various fine-tuning strategies including layer-wise learning rate decay, discriminative fine-tuning, and gradual unfreezing. Our experiments on multiple document classification benchmarks show that proper fine-tuning of BERT can achieve significant improvements over previous state-of-the-art methods. We also analyze the impact of document length and training set size.",
        "year": 2019,
        "authors": ["Jianfang Hui", "Liangjie Hong", "Wei Liu"],
        "venue": "arXiv",
        "domain": "NLP"
    },
    {
        "id": "transformer_survey",
        "title": "A Survey of Transformer Architectures for Natural Language Processing",
        "abstract": "Transformers have become the dominant architecture in natural language processing since their introduction in 2017. This survey provides a comprehensive overview of transformer variants including vanilla transformer, BERT, GPT, T5, and their variants. We discuss architectural modifications, pre-training objectives, and efficient transformer variants. We also cover applications in machine translation, text generation, and question answering.",
        "year": 2020,
        "authors": ["Yi Yang"],
        "venue": "ACM Computing Surveys",
        "domain": "NLP"
    },
    # Computer Vision papers
    {
        "id": "alexnet",
        "title": "ImageNet Classification with Deep Convolutional Neural Networks",
        "abstract": "We trained a large, deep convolutional neural network to classify the 1.2 million high-resolution images in the ImageNet LSVRC-2010 contest into the 1000 different classes. On the test data, we achieved top-1 and top-5 error rates of 37.5% and 17.0% which is considerably better than the previous state-of-the-art. The neural network has 60 million parameters and 650,000 neurons and consists of five convolutional layers, some of which are followed by max-pooling layers, and three fully connected layers with a final 1000-way softmax.",
        "year": 2012,
        "authors": ["Alex Krizhevsky", "Ilya Sutskever", "Geoffrey Hinton"],
        "venue": "NeurIPS",
        "domain": "CV"
    },
    {
        "id": "resnet",
        "title": "Deep Residual Learning for Image Recognition",
        "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions. We provide comprehensive empirical evidence showing that these residual networks are easier to optimize, and can gain accuracy from considerably increased depth.",
        "year": 2016,
        "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        "venue": "CVPR",
        "domain": "CV"
    },
    {
        "id": "vit",
        "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
        "abstract": "While the Transformer architecture has become the de-facto standard for natural language processing tasks, its applications to computer vision remain limited. Inspired by the Transformer scaling successes in NLP and how they can be scaled to billions of tokens, we show that this reliance on CNNs is not necessary and a pure transformer applied directly to sequences of image patches can perform very well on image classification tasks.",
        "year": 2021,
        "authors": ["Alexey Dosovitskiy", "Lucas Beyer", "Alexander Kolesnikov", "Dirk Weissenborn"],
        "venue": "ICLR",
        "domain": "CV"
    },
    {
        "id": "clip",
        "title": "Learning Transferable Visual Models From Natural Language Supervision",
        "abstract": "State-of-the-art computer vision systems are trained to predict a fixed set of predetermined object categories. This requires significant human effort to label data, and limits the generality of the model. We demonstrate that the simple pre-training task of predicting which image goes with which text is an efficient and scalable way to learn SOTA image representations from scratch on a dataset of 400 million images collected from the internet.",
        "year": 2021,
        "authors": ["Alec Radford", "Jong Wook Kim", "Chris Hallacy", "Aditya Rameshbharathi"],
        "venue": "ICML",
        "domain": "CV"
    },
    # Reinforcement Learning papers
    {
        "id": "dqn",
        "title": "Playing Atari with Deep Reinforcement Learning",
        "abstract": "We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input using reinforcement learning. The model is a convolutional neural network, trained with a variant of Q-learning, whose input is raw pixels and whose output is a value function estimating future rewards. We find that it learns to play seven Atari 2600 games without any prior knowledge of their rules.",
        "year": 2013,
        "authors": ["Volodymyr Mnih", "Koray Kavukcuoglu", "David Silver", "Alex Graves"],
        "venue": "arXiv",
        "domain": "RL"
    },
    {
        "id": "ppo",
        "title": "Proximal Policy Optimization Algorithms",
        "abstract": "We propose a new family of policy gradient methods for reinforcement learning, which alternate between sampling data through interaction with the environment, and optimizing a surrogate objective function using stochastic gradient ascent. Unlike standard policy gradient methods, which perform one gradient update per data sample, we propose a novel method with multiple epochs of minibatch updates. These methods are significantly more data efficient and robust than previous approaches.",
        "year": 2017,
        "authors": ["John Schulman", "Filip Wolski", "Prafulla Dhariwal", "Alec Radford", "Oleg Klimov"],
        "venue": "arXiv",
        "domain": "RL"
    },
]

# Define citation relationships (citing paper → cited paper)
# Format: {"source": citing_paper_id, "target": cited_paper_id}
# This creates a realistic citation graph with clear lineages
CITATION_EDGES = [
    # BERT lineage: BERT cites transformer, word2vec
    {"source": "bert", "target": "transformer"},
    {"source": "bert", "target": "word2vec"},
    {"source": "bert_doc_class", "target": "bert"},
    {"source": "bert_doc_class", "target": "transformer"},
    
    # Transformer lineage: cites attention, seq2seq
    {"source": "transformer", "target": "attention_nmt"},
    {"source": "transformer", "target": "seq2seq"},
    {"source": "transformer", "target": "lstm"},
    
    # GPT lineage: GPT cites transformer, word2vec
    {"source": "gpt2", "target": "transformer"},
    {"source": "gpt2", "target": "word2vec"},
    {"source": "gpt3", "target": "gpt2"},
    {"source": "gpt3", "target": "transformer"},
    
    # Attention for text classification cites LSTM and attention
    {"source": "attention_text", "target": "lstm"},
    {"source": "attention_text", "target": "attention_nmt"},
    
    # LSTM text classification cites LSTM
    {"source": "lstm_text", "target": "lstm"},
    
    # TextCNN cites word2vec
    {"source": "textcnn", "target": "word2vec"},
    {"source": "textcnn", "target": "seq2seq"},
    
    # Transformer survey cites multiple
    {"source": "transformer_survey", "target": "transformer"},
    {"source": "transformer_survey", "target": "bert"},
    {"source": "transformer_survey", "target": "attention_nmt"},
    
    # ViT cites transformer and resnet
    {"source": "vit", "target": "transformer"},
    {"source": "vit", "target": "resnet"},
    {"source": "vit", "target": "alexnet"},
    
    # CLIP cites transformer, vit
    {"source": "clip", "target": "transformer"},
    {"source": "clip", "target": "vit"},
    {"source": "clip", "target": "resnet"},
    
    # ResNet cites alexnet
    {"source": "resnet", "target": "alexnet"},
    
    # DQN cites LSTM
    {"source": "dqn", "target": "lstm"},
    
    # PPO cites DQN, LSTM
    {"source": "ppo", "target": "dqn"},
    {"source": "ppo", "target": "lstm"},
]


def check_existing_data():
    """Check if data already exists in the database."""
    result = db.records.find({
        "labels": ["PAPER"],
        "limit": 1
    })
    return result.total > 0


def create_papers():
    """Create all papers with their embeddings."""
    print("\n📄 Creating papers with abstract embeddings...")
    
    # Check if vector index exists, create if not
    indexes = db.ai.indexes.find()
    abstract_index = None
    for idx in indexes.data:
        if idx['label'] == 'PAPER' and idx['propertyName'] == 'abstract':
            abstract_index = idx
            break
    
    if not abstract_index:
        print("   Creating vector index for PAPER.abstract...")
        abstract_index = db.ai.indexes.create({
            "label": "PAPER",
            "propertyName": "abstract",
            "sourceType": "external",
            "dimensions": EMBEDDING_DIM,
            "similarityFunction": "cosine"
        })
        print(f"   Created index: {abstract_index.id}")
    else:
        print(f"   Using existing index: {abstract_index.id}")
    
    index_id = abstract_index.id
    
    # Generate embeddings for all abstracts
    abstracts = [p["abstract"] for p in PAPERS_DATA]
    print("   Generating embeddings...")
    embeddings = embed_texts(abstracts)
    
    # Create papers in batches
    created_papers = {}
    for i, paper_data in enumerate(PAPERS_DATA):
        paper = db.records.create(
            label="PAPER",
            data={
                "paper_id": paper_data["id"],
                "title": paper_data["title"],
                "abstract": paper_data["abstract"],
                "year": paper_data["year"],
                "authors": paper_data["authors"],
                "venue": paper_data["venue"],
                "domain": paper_data["domain"]
            },
            vectors=[{
                "propertyName": "abstract",
                "vector": embeddings[i]
            }]
        )
        created_papers[paper_data["id"]] = paper
        
        if (i + 1) % 5 == 0:
            print(f"   Created {i + 1}/{len(PAPERS_DATA)} papers...")
    
    print(f"   ✓ Created {len(created_papers)} papers with embeddings")
    return created_papers


def create_citations(papers: dict):
    """Create citation relationships between papers."""
    print("\n🔗 Creating citation relationships...")
    
    created_count = 0
    for i, edge in enumerate(CITATION_EDGES):
        source_paper = papers.get(edge["source"])
        target_paper = papers.get(edge["target"])
        
        if source_paper and target_paper:
            # Attach creates a directed edge: source CITES target
            # Direction "out" means source → target
            db.records.attach(
                source=source_paper,
                target=target_paper,
                options={"type": "CITES", "direction": "out"}
            )
            created_count += 1
        
        if (i + 1) % 10 == 0:
            print(f"   Created {i + 1}/{len(CITATION_EDGES)} citations...")
    
    print(f"   ✓ Created {created_count} citation edges")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("CITATION NETWORK SEED SCRIPT")
    print("=" * 60)
    
    # Check for existing data
    if check_existing_data():
        response = input("\n⚠️  Existing papers found. Re-seed? This will create duplicates. (y/N): ")
        if response.lower() != 'y':
            print("\n✅ Using existing data. Run 'python main.py' to proceed.")
            return
        print("\n📝 Proceeding with seeding (new papers will be created)...")
    
    start_time = datetime.now()
    
    # Create papers with embeddings
    papers = create_papers()
    
    # Create citation relationships
    create_citations(papers)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print(f"✅ SEEDING COMPLETE ({elapsed:.1f}s)")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   • {len(PAPERS_DATA)} papers created")
    print(f"   • {len(CITATION_EDGES)} citation relationships")
    print(f"   • {EMBEDDING_DIM}-dimensional abstract embeddings")
    print(f"\n🚀 Run 'python main.py' to see the graph+vector demo!")


if __name__ == "__main__":
    main()
