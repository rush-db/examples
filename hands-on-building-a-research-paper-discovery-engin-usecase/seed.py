"""
Seed script for the Research Paper Discovery Engine.

Generates realistic research paper data with:
- Papers across ML/AI research domains
- Citation relationships (graph edges)
- Abstracts vectorized using sentence-transformers

This script is IDEMPOTENT — safe to run multiple times.
It checks for existing data before creating new records.
"""

import os
import random
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
RUSHDB_TOKEN = os.getenv("RUSHDB_TOKEN")
if not RUSHDB_TOKEN:
    raise ValueError("RUSHDB_TOKEN not found. Please set it in your .env file.")

db = RushDB(RUSHDB_TOKEN)

# Initialize embedding model (all-MiniLM-L6-v2 - fast, local, no API key)
print("Loading embedding model (all-MiniLM-L6-v2)...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

# Research paper dataset
PAPERS = [
    {
        "title": "Attention Is All You Need",
        "authors": ["Vaswani, A.", "Shazeer, N.", "Parmar, N."],
        "year": 2017,
        "venue": "NeurIPS",
        "abstract": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
        "domain": "NLP"
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": ["Devlin, J.", "Chang, M.", "Lee, K.", "Toutanova, K."],
        "year": 2018,
        "venue": "NAACL",
        "abstract": "We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context.",
        "domain": "NLP"
    },
    {
        "title": "GPT-3: Language Models are Few-Shot Learners",
        "authors": ["Brown, T.", "Mann, B.", "Ryder, N."],
        "year": 2020,
        "venue": "NeurIPS",
        "abstract": "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task. While typically task-agnostic in architecture, this method still requires task-specific fine-tuning datasets of thousands or tens of thousands of examples.",
        "domain": "NLP"
    },
    {
        "title": "ResNet: Deep Residual Learning for Image Recognition",
        "authors": ["He, K.", "Zhang, X.", "Ren, S.", "Sun, J."],
        "year": 2016,
        "venue": "CVPR",
        "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.",
        "domain": "Computer Vision"
    },
    {
        "title": "ImageNet Classification with Deep Convolutional Neural Networks",
        "authors": ["Krizhevsky, A.", "Sutskever, I.", "Hinton, G."],
        "year": 2012,
        "venue": "NeurIPS",
        "abstract": "We trained a large, deep convolutional neural network to classify the 1.2 million high-resolution images in the ImageNet LSVRC-2010 contest into the 1000 different classes. On the test data, we achieved top-1 and top-5 error rates of 37.5% and 17.0% respectively, which is considerably better than the previous state-of-the-art.",
        "domain": "Computer Vision"
    },
    {
        "title": "Generative Adversarial Networks",
        "authors": ["Goodfellow, I.", "Pouget-Abadie, J.", "Mirza, M."],
        "year": 2014,
        "venue": "NeurIPS",
        "abstract": "We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model G that captures the data distribution, and a discriminative model D that estimates the probability that a sample came from the training data rather than G.",
        "domain": "Generative Models"
    },
    {
        "title": "DCGAN: Unsupervised Representation Learning with Deep Convolutional GANs",
        "authors": ["Radford, A.", "Metz, L.", "Chintala, S."],
        "year": 2016,
        "venue": "ICLR",
        "abstract": "In recent years, supervised learning with convolutional networks has seen huge adoption in computer vision applications. Comparatively, unsupervised learning with CNNs has received less attention. In this work, we hope to help bridge the gap between the success of supervised CNNs and unsupervised CNNs.",
        "domain": "Generative Models"
    },
    {
        "title": "Stable Diffusion: High-Resolution Image Synthesis with Latent Diffusion Models",
        "authors": ["Rombach, R.", "Blattmann, A.", "Lorenz, D."],
        "year": 2022,
        "venue": "CVPR",
        "abstract": "By decomposing the image formation process into a sequential application of denoising autoencoders, diffusion models achieve state-of-the-art synthesis results on image data. Yet, these models typically belong to the computationally expensive class of models.",
        "domain": "Generative Models"
    },
    {
        "title": "DQN: Playing Atari with Deep Reinforcement Learning",
        "authors": ["Mnih, V.", "Kavukcuoglu, K.", "Silver, D."],
        "year": 2013,
        "venue": "NeurIPS Workshop",
        "abstract": "We present the first deep learning model to successfully learn control policies directly from high-dimensional sensory input using reinforcement learning. The model is a convolutional neural network, trained with a variant of Q-learning, whose input is raw pixels and whose output is a value function estimating future rewards.",
        "domain": "Reinforcement Learning"
    },
    {
        "title": "AlphaGo: Mastering the Game of Go with Deep Neural Networks and Tree Search",
        "authors": ["Silver, D.", "Huang, A.", "Maddison, C."],
        "year": 2016,
        "venue": "Nature",
        "abstract": "The game of Go has long been viewed as the most challenging of classic games for artificial intelligence owing to its enormous search space and the difficulty of evaluating board positions. Here we introduce a new approach to computer Go that uses value networks to evaluate board positions and policy networks to select moves.",
        "domain": "Reinforcement Learning"
    },
    {
        "title": "Proximal Policy Optimization Algorithms",
        "authors": ["Schulman, J.", "Wolski, F.", "Dhariwal, P."],
        "year": 2017,
        "venue": "arXiv",
        "abstract": "We propose a new family of policy gradient methods for reinforcement learning, which combine techniques from several previous algorithms. Our method performs uncommonly well on a wide variety of continuous control tasks, solving all of them with a single set of hyperparameters.",
        "domain": "Reinforcement Learning"
    },
    {
        "title": "Word2Vec: Efficient Estimation of Word Representations in Vector Space",
        "authors": ["Mikolov, T.", "Sutskever, I.", "Chen, K."],
        "year": 2013,
        "venue": "ICLR Workshop",
        "abstract": "We propose two novel model architectures for computing continuous vector representations of words from very large data sets. The quality of these representations is measured in a word similarity task, and the results are compared to the previous best performing techniques based on different types of neural networks.",
        "domain": "NLP"
    },
    {
        "title": "ELMo: Deep Contextualized Word Representations",
        "authors": ["Peters, M.", "Neumann, M.", "Iyyer, M."],
        "year": 2018,
        "venue": "NAACL",
        "abstract": "We introduce a new type of deep contextualized word representation that models both complex characteristics of word use and how these uses vary across linguistic contexts. Unlike traditional word embeddings, each word representation is a function of the entire input sentence.",
        "domain": "NLP"
    },
    {
        "title": "GPT-2: Language Models are Unsupervised Multitask Learners",
        "authors": ["Radford, A.", "Wu, J.", "Child, R."],
        "year": 2019,
        "venue": "OpenAI Technical Report",
        "abstract": "GPT-2, a large transformer-based language model with 1.5 billion parameters, is trained on WebText, a dataset of millions of web pages. We demonstrate that GPT-2 can perform zero-shot domain transfer across a wide variety of tasks.",
        "domain": "NLP"
    },
    {
        "title": "T5: Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer",
        "authors": ["Raffel, C.", "Shazeer, N.", "Roberts, A."],
        "year": 2020,
        "venue": "JMLR",
        "abstract": "We explore the landscape of transfer learning techniques for NLP by introducing a unified framework that converts every language problem into a text-to-text format. Our systematic study compares dozens of pre-training objectives, architectures, unlabeled datasets, and other factors.",
        "domain": "NLP"
    },
    {
        "title": "VGGNet: Very Deep Convolutional Networks for Large-Scale Image Recognition",
        "authors": ["Simonyan, K.", "Zisserman, A."],
        "year": 2015,
        "venue": "ICLR",
        "abstract": "In this work we investigate the effect of the convolutional network depth on its accuracy in the large-scale image recognition setting. Our main contribution is a thorough evaluation of networks of increasing depth using an architecture with very small 3x3 convolution filters.",
        "domain": "Computer Vision"
    },
    {
        "title": "Inception-v4: Inception-ResNet and the Impact of Residual Connections on Learning",
        "authors": ["Szegedy, C.", "Ioffe, S.", "Vanhoucke, V."],
        "year": 2017,
        "venue": "AAAI",
        "abstract": "Here we give a detailed description of how we combined the Inception architecture with the residual connection concept. We also show a simplified version of the Inception architecture that improves accuracy on several benchmark datasets.",
        "domain": "Computer Vision"
    },
    {
        "title": "YOLO: You Only Look Once Unified Real-Time Object Detection",
        "authors": ["Redmon, J.", "Divvala, S.", "Girshick, R."],
        "year": 2016,
        "venue": "CVPR",
        "abstract": "We present YOLO, a unified approach to real-time object detection. Prior detection systems repurpose classifiers or localizers to perform detection. We reframe object detection as a single regression problem, directly predicting bounding boxes and class probabilities from image pixels.",
        "domain": "Computer Vision"
    },
    {
        "title": "Mask R-CNN",
        "authors": ["He, K.", "Gkioxari, G.", "Dollar, P."],
        "year": 2017,
        "venue": "ICCV",
        "abstract": "We present a conceptually simple, flexible, and general framework for object instance segmentation. Our approach efficiently detects objects in an image while simultaneously generating a high-quality segmentation mask for each instance.",
        "domain": "Computer Vision"
    },
    {
        "title": "CLIP: Learning Transferable Visual Models From Natural Language Supervision",
        "authors": ["Radford, A.", "Kim, J.", "Hallacy, C."],
        "year": 2021,
        "venue": "ICML",
        "abstract": "State-of-the-art computer vision systems are trained to predict a fixed set of predetermined object categories. We demonstrate that the simple pre-training task of predicting which image goes with which sentence is an efficient way to learn SOTA image representations from scratch on a dataset of 400 million image-text pairs.",
        "domain": "Computer Vision"
    },
    {
        "title": "DALL-E: Zero-Shot Text-to-Image Generation",
        "authors": ["Ramesh, A.", "Pavlov, M.", "Goh, G."],
        "year": 2021,
        "venue": "ICML",
        "abstract": "We explore the capability of transformer language models to generate images from text descriptions. We train a sparse transformer with 12 billion parameters to autoregressively model text and image tokens as a single stream.",
        "domain": "Generative Models"
    },
    {
        "title": "InstructGPT: Training Language Models to Follow Instructions with Human Feedback",
        "authors": ["Ouyang, L.", "Wu, J.", "Jiang, X."],
        "year": 2022,
        "venue": "NeurIPS",
        "abstract": "Making language models larger does not inherently make them better at following a user's intent. We demonstrate that fine-tuning with human feedback is effective for aligning language models with user intent.",
        "domain": "NLP"
    },
    {
        "title": "RLHF: Deep Reinforcement Learning from Human Preferences",
        "authors": ["Christiano, P.", "Leike, J.", "Brown, T."],
        "year": 2017,
        "venue": "NeurIPS",
        "abstract": "For sophisticated AI systems to approach human-level performance, we need a way to specify complex goals that machines can learn from limited feedback. We train a deep neural network to perform a task by asking humans to choose which of two video clips shows more progress.",
        "domain": "Reinforcement Learning"
    },
    {
        "title": "LSTM: Long Short-Term Memory Networks",
        "authors": ["Hochreiter, S.", "Schmidhuber, J."],
        "year": 1997,
        "venue": "Neural Computation",
        "abstract": "Learning to store information over extended time intervals by recurrent backpropagation takes a very long time, mostly because of insufficient, decaying error backflow. We briefly review Hochreiter's 1991 analysis of this problem, which shows that standard RNNs suffer from the vanishing and exploding gradient problems.",
        "domain": "NLP"
    },
    {
        "title": "Seq2Seq: Sequence to Sequence Learning with Neural Networks",
        "authors": ["Sutskever, I.", "Vinyals, O.", "Le, Q."],
        "year": 2014,
        "venue": "NeurIPS",
        "abstract": "Deep Neural Networks are powerful models that have achieved excellent performance on difficult learning tasks. Although DNNs work well whenever large labeled training sets are available, they cannot be used to map sequences to sequences. In this paper, we present a general end-to-end approach to sequence learning.",
        "domain": "NLP"
    },
    {
        "title": "Dropout: A Simple Way to Prevent Neural Networks from Overfitting",
        "authors": ["Srivastava, N.", "Hinton, G.", "Krizhevsky, A."],
        "year": 2014,
        "venue": "JMLR",
        "abstract": "Deep neural networks with a large number of parameters are very powerful machine learning systems. However, overfitting is a serious problem in such networks. Dropout is a technique for addressing this problem. The key idea is to randomly drop units along with their connections during training.",
        "domain": "Deep Learning"
    },
    {
        "title": "Batch Normalization: Accelerating Deep Network Training",
        "authors": ["Ioffe, S.", "Szegedy, C."],
        "year": 2015,
        "venue": "ICML",
        "abstract": "Training Deep Neural Networks is complicated by the fact that the distribution of each layer's inputs changes during training, as the parameters of the previous layers change. We refer to this phenomenon as internal covariate shift, and address the problem by normalizing layer inputs.",
        "domain": "Deep Learning"
    },
    {
        "title": "Adam: A Method for Stochastic Optimization",
        "authors": ["Kingma, D.", "Ba, J."],
        "year": 2015,
        "venue": "ICLR",
        "abstract": "We introduce Adam, an algorithm for first-order gradient-based optimization of stochastic objective functions, based on adaptive estimates of lower-order moments. The method is straightforward to implement, is computationally efficient, has little memory requirements, is invariant to diagonal rescaling of the gradients.",
        "domain": "Deep Learning"
    },
    {
        "title": "Layer Normalization",
        "authors": ["Ba, J.", "Kiros, J.", "Hinton, G."],
        "year": 2016,
        "venue": "arXiv",
        "abstract": "Training state-of-the-art, deep neural networks is computationally expensive. One way to accelerate training is to normalize the activities of the hidden units. We propose layer normalization, a simple technique for improving the speed of training neural networks.",
        "domain": "Deep Learning"
    },
    {
        "title": "Contrastive Language-Image Pre-Training with Negative Sampling",
        "authors": ["Chen, T.", "Kornblith, S.", "Norouzi, M."],
        "year": 2020,
        "venue": "ICML",
        "abstract": "We study an efficient contrastive learning method for image representations that does not require a memory bank or prototypes. We demonstrate that when combined with a few architectural changes, our method achieves strong performance on ImageNet classification.",
        "domain": "Computer Vision"
    },
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors": ["Lewis, P.", "Perez, E.", "Piktus, A."],
        "year": 2020,
        "venue": "NeurIPS",
        "abstract": "Large language models have shown impressive abilities to internalize knowledge during pre-training. However, they have limitations for knowledge-intensive tasks. We present a general-purpose fine-tuning recipe for retrieval-augmented generation combining pre-trained parametric and non-parametric memory.",
        "domain": "NLP"
    },
    {
        "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "authors": ["Wei, J.", "Wang, X.", "Schuurmans, D."],
        "year": 2022,
        "venue": "NeurIPS",
        "abstract": "We explore how generating a chain of thought, a series of intermediate reasoning steps, significantly improves the ability of large language models to perform complex reasoning. We show how such reasoning abilities emerge naturally in sufficiently large language models.",
        "domain": "NLP"
    },
    {
        "title": "Codex: Evaluating Large Language Models Trained on Code",
        "authors": ["Chen, M.", "Tworek, J.", "Jun, H."],
        "year": 2021,
        "venue": "arXiv",
        "abstract": "We develop Codex, a GPT language model fine-tuned on code from GitHub, and study its performance on a novel set of programming challenges. Our model solves problems from the HumanEval dataset more often than any prior approach.",
        "domain": "NLP"
    },
    {
        "title": "Toolformer: Language Models Can Teach Themselves to Use Tools",
        "authors": ["Schick, T.", "Dwivedi-Yu, J.", "Dacrema, M."],
        "year": 2023,
        "venue": "arXiv",
        "abstract": "We propose Toolformer, a model that learns to use external tools APIs by self-supervised training. We show that Toolformer enables language models to learn to use tools like calculators, search engines, and calendars with minimal human annotation.",
        "domain": "NLP"
    },
    {
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "authors": ["Hu, E.", "Shen, Y.", "Wallis, P."],
        "year": 2022,
        "venue": "ICLR",
        "abstract": "We propose a new technique, Low-Rank Adaptation (LoRA), that freezes pre-trained model weights and injects trainable rank decomposition matrices into each layer of the Transformer architecture. This greatly reduces the number of trainable parameters for downstream tasks.",
        "domain": "NLP"
    },
    {
        "title": "Scaling Laws for Neural Language Models",
        "authors": ["Kaplan, J.", "McCandlish, S.", "Henighan, T."],
        "year": 2020,
        "venue": "arXiv",
        "abstract": "We study empirical scaling laws for language model performance on the cross-entropy loss. The loss scales as a power-law with model size, dataset size, and the amount of compute used for training, with some trends spanning more than seven orders of magnitude.",
        "domain": "Deep Learning"
    },
    {
        "title": "Emergent Abilities of Large Language Models",
        "authors": ["Wei, J.", "Tay, Y.", "Bommasani, R."],
        "year": 2022,
        "venue": "TMLR",
        "abstract": "Scaling up language models has been shown to predict improvements on a wide range of downstream tasks. Many emergent abilities have been observed as language models scale up, abilities that are not present in smaller models but appear in larger ones.",
        "domain": "NLP"
    },
    {
        "title": "Chain-of-Density: Improving Dense Concise Controlled Generation",
        "authors": ["Adams, L.", "Guan, J.", "Liu, P."],
        "year": 2023,
        "venue": "arXiv",
        "abstract": "We propose Chain-of-Density, a novel approach for improving the conciseness and detail coverage of dense text generation. Our method iteratively refines generated descriptions by identifying and adding missing entities while maintaining conciseness.",
        "domain": "NLP"
    },
    {
        "title": "Segment Anything Model",
        "authors": ["Kirillov, A.", "Mintun, E.", "Ravi, N."],
        "year": 2023,
        "venue": "ICCV",
        "abstract": "We introduce the Segment Anything Model (SAM), a new promptable segmentation system that can segment any object in any image with a single prompt. SAM demonstrates strong zero-shot performance across a diverse range of segmentation tasks.",
        "domain": "Computer Vision"
    },
    {
        "title": "DINO: Self-Supervised Vision Transformers with Data-Efficient Training",
        "authors": ["Caron, M.", "Touvron, H.", "Misra, I."],
        "year": 2021,
        "venue": "ICCV",
        "abstract": "We present a new self-supervised learning approach called DINO that works particularly well with Vision Transformers. We show that DINO features can be used directly for downstream tasks without fine-tuning, achieving competitive performance.",
        "domain": "Computer Vision"
    },
    {
        "title": "Diffusion Models Beat GANs on Image Synthesis",
        "authors": ["Dhariwal, P.", "Nichol, A."],
        "year": 2021,
        "venue": "NeurIPS",
        "abstract": "We show that diffusion models can achieve image sample quality superior to generative adversarial networks while also offering benefits such as improved mode coverage and reduced sensitivity to architectural choices.",
        "domain": "Generative Models"
    },
    {
        "title": "GRPO: Group Relative Preference Optimization",
        "authors": ["Schnell, N.", "Zhang, W.", "Chen, Y."],
        "year": 2024,
        "venue": "arXiv",
        "abstract": "We propose Group Relative Preference Optimization (GRPO), an efficient alignment method that optimizes language models without requiring a critic model. GRPO groups prompts and generates multiple responses, then uses group-relative ranking for preference learning.",
        "domain": "Reinforcement Learning"
    },
    {
        "title": "Mixture of Experts with Token Routing",
        "authors": ["Roller, S.", "Sukhbaatar, S.", "Arthur, P."],
        "year": 2021,
        "venue": "NeurIPS",
        "abstract": "We present a method for conditioning a sparse mixture of experts model on an input text to route each token to appropriate experts. This allows the model to specialize different experts for different types of inputs while maintaining computational efficiency.",
        "domain": "Deep Learning"
    },
    {
        "title": "Sparse Mixture of Experts for Vision and Language",
        "authors": ["Puigcerver, J.", "Rodriqueau, C.", "Klinger, T."],
        "year": 2023,
        "venue": "arXiv",
        "abstract": "We adapt sparse mixture of experts models to multi-modal vision and language tasks. By selectively activating relevant experts based on input modality and content, we achieve strong results with reduced computational cost.",
        "domain": "Deep Learning"
    },
    {
        "title": "Retrieval-Enhanced Transformer for Long Document Understanding",
        "authors": ["Wang, S.", "Li, Y.", "Zhang, H."],
        "year": 2022,
        "venue": "EMNLP",
        "abstract": "We propose a retrieval-enhanced Transformer architecture that can effectively process long documents by retrieving and attending to relevant passages. Our method significantly improves performance on question answering and summarization tasks.",
        "domain": "NLP"
    },
    {
        "title": "Dense Passage Retrieval for Open-Domain Question Answering",
        "authors": ["Karpukhin, V.", "Oguz, B.", "Min, S."],
        "year": 2020,
        "venue": "EMNLP",
        "abstract": "We study the problem of dense passage retrieval for open-domain question answering, where the goal is to find relevant text passages given a question. We show that dense retrieval significantly outperforms traditional sparse methods like BM25.",
        "domain": "NLP"
    },
    {
        "title": "ConvNeXt: A ConvNet for the 2020s",
        "authors": ["Liu, Z.", "Mao, H.", "Cha, C."],
        "year": 2022,
        "venue": "CVPR",
        "abstract": "We present ConvNeXt, a pure convolutional network that modernizes the classic ResNet architecture to match the performance of Vision Transformers. By incorporating design elements from Transformers, ConvNeXt achieves state-of-the-art results.",
        "domain": "Computer Vision"
    },
    {
        "title": "Swin Transformer: Hierarchical Vision Transformer Using Shifted Windows",
        "authors": ["Liu, Z.", "Lin, Y.", "Cao, Y."],
        "year": 2021,
        "venue": "ICCV",
        "abstract": "We present Swin Transformer, an efficient Vision Transformer with shifted windows. The shifted windowing scheme brings efficiency by limiting self-attention computation to non-overlapping local windows while enabling cross-window connection.",
        "domain": "Computer Vision"
    },
    {
        "title": "Vision Transformers with Patch Merging and Hierarchical Design",
        "authors": ["Dosovitskiy, A.", "Beyer, L.", "Kolesnikov, A."],
        "year": 2021,
        "venue": "ICLR",
        "abstract": "We extend the Vision Transformer to hierarchical patch-based processing, enabling efficient computation for high-resolution images. Our approach combines the strengths of CNNs and Transformers for improved visual recognition.",
        "domain": "Computer Vision"
    }
]

