# RushDB实战: 用TypeScript SDK构建知识图谱增强的聊天机器人

![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue)
![RushDB](https://img.shields.io/badge/RushDB-SDK-green)

这是一个完整的知识图谱增强聊天机器人示例，演示了 RushDB 的图结构与向量搜索双层架构如何协同工作，解决传统方案无法单独处理的复杂对话上下文问题。

## 核心概念

### 为什么需要知识图谱增强？

纯向量搜索的局限性：
- 能找到"相似问题"，但无法追踪对话历史中的上下文依赖
- 无法理解实体之间的关系（如"这个产品和用户之前购买的是同类"）
- 丢失对话的因果链条

纯图数据库的局限性：
- 语义理解差，只能做精确匹配
- 无法处理同义词、多表述的问题

**RushDB 方案**：向量搜索处理"语义理解"，图结构处理"关系推理"，两者互补。

## 知识图谱设计

### 实体类型

| Label | 说明 |
| ----- | --- |
| `User` | 聊天用户 |
| `Product` | 产品信息 |
| `Topic` | 话题/意图分类 |
| `Message` | 对话消息 |
| `Session` | 对话会话 |

### 关系类型

| 关系 | 说明 |
| ---- | --- |
| `asked_about` | 用户询问某产品/话题 |
| `purchased` | 用户购买过某产品 |
| `related_to` | 产品/话题之间相互关联 |
| `in_session` | 消息属于某个会话 |
| `replies_to` | 消息回复关系 |
| `has_intent` | 消息包含的意图 |

## 项目结构

```
rushdb-typescript-sdk-usecase/
├── package.json
├── tsconfig.json
├── .env.example
├── README.md
├── data/
│   └── seed-data.json          # 初始化数据
└── src/
    ├── index.ts                  # 入口文件
    ├── types.ts                  # TypeScript 类型定义
    ├── schema.ts                 # 图谱 schema 初始化
    ├── embeddings.ts             # 向量嵌入生成
    ├── chatbot.ts                # 聊天机器人核心逻辑
    └── context.ts                # 上下文检索策略
```

## erequisites

- Node.js >= 18.0.0
- RushDB API Key ([获取地址](https://dash.rushdb.com))
- OpenAI API Key (用于生成向量嵌入)

## Setup


### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

### 3. 初始化数据（可选）

首次运行时，程序会自动检测并加载初始化数据：

```bash
npm run start
# 看到 "Initializing knowledge graph schema..." 即开始初始化
```

## 运行

```bash
npm run start
```

预期输出：

```
=== RushDB 知识图谱聊天机器人 ===

[初始化]
✓ 初始化知识图谱 schema
✓ 加载产品信息 (3 个)
✓ 加载用户数据 (2 个)
✓ 初始化向量索引

[对话演示]
用户: 请问你们的无线耳机有什么推荐？

→ 语义搜索: "无线耳机推荐"
→ 找到相似消息: "这款蓝牙耳机音质不错，续航 30 小时"
→ 图谱检索: 查找该产品的关联信息
→ 上下文解析: 用户是新客户，没有购买历史

🤖 Bot: 这款蓝牙耳机是我们最畅销的无线耳机，采用最新蓝牙 5.3 技术，
      续航长达 30 小时，目前特价优惠中。

      您是否还有其他问题？

---
用户: 有降噪功能吗？

→ 上下文加载: 当前产品 "蓝牙耳机"
→ 意图识别: 降噪功能咨询
→ 图谱查询: 获取产品特性

🤖 Bot: 是的！蓝牙耳机配备主动降噪功能 (ANC)，
      支持通透模式，适合各种使用场景。

---
用户: 和之前买的那个比怎么样？

→ 追踪购买历史: 用户有 "入耳式耳机" 购买记录
→ 图谱查询: 获取购买产品的规格
→ 对比分析: 两个产品的规格对比

🤖 Bot: 对比您之前购买的入耳式耳机：
      • 降噪: 蓝牙耳机 (ANC) > 入耳式耳机 (被动降噪)
      • 价格: 蓝牙耳机 ¥399 > 入耳式耳机 ¥199
      • 续航: 蓝牙耳机 30h > 入耳式耳机 20h
      您要升级到这个新款吗？
```

## 核心代码流程

### 1. Schema 初始化

```sdk
// 创建实体标签和索引
await db.records.create({ label: 'Product', data: { name: '蓝牙耳机' } })
await db.ai.indexes.create({
  label: 'Message',
  propertyName: 'content',
  dimensions: 1536,
  sourceType: 'external'
})
___SPLIT___
// TypeScript
await db.records.create({ label: 'Product', data: { name: '蓝牙耳机' } })
await db.ai.indexes.create({
  label: 'Message',
  propertyName: 'content',
  dimensions: 1536,
  sourceType: 'external'
})
```

### 2. 消息存储

```sdk
// 在事务中创建消息并建立关系
const tx = await db.transactions.begin()
const message = await db.records.create({
  label: 'Message',
  data: { content: '请问有降噪耳机吗', role: 'user', timestamp: Date.now() }
}, tx)
await db.records.attach({
  source: message,
  target: session,
  options: { type: 'in_session', direction: 'out' }
}, tx)
await tx.commit()
___SPLIT___
// TypeScript
const tx = await db.transactions.begin()
const message = await db.records.create({
  label: 'Message',
  data: { content: '请问有降噪耳机吗', role: 'user', timestamp: Date.now() }
}, tx)
await db.records.attach({
  source: message,
  target: session,
  options: { type: 'in_session', direction: 'out' }
}, tx)
await tx.commit()
```

### 3. 向量语义搜索

```sdk
const { data: similar } = await db.ai.search({
  propertyName: 'content',
  query: userMessage,
  labels: ['Message'],
  limit: 5
})
___SPLIT___
// TypeScript
const { data: similar } = await db.ai.search({
  propertyName: 'content',
  query: userMessage,
  labels: ['Message'],
  limit: 5
})
```

### 4. 图谱关系查询

```sdk
const { data: history } = await db.records.find({
  labels: ['Message'],
  where: { Session: { id: sessionId } },
  limit: 10
})
___SPLIT___
// TypeScript
const { data: history } = await db.records.find({
  labels: ['Message'],
  where: { Session: { id: sessionId } },
  limit: 10
})
```

## Query Strategy: 双层检索

```
用户输入
    ↓
┌─────────────────┐
│ Layer 1: 向量搜索 │
│ 语义理解层       │
│ - 找到相似问题   │
│ - 理解用户意图   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Layer 2: 图遍历  │
│ 关系推理层       │
│ - 追踪上下文     │
│ - 关联实体       │
│ - 购买历史       │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Context Assembly │
│ 组合检索结果     │
│ 生成回复策略     │
└─────────────────┘
```

## 技术栈

- **RushDB SDK** (`@rushdb/javascript-sdk`) - 图存储 + 向量索引
- **OpenAI Embeddings** - 生成文本向量
- **TypeScript** - 类型安全

## 学习路径

1. `src/schema.ts` - 理解图谱设计
2. `src/chatbot.ts` - 理解核心逻辑
3. `src/context.ts` - 理解双层检索策略
4. `src/index.ts` - 理解整体流程

## 参考链接

- [RushDB 文档](https://docs.rushdb.com)
- [GitHub 示例库](https://github.com/rush-db/examples/tree/main/rushdb-typescript-sdk-usecase)
- [RushDB Dashboard](https://dash.rushdb.com)
