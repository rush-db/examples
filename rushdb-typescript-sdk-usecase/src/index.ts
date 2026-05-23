/**
 * RushDB 知识图谱增强聊天机器人 - 入口文件
 * 
 * 本示例演示 RushDB 的图结构 + 向量搜索双层架构如何协同工作，
 * 为聊天机器人提供持久化记忆和上下文理解能力。
 */

import { config } from 'dotenv';
import { initializeKnowledgeGraph } from './schema.js';
import { createChatbot } from './chatbot.js';

// Load environment variables
config();


// Validate required environment variables
function validateEnvironment(): void {
  const apiKey = process.env.RUSHDB_API_KEY;
  const openaiKey = process.env.OPENAI_API_KEY;


  if (!apiKey) {
    console.error('❌ Error: RUSHDB_API_KEY is not set');
    console.error('   Please create a .env file with your RushDB API key');
    console.error('   Get your key from: https://dash.rushdb.com/settings/api-keys');
    process.exit(1);
  }


  if (!openaiKey) {
    console.error('❌ Error: OPENAI_API_KEY is not set');
    console.error('   Please add your OpenAI API key to .env');
    console.error('   Get your key from: https://platform.openai.com/api-keys');
    process.exit(1);
  }

  console.log('✅ Environment validation passed\n');
}

/**
 * Simulated conversation for demo purposes
 */
async function runDemoConversation(): Promise<void> {
  console.log('\n========================================');
  console.log('   RushDB 知识图谱增强聊天机器人演示');
  console.log('========================================\n');

  // Create chatbot instance for demo user
  const chatbot = createChatbot('lisi@example.com');

  // Start session
  await chatbot.startSession();

  // Simulate conversation
  const conversation = [
    '请问你们的无线耳机有什么推荐？',
    '有降噪功能吗？',
    '续航怎么样？能用多久？',
    '和之前买的那个比怎么样？',
  ];

  for (const message of conversation) {
    console.log('\n----------------------------------------');
    const response = await chatbot.processMessage(message);
    console.log('\n🤖 Bot:');
    console.log(response);

    // Add delay to make output readable
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  // End session
  await chatbot.endSession();

  console.log('\n========================================');
  console.log('   演示完成');
  console.log('========================================');
  console.log('\n📚 本演示展示的核心能力：');
  console.log('   1. 向量搜索：理解用户查询的语义意图');
  console.log('   2. 图遍历：追踪用户的购买历史和上下文');
  console.log('   3. 关系推理：关联产品之间的关系');
  console.log('   4. 意图识别：基于话题关键词推断用户意图');
  console.log('   5. 上下文感知：根据历史信息生成个性化回复');
}

/**
 * Main function
 */
async function main(): Promise<void> {
  console.log('\n🚀 RushDB Knowledge Graph Chatbot');
  console.log('   Using RushDB SDK + Vector Search + Graph Traversal\n');

  // Validate environment
  validateEnvironment();

  // Initialize knowledge graph
  await initializeKnowledgeGraph();

  // Run demo conversation
  await runDemoConversation();
}

// Run the application
main().catch((error) => {
  console.error('\n❌ Application error:', error);
  process.exit(1);
});
