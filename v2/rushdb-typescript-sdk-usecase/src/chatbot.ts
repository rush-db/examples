import { db, LABELS, RELATIONSHIPS } from './schema.js';
import { generateEmbedding } from './embeddings.js';
import { queryContext, getProductByName, detectIntent } from './context.js';
import type { RushDBRecord, Session, Message } from './types.js';


/**
 * Knowledge Graph Enhanced Chatbot
 * 
 * Architecture:
 * - Vector Search Layer: Semantic understanding of user queries
 * - Graph Traversal Layer: Context and relationship resolution
 * - Response Generation: Combines both layers for contextual responses
 */
export class KnowledgeGraphChatbot {
  private sessionId: string | null = null;
  private currentUser: RushDBRecord | null = null;
  private currentProduct: RushDBRecord | null = null;
  private messageHistory: RushDBRecord[] = [];

  constructor(private userEmail: string = 'lisi@example.com') {}

  /**
   * Start a new conversation session
   */
  async startSession(): Promise<void> {
    console.log(`\n🔵 Starting session for user: ${this.userEmail}`);

    // Create new session record
    const session = await db.records.create({
      label: LABELS.SESSION,
      data: {
        userId: this.userEmail,
        createdAt: Date.now(),
        status: 'active',
      },
    });

    this.sessionId = session.id;
    console.log(`  Session ID: ${this.sessionId}`);

    // Load or create user
    await this.loadUser();

    // Load purchase history
    await this.loadPurchaseHistory();
  }

  /**
   * Load user record
   */
  private async loadUser(): Promise<void> {
    const { data: users } = await db.records.find({
      labels: [LABELS.USER],
      where: { email: this.userEmail },
      limit: 1,
    });

    if (users.length > 0) {
      this.currentUser = users[0];
      console.log(`  Loaded user: ${(this.currentUser as { name: string }).name}`);
    }
  }

  /**
   * Load user's purchase history
   */
  private async loadPurchaseHistory(): Promise<void> {
    if (!this.currentUser) return;

    const { data: purchases } = await db.records.find({
      labels: [LABELS.PRODUCT],
      where: {
        [LABELS.USER]: {
          $relation: { type: RELATIONSHIPS.PURCHASED, direction: 'in' },
          email: this.userEmail,
        },
      },
    });

    console.log(`  Purchase history: ${purchases.length} products`);
    if (purchases.length > 0) {
      this.messageHistory = purchases;
    }
  }

  /**
   * Process user message and generate response
   */
  async processMessage(userMessage: string): Promise<string> {
    console.log(`\n🟢 USER: ${userMessage}`);

    // Step 1: Store user message in graph
    await this.storeMessage(userMessage, 'user');

    // Step 2: Query context from both layers
    const context = await queryContext(
      userMessage,
      this.userEmail,
      this.currentProduct ? (this.currentProduct as { name: string }).name : undefined
    );

    // Step 3: Detect intent
    const intent = await detectIntent(userMessage);

    // Step 4: Identify if user is asking about a specific product
    await this.identifyProductContext(userMessage);

    // Step 5: Generate response based on context
    const response = await this.generateResponse(userMessage, context, intent);


    // Step 6: Store assistant response
    await this.storeMessage(response, 'assistant');

    return response;
  }

  /**
   * Store a message in the knowledge graph with vector embedding
   */
  private async storeMessage(content: string, role: 'user' | 'assistant'): Promise<void> {
    if (!this.sessionId) return;


    const tx = await db.transactions.begin();


    try {
      // Generate vector embedding
      const vector = await generateEmbedding(content);


      // Create message record with embedding
      const message = await db.records.create(
        {
          label: LABELS.MESSAGE,
          data: {
            content,
            role,
            timestamp: Date.now(),
            intent: role === 'user' ? await detectIntent(content) : undefined,
          },
        },
        tx
      );

      // Attach to session
      await db.records.attach(
        {
          source: message,
          target: { id: this.sessionId } as RushDBRecord,
          options: { type: RELATIONSHIPS.IN_SESSION, direction: 'out' },
        },
        tx
      );


      // If user message, check for product references
      if (role === 'user' && this.currentProduct) {
        await db.records.attach(
          {
            source: message,
            target: this.currentProduct,
            options: { type: RELATIONSHIPS.ASKED_ABOUT, direction: 'out' },
          },
          tx
        );
      }

      await tx.commit();
      this.messageHistory.push(message);
    } catch (error) {
      await tx.rollback();
      throw error;
    }
  }