# Citation graph: which papers cite which (by title)
# Older papers are cited by newer papers
CITATIONS = {
    "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding": ["Attention Is All You Need", "Word2Vec: Efficient Estimation of Word Representations in Vector Space", "ELMo: Deep Contextualized Word Representations"],
    "GPT-2: Language Models are Unsupervised Multitask Learners": ["GPT-3: Language Models are Few-Shot Learners", "InstructGPT: Training Language Models to Follow Instructions with Human Feedback"],
    "GPT-3: Language Models are Few-Shot Learners": ["InstructGPT: Training Language Models to Follow Instructions with Human Feedback", "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models", "Codex: Evaluating Large Language Models Trained on Code"],
    "InstructGPT: Training Language Models to Follow Instructions with Human Feedback": ["Chain-of-Thought Prompting Elicits Reasoning in Large Language Models", "Toolformer: Language Models Can Teach Themselves to Use Tools", "GRPO: Group Relative Preference Optimization"],
    "RLHF: Deep Reinforcement Learning from Human Preferences": ["InstructGPT: Training Language Models to Follow Instructions with Human Feedback", "AlphaGo: Mastering the Game of Go with Deep Neural Networks and Tree Search"],
    "ImageNet Classification with Deep Convolutional Neural Networks": ["ResNet: Deep Residual Learning for Image Recognition", "VGGNet: Very Deep Convolutional Networks for Large-Scale Image Recognition", "DQN: Playing Atari with Deep Reinforcement Learning"],
    "ResNet: Deep Residual Learning for Image Recognition": ["Inception-v4: Inception-ResNet and the Impact of Residual Connections on Learning", "Mask R-CNN", "DINO: Self-Supervised Vision Transformers with Data-Efficient Training", "ConvNeXt: A ConvNet for the 2020s"],
    "VGGNet: Very Deep Convolutional Networks for Large-Scale Image Recognition": ["Inception-v4: Inception-ResNet and the Impact of Residual Connections on Learning"],
    "YOLO: You Only Look Once Unified Real-Time Object Detection": ["Mask R-CNN"],
    "DCGAN: Unsupervised Representation Learning with Deep Convolutional GANs": ["Generative Adversarial Networks", "Stable Diffusion: High-Resolution Image Synthesis with Latent Diffusion Models"],
    "Stable Diffusion: High-Resolution Image Synthesis with Latent Diffusion Models": ["DALL-E: Zero-Shot Text-to-Image Generation", "Diffusion Models Beat GANs on Image Synthesis"],
    "DALL-E: Zero-Shot Text-to-Image Generation": ["Stable Diffusion: High-Resolution Image Synthesis with Latent Diffusion Models"],
    "DINO: Self-Supervised Vision Transformers with Data-Efficient Training": ["Swin Transformer: Hierarchical Vision Transformer Using Shifted Windows", "CLIP: Learning Transferable Visual Models From Natural Language Supervision"],
    "CLIP: Learning Transferable Visual Models From Natural Language Supervision": ["DALL-E: Zero-Shot Text-to-Image Generation", "Contrastive Language-Image Pre-Training with Negative Sampling", "Segment Anything Model"],
    "Attention Is All You Need": ["BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding", "T5: Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer", "GPT-2: Language Models are Unsupervised Multitask Learners", "DQN: Playing Atari with Deep Reinforcement Learning", "LSTM: Long Short-Term Memory Networks"],
    "Seq2Seq: Sequence to Sequence Learning with Neural Networks": ["Attention Is All You Need", "LSTM: Long Short-Term Memory Networks"],
    "LSTM: Long Short-Term Memory Networks": ["Seq2Seq: Sequence to Sequence Learning with Neural Networks", "Word2Vec: Efficient Estimation of Word Representations in Vector Space"],
    "Dropout: A Simple Way to Prevent Neural Networks from Overfitting": ["Batch Normalization: Accelerating Deep Network Training"],
    "Batch Normalization: Accelerating Deep Network Training": ["Layer Normalization", "ResNet: Deep Residual Learning for Image Recognition"],
    "Adam: A Method for Stochastic Optimization": ["Attention Is All You Need", "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding", "GPT-3: Language Models are Few-Shot Learners"],
    "Dense Passage Retrieval for Open-Domain Question Answering": ["Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", "Retrieval-Enhanced Transformer for Long Document Understanding"],
    "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks": ["InstructGPT: Training Language Models to Follow Instructions with Human Feedback", "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"],
    "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models": ["Toolformer: Language Models Can Teach Themselves to Use Tools"],
    "LoRA: Low-Rank Adaptation of Large Language Models": ["InstructGPT: Training Language Models to Follow Instructions with Human Feedback", "Mixture of Experts with Token Routing"],
    "Mixture of Experts with Token Routing": ["Sparse Mixture of Experts for Vision and Language"],
    "ConvNeXt: A ConvNet for the 2020s": ["Swin Transformer: Hierarchical Vision Transformer Using Shifted Windows"],
    "Vision Transformers with Patch Merging and Hierarchical Design": ["Swin Transformer: Hierarchical Vision Transformer Using Shifted Windows", "ConvNeXt: A ConvNet for the 2020s"]
}


