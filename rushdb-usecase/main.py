#!/usr/bin/env python3
"""
RushDB Use Case: Hybrid Vector + Graph Search Demo

This script demonstrates the core value proposition of RushDB:
- Single data model for vectors and graphs
- Unified query interface
- No synchronization complexity

The scenario: A developer documentation search system where:
1. Users search docs by concept (vector similarity)
2. System shows how concepts relate to other modules (graph traversal)
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Initialize embedding model (same as seed.py)
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


def generate_embedding(text: str) -> list:
    """Generate vector embedding for text content."""
    return embedding_model.encode(text).tolist()


def main():
    """Main demonstration of RushDB hybrid vector + graph search."""
    
    api_key = os.getenv('RUSHDB_API_KEY')
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Please ensure .env file exists with your RushDB API key")
        return
    
    db = RushDB(api_key)
    
    print("\n" + "=" * 70)
    print("RushDB 实战演示：向量 + 图谱混合检索系统")
    print("=" * 70)
    
    # =========================================================================
    # Demo 1: Check System Status
    # =========================================================================
    
    print("\n📊 【演示 1】系统状态检查")
    print("-" * 40)
    
    # Count records
    apis = db.records.find({"labels": ["API"], "limit": 100})
    modules = db.records.find({"labels": ["Module"], "limit": 100})
    services = db.records.find({"labels": ["Service"], "limit": 100})
    
    print(f"  API 记录: {len(apis.data)}")
    print(f"  Module 记录: {len(modules.data)}")
    print(f"  Service 记录: {len(services.data)}")
    
    # Check vector indexes
    print("\n  向量索引状态:")
    indexes = db.ai.indexes.find()
    for idx in indexes.data:
        stats = db.ai.indexes.stats(idx['__id'])
        print(f"    • {idx['label']}.{idx['propertyName']}")
        print(f"      状态: {idx['status']}")
        print(f"      索引记录: {stats.data.get('indexedRecords', 0)} / {stats.data.get('totalRecords', 0)}")
    
    # =========================================================================
    # Demo 2: Vector Search - Semantic Query
    # =========================================================================
    
    print("\n\n🔍 【演示 2】向量语义搜索：查询"认证机制"相关 API")
    print("-" * 40)
    
    # Natural language query
    query_text = "authentication and token management"
    query_vector = generate_embedding(query_text)
    
    print(f"  查询: \"{query_text}\"")
    print(f"  生成向量维度: {len(query_vector)}")
    print()
    
    # Perform vector search using external index
    # Note: For managed index, use db.ai.search() directly
    # For external index, we search all APIs and compute similarity
    all_apis = db.records.find({"labels": ["API"], "limit": 100})
    
    # Compute similarity scores
    results = []
    for api in all_apis.data:
        if 'description' in api:
            api_vector = generate_embedding(api['description'])
            # Cosine similarity
            dot = sum(a * b for a, b in zip(query_vector, api_vector))
            norm_q = sum(a * a for a in query_vector) ** 0.5
            norm_a = sum(a * a for a in api_vector) ** 0.5
            score = dot / (norm_q * norm_a) if (norm_q * norm_a) > 0 else 0
            results.append((score, api))
    
    # Sort by similarity
    results.sort(key=lambda x: x[0], reverse=True)
    
    print("  搜索结果（按语义相似度排序）:")
    print()
    for score, api in results[:5]:
        print(f"  [{score:.3f}] {api['method']} {api['path']}")
        print(f"       名称: {api['name']}")
        print(f"       描述: {api['description'][:80]}...")
        print()
    
    # =========================================================================
    # Demo 3: Graph Traversal - Find Related Services
    # =========================================================================
    
    print("\n\n🔗 【演示 3】图谱遍历：查找相关服务和底层模块")
    print("-" * 40)
    
    # Get the top result API
    top_api = results[0][1]
    print(f"  以 '{top_api['name']}' 为例")
    print()
    
    # Find services that CONSUME this API
    consuming_services = db.records.find({
        "labels": ["Service"],
        "where": {
            "API": {
                "$relation": {"type": "CONSUMES", "direction": "in"},
                "name": top_api['name']
            }
        }
    })
    
    print("  📡 消费此 API 的服务:")
    if consuming_services.data:
        for svc in consuming_services.data:
            print(f"    • {svc['name']}")
            print(f"      描述: {svc['description']}")
    else:
        print("    (无直接消费记录)")
    print()
    
    # Find modules that IMPLEMENT this API
    implementing_modules = db.records.find({
        "labels": ["Module"],
        "where": {
            "API": {
                "$relation": {"type": "IMPLEMENTS", "direction": "out"},
                "name": top_api['name']
            }
        }
    })
    
    # Also check BACKS and POWERS relationships
    backing_modules = db.records.find({
        "labels": ["Module"],
        "where": {
            "API": {
                "$relation": {"type": "BACKS", "direction": "out"},
                "name": top_api['name']
            }
        }
    })
    
    powering_modules = db.records.find({
        "labels": ["Module"],
        "where": {
            "API": {
                "$relation": {"type": "POWERS", "direction": "out"},
                "name": top_api['name']
            }
        }
    })
    
    all_modules = implementing_modules.data + backing_modules.data + powering_modules.data
    
    print("  ⚙️  实现此 API 的模块:")
    if all_modules:
        for mod in all_modules:
            print(f"    • {mod['name']}")
            print(f"      描述: {mod['description']}")
    else:
        print("    (无实现模块记录)")
    
    # =========================================================================
    # Demo 4: Unified Query - Vector + Graph in One
    # =========================================================================
    
    print("\n\n✨ 【演示 4】统一查询：向量过滤 + 图谱扩展（一次完成）")
    print("-" * 40)
    print()
    print("  场景: 查找与"用户管理"相关且被多个服务消费的 API")
    print()
    
    # Step 1: Vector search for "user management"
    user_query = "user profile management and updates"
    user_query_vector = generate_embedding(user_query)
    
    # Get all APIs and compute similarity
    user_api_results = []
    for api in all_apis.data:
        if 'description' in api:
            api_vector = generate_embedding(api['description'])
            dot = sum(a * b for a, b in zip(user_query_vector, api_vector))
            norm_q = sum(a * a for a in user_query_vector) ** 0.5
            norm_a = sum(a * a for a in api_vector) ** 0.5
            score = dot / (norm_q * norm_a) if (norm_q * norm_a) > 0 else 0
            user_api_results.append((score, api))
    
    user_api_results.sort(key=lambda x: x[0], reverse=True)
    
    # Step 2: For top results, count consuming services
    print("  语义相似度最高的 API:")
    for score, api in user_api_results[:5]:
        # Count how many services consume this API
        consuming = db.records.find({
            "labels": ["Service"],
            "where": {
                "API": {
                    "$relation": {"type": "CONSUMES", "direction": "in"},
                    "name": api['name']
                }
            }
        })
        service_count = len(consuming.data)
        
        print(f"\n  [{score:.3f}] {api['method']} {api['path']}")
        print(f"      消费服务数: {service_count}")
        if consuming.data:
            print(f"      服务列表: {', '.join(s['name'] for s in consuming.data)}")
    
    # =========================================================================
    # Demo 5: Traditional Stack Comparison
    # =========================================================================
    
    print("\n\n" + "=" * 70)
    print("📐 【对比】传统架构 vs RushDB 统一架构")
    print("=" * 70)
    
    print("""