  /**
   * Identify product context from message
   */
  private async identifyProductContext(message: string): Promise<void> {
    const lowerMessage = message.toLowerCase();

    // Product name keywords
    const productKeywords = [
      '蓝牙耳机', '入耳式', '头戴式', '音箱', '耳机',
      'pro', '无线',
    ];


    for (const keyword of productKeywords) {
      if (lowerMessage.includes(keyword.toLowerCase())) {
        // Try to find the product
        const { data: products } = await db.records.find({
          labels: [LABELS.PRODUCT],
          where: {
            name: { $contains: keyword },
          },
          limit: 1,
        });

        if (products.length > 0) {
          this.currentProduct = products[0];
          console.log(`  📦 Current product: ${(this.currentProduct as { name: string }).name}`);
          return;
        }
      }
    }
  }

  /**
   * Generate contextual response based on retrieved context
   */
  private async generateResponse(
    userMessage: string,
    context: Awaited<ReturnType<typeof queryContext>>,
    intent: string | null
  ): Promise<string> {
    console.log('\n🔔 Generating response...');

    // Build response components
    const responseParts: string[] = [];

    // Analyze similar messages
    if (context.similarMessages.length > 0) {
      const topMatch = context.similarMessages[0];
      const similarContent = (topMatch.record as { content: string }).content;
      const score = topMatch.score;
      console.log(`  → Best match (score: ${score.toFixed(3)}): "${similarContent}"`);

    }

    // Generate response based on intent
    switch (intent) {
      case '降噪功能':
        responseParts.push(this.generateNoiseCancellationResponse());
        break;


      case '续航问题':
        responseParts.push(this.generateBatteryResponse());
        break;


      case '产品对比':
        responseParts.push(this.generateComparisonResponse(context));
        break;

      case '产品推荐':
        responseParts.push(this.generateRecommendationResponse(context));
        break;


      default:
        responseParts.push(this.generateDefaultResponse(context));
    }

    return responseParts.join('\n');
  }

  /**
   * Generate noise cancellation feature response
   */
  private generateNoiseCancellationResponse(): string {
    if (this.currentProduct) {
      const product = this.currentProduct as { name: string; features: string[] };
      const hasANC = product.features?.includes('主动降噪');

      if (hasANC) {
        return `是的！${product.name} 配备主动降噪功能 (ANC)，支持通透模式。\n` +
               `• 降噪深度可达 35dB\n` +
               `• 一键切换通透模式\n` +
               `• 适合各种使用场景`;
      } else {
        return `${product.name} 采用被动降噪设计，通过物理隔音达到降噪效果。\n` +
               `如果您需要主动降噪功能，推荐看看我们的「蓝牙耳机 Pro」或「头戴式耳机」`;
      }
    }

    return '我们的耳机产品中，蓝牙耳机 Pro 和头戴式耳机都配备了主动降噪功能 (ANC)，\n' +
           '而入耳式耳机采用的是被动降噪设计。\n' +
           '您想了解哪款产品的具体降噪效果？';
  }

  /**
   * Generate battery/usage time response
   */
  private generateBatteryResponse(): string {
    if (this.currentProduct) {
      const product = this.currentProduct as { name: string; features: string[] };
      const batteryFeature = product.features?.find((f) => f.includes('小时续航'));

      if (batteryFeature) {
        return `📊 ${product.name} 的电池续航信息：\n` +
               `• ${batteryFeature}\n` +
               `• 支持快充，充电 10 分钟可使用 2 小时\n` +
               `• 采用 USB-C 充电接口`;
      }
    }

    return '我们的耳机续航能力如下：\n' +
           '• 入耳式耳机：20 小时\n' +
           '• 蓝牙耳机 Pro：30 小时\n' +
           '• 头戴式耳机：40 小时\n' +
           '您想了解哪款产品的详细信息？';
  }