def check_existing_data():
    """Check if papers already exist in the database."""
    result = db.records.find({"labels": ["PAPER"], "limit": 1})
    return len(result.data) > 0


def create_papers():
    """Create paper records with metadata."""
    print("\nCreating paper records...")
    paper_records = []
    
    for i, paper in enumerate(PAPERS):
        record = db.records.create(
            label="PAPER",
            data={
                "title": paper["title"],
                "authors": paper["authors"],
                "year": paper["year"],
                "venue": paper["venue"],
                "abstract": paper["abstract"],
                "domain": paper["domain"]
            }
        )
        paper_records.append({
            "record": record,
            "title": paper["title"]
        })
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{len(PAPERS)} papers...")
    
    print(f"  Created {len(PAPERS)} papers total.")
    return paper_records


def create_citation_edges(paper_records):
    """Create citation relationships between papers."""
    print("\nCreating citation relationships...")
    
    # Build a lookup: title -> record
    title_to_record = {p["title"]: p["record"] for p in paper_records}
    
    edge_count = 0
    for citing_title, cited_titles in CITATIONS.items():
        if citing_title not in title_to_record:
            continue
        
        citing_record = title_to_record[citing_title]
        
        for cited_title in cited_titles:
            if cited_title in title_to_record:
                db.records.attach(
                    source=citing_record,
                    target=title_to_record[cited_title],
                    options={"type": "CITES", "direction": "out"}
                )
                edge_count += 1
    
    print(f"  Created {edge_count} citation edges.")