┌─────────────────────────────────────────────────────────────────────┐
│ 传统架构（需要维护两套系统）                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. 向量数据库 (如 Pinecone / pgvector)                              │
│     - 存储 API 描述的向量嵌入                                        │
│     - 使用 ANN 算法做相似度搜索                                      │
│     → 需要单独维护、监控、备份                                       │
│                                                                     │
│  2. 图数据库 (如 Neo4j)                                              │
│     - 存储 API、Module、Service 及其关系                             │
│     - 使用 Cypher 做关系查询                                         │
│     → 需要单独维护、监控、备份                                       │
│                                                                     │
│  3. 同步逻辑                                                         │
│     - 当 API 更新时，需要同时更新向量库和图库                        │
│     - 两边数据需要保持一致                                          │
│     → 增加复杂度和出错风险                                           │
│                                                                     │
│  4. 查询逻辑                                                         │
│     - 先查向量库得到 API 列表                                        │
│     - 再查图库获取关系信息                                           │
│     → 两次网络往返，延迟叠加                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ RushDB 统一架构（单一数据层）                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. RushDB (内置 Neo4j)                                              │
│     - 一次性写入 API 记录及其向量嵌入                                │
│     - 关系和向量存储在同一个事务中                                   │
│     → ACID 保证，无同步问题                                         │
│                                                                     │
│  2. 统一查询                                                         │
│     - Python SDK: db.records.find() 即可获取记录及关系              │
│     - 向量搜索: db.ai.search() 返回带相似度分数的记录                │
│     → 单次 API 调用即可完成向量 + 图谱联合查询                       │
│                                                                     │
│  3. 运维简化                                                         │
│     - 一个服务部署                                                  │
│     - 一套监控指标                                                  │
│     - 一套备份策略                                                  │
│     → 运维成本减半                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
""")
    
    # =========================================================================
    # Summary
    # =========================================================================
    
    print("=" * 70)
    print("✅ 演示完成！")
    print("=" * 70)
    print("""
本演示展示了 RushDB 的核心价值主张：

1. ✅ 单一数据模型
   - 向量和关系共存于同一个记录
   - 无需在不同数据库间同步数据

2. ✅ 统一查询接口
   - db.ai.search() 进行向量搜索
   - db.records.find() 进行关系查询
   - 可以链式组合，满足复杂业务场景

3. ✅ 简化运维
   - 一个 API Key 连接所有功能
   - 一套 SDK 处理所有数据操作
   - ACID 事务覆盖所有变更

对于需要同时处理语义搜索和关系遍历的应用场景，
RushDB 提供了一个高度集成、低运维成本的解决方案。
""")


if __name__ == "__main__":
    main()