  /**
   * Generate product comparison response
   */
  private generateComparisonResponse(
    context: Awaited<ReturnType<typeof queryContext>>
  ): string {
    const purchases = context.purchaseHistory;

    if (purchases.length > 0) {
      const purchased = purchases[0] as { name: string; features: string[]; price: number };

      const current = this.currentProduct as { name: string; features: string[]; price: number } | null;

      if (current && current.name !== purchased.name) {
        return `📊 对比「${purchased.name}」和「${current.name}」：\n\n` +
               `| 特性 | ${purchased.name} | ${current.name} |\n` +
               `|------|-----------------|---------------|\n` +
               `| 价格 | ¥${purchased.price} | ¥${current.price} |\n` +
               `| 降噪 | ${purchased.features?.includes('主动降噪') ? 'ANC' : '被动'} | ${current.features?.includes('主动降噪') ? 'ANC' : '被动'} |\n` +
               `| 续航 | ${purchased.features?.find((f) => f.includes('小时')) || 'N/A'} | ${current.features?.find((f) => f.includes('小时')) || 'N/A'} |\n\n` +
               `总体来说，${current.name} 在降噪和续航方面都有升级。`;
      }
    }

    return '您想对比哪两款产品？我们的主要产品线包括：\n' +
           '• 入耳式耳机 (¥199) - 高性价比\n' +
           '• 蓝牙耳机 Pro (¥399) - 热门旗舰\n' +
           '• 头戴式耳机 (¥599) - 专业音质';
  }

  /**
   * Generate product recommendation response
   */
  private generateRecommendationResponse(
    context: Awaited<ReturnType<typeof queryContext>>
  ): string {
    const purchases = context.purchaseHistory;


    if (purchases.length > 0) {
      return '根据您之前的购买记录，您已经购买了「入耳式耳机」。\n' +
             '如果您需要升级，我们推荐「蓝牙耳机 Pro」，\n' +
             '它配备主动降噪功能，续航提升 50%，是入耳式的完美升级选择。';
    }


    return '🎧 无线耳机推荐：\n\n' +
           '我们有以下几款无线耳机：\n\n' +
           '1️⃣ **蓝牙耳机 Pro** (¥399) - 性价比之选\n' +
           '   主动降噪 + 30小时续航 + 蓝牙5.3\n\n' +
           '2️⃣ **头戴式耳机** (¥599) - 音质发烧友\n' +
           '   Hi-Res认证 + 40小时续航 + 折叠设计\n\n' +
           '3️⃣ **入耳式耳机** (¥199) - 入门首选\n' +
           '   轻巧便携 + 20小时续航\n\n' +
           '您更关心降噪、音质还是价格呢？';
  }

  /**
   * Generate default response
   */
  private generateDefaultResponse(
    context: Awaited<ReturnType<typeof queryContext>>
  ): string {
    if (context.similarMessages.length > 0) {
      const topMatch = context.similarMessages[0].record as { content: string; role: string };


      if (topMatch.role === 'assistant') {
        return topMatch.content;
      }
    }

    return '感谢您的咨询！我是您的智能购物助手。\n' +
           '我可以帮您：\n' +
           '• 介绍我们的产品特点和功能\n' +
           '• 比较不同产品的规格和价格\n' +
           '• 根据您的需求推荐合适的产品\n' +
           '• 解答关于降噪、续航等问题\n\n' +
           '请告诉我您想了解什么？';
  }


  /**
   * End the conversation session
   */
  async endSession(): Promise<void> {
    if (this.sessionId) {
      await db.records.update(
        { id: this.sessionId } as RushDBRecord,
        { status: 'closed' }
      );
    }
    console.log('\n🔴 Session ended');
  }
}

/**
 * Factory function to create chatbot instance
 */
export function createChatbot(userEmail?: string): KnowledgeGraphChatbot {
  return new KnowledgeGraphChatbot(userEmail);
}