def create_vector_index():
    """Create vector index for paper abstracts."""
    print("\nCreating vector index for abstracts...")
    
    # Check if index already exists
    existing_indexes = db.ai.indexes.find()
    for idx in existing_indexes.data:
        if idx["label"] == "PAPER" and idx["propertyName"] == "abstract":
            print("  Vector index already exists, skipping creation.")
            return idx
    
    # Create new index (external type - we provide our own vectors)
    index = db.ai.indexes.create({
        "label": "PAPER",
        "propertyName": "abstract",
        "sourceType": "external",
        "dimensions": 384,  # all-MiniLM-L6-v2 output dimension
        "similarityFunction": "cosine"
    })
    print("  Vector index created.")
    return index


def generate_embeddings_and_upsert(paper_records, index):
    """Generate embeddings for abstracts and upsert to index."""
    print("\nGenerating embeddings and upserting to index...")
    index_id = index.data["__id"]
    
    # Collect all abstracts
    abstracts = [p["record"].data["abstract"] for p in paper_records]
    
    # Generate embeddings in batch
    print("  Computing embeddings (this may take a moment)...")
    embeddings = embedding_model.encode(abstracts, show_progress_bar=True)
    
    # Prepare vectors for upsert
    items = []
    for i, paper in enumerate(paper_records):
        items.append({
            "recordId": paper["record"].id,
            "vector": embeddings[i].tolist()
        })
    
    # Upsert vectors
    print("  Upserting vectors to index...")
    db.ai.indexes.upsert_vectors(index_id, {"items": items})
    print("  Done!")


def main():
    print("=" * 60)
    print("Research Paper Discovery Engine - Database Seeding")
    print("=" * 60)
    
    # Check if data already exists
    if check_existing_data():
        print("\n⚠️  Papers already exist in the database.")
        print("   Skipping seed to avoid duplicates.")
        print("   To re-seed, delete existing PAPER records first.")
        return
    
    # Create papers
    paper_records = create_papers()
    
    # Create citation edges
    create_citation_edges(paper_records)
    
    # Create vector index
    index = create_vector_index()
    
    # Generate embeddings and upsert
    generate_embeddings_and_upsert(paper_records, index)
    
    print("\n" + "=" * 60)
    print("✅ Database seeded successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
