# RAG 知识检索增强设计

> 状态：核心链路与完整语料已实现；人工许可复核待完成
> 日期：2026-07-28
> 落地目标：`docs/agent-behavior-spec.md` 的 I24（知识问答）与 `docs/agent-intelligence-plan.md` P1 第 5 项「知识库 tool」
> 相关文档：[agent-design.md](../../agent-design.md)、[agent-behavior-spec.md](../../agent-behavior-spec.md)、[architecture.md](../../architecture.md)、[testing.md](../../testing.md)

---

## 1. 背景

项目当前的「知识库」是空壳：

| 现状 | 位置 | 问题 |
|------|------|------|
| `knowledge_base` 表已建 | `backend/app/db/models.py:208` | 字段仅 title/content/source/tags，库中无任何语料 |
| `GET /knowledge/search/{query}` | `backend/app/api/endpoints/knowledge.py:122` | `ilike '%q%'` 硬匹配，`score` 恒为 `1.0`，无排序能力 |
| ChromaDB 向量检索实验 | `backend/app/ml/llm_service.py` | README 已标注为遗留代码，不在主路径 |
| `KnowledgeView.vue` | `frontend/src/views/KnowledgeView.vue` | 477 行纯 mock 页，`knowledgeList = ref([])`，无任何 API 调用 |
| Agent 工具集 | `backend/app/agent/tools.py` | 六个工具全部围绕用户自有数据，无知识检索能力 |

因此，用户问「运动前后要注意什么」「低血糖怎么处理」这类**非个人数据**的常识问题时，Agent 只能凭模型记忆自由生成——这正是项目在 `agent-intelligence-plan.md §1.1` 中列为首要痛点的「套壳」行为，且在健康场景下风险最高。

本设计为 Agent 补上一条有出处、可核对、可降级的知识检索通路。

## 2. 目标与非目标

### 目标

1. 从权威公共领域来源构建一份版本化的中文糖尿病自我管理语料，随仓库提交，clone 即可演示。
2. 提供混合检索器（中文 BM25 底座 + 可选向量叠加），检索结果**必带来源出处**。
3. 以第 7 个 Agent 工具 `search_knowledge` 接入，遵循项目既有的「模型只选工具、Python 执行」架构。
4. 断网 / 无 LLM 时，规则模式仍能回答知识型问题。
5. 前端在已有工具轨迹区渲染来源引用，让「有据可查」在界面上可见。

### 非目标

- 不做实时联网检索。运行时不发起任何对外抓取。
- 不做临床指南、诊断规则、用药剂量建议。语料只收自我管理科普层面的内容。
- 不引入向量数据库组件（Chroma / LanceDB / FAISS）。
- 不引入本地 embedding 模型（sentence-transformers / torch）。
- 不重做 `KnowledgeView.vue`（见 §15 待办）。
- 不引入 Alembic（见 §15 待办）。

## 3. 架构

```
[离线·一次性]  backend/scripts/ingest_knowledge.py
   白名单 URL → 抽正文 → LLM 中文改写 → 切片 → (可选) 算 embedding
        └→ data/knowledge/corpus.jsonl
           data/knowledge/corpus.meta.json
           data/knowledge/LICENSES.md          ← 三项产物均提交进 Git

[部署时·非 CI]  backend/scripts/seed_knowledge.py   幂等 upsert
        └→ knowledge_base (文档级) + knowledge_chunks (片段级)

[运行时]  app/services/knowledge_retrieval.py :: KnowledgeRetriever
   中文 BM25 ──┐
                ├─ RRF 融合 → top-k Citation
   向量余弦(可选)┘     端点未配 / 超时 / 报错 → 退回纯 BM25

        ├─→ Agent tool  search_knowledge
        └─→ REST  GET /api/v1/knowledge/search
                        │
                HealthAgent → reply 带 [1][2] 角标，tool_results 带 citations
                        │
                AssistantView → 工具轨迹区渲染来源引用卡
```

核心约束：**语料是版本化的构建产物**。摄取脚本不参与运行时、不参与 CI、不在测试中执行。

## 4. 数据源与许可

### 4.1 选定来源

| source_key | 站点 | 选择理由 |
|---|---|---|
| `niddk` | National Institute of Diabetes and Digestive and Kidney Diseases（NIH） | 糖尿病自我管理科普覆盖最系统 |
| `medlineplus` | MedlinePlus（NLM） | 主题页结构规整，适合切片 |

最终白名单为 NIDDK 38 篇、MedlinePlus 22 篇，共 60 个唯一 URL。CDC 曾作为候选来源，但主站在构建环境返回 403，官方 Media Library 的 Usage Guidelines 又明确禁止 syndicated content 再分发，因此本轮不纳入版本化语料。完整核对见 [`docs/research/2026-07-28-rag-corpus-source-review.md`](../../research/2026-07-28-rag-corpus-source-review.md)。

### 4.2 许可处理（必做）

已在线核对 NIDDK 与 MedlinePlus 的官方内容使用声明，并把许可核实保留为管道强制环节：

1. `ingest_knowledge.py` 抓取每个页面时，一并抓取该站点的 copyright / content-usage 声明，连同 `retrieved_at` 写入 `data/knowledge/LICENSES.md`，并把逐文档的 `license` 字段写进 corpus。
2. **首次运行摄取脚本后，必须人工复核 `LICENSES.md`**，确认每个来源确为公共领域或允许再分发；任何存疑来源从 `sources.py` 白名单中移除后重跑。
3. 该复核是本特性的交付前置条件，写入 §13 验收标准。

### 4.3 抓取范围

`backend/scripts/sources.py` 显式枚举 URL 白名单，**不做广度爬虫**——顺链接爬出去极易抓到非公共领域的第三方内容。

主题清单（约 20 个主题簇，每簇 2–3 篇，合计 40–60 文档）：

糖尿病类型与诊断 / 糖尿病前期 / 血糖自我监测 / 目标范围与 A1C / 低血糖识别与处理 / 高血糖与酮症 / 碳水化合物与饮食规划 / 运动与活动 / 体重管理 / 足部护理 / 眼部并发症 / 肾脏并发症 / 神经病变 / 心血管风险 / 用药依从性（不含具体剂量） / 生病日管理 / 旅行 / 妊娠糖尿病 / 戒烟 / 心理健康与糖尿病倦怠。

脚本尊重目标站 `robots.txt`，按 `max(本地 1 秒下限, robots crawl-delay)` 节流并带可识别的 User-Agent；NIDDK 当前实际间隔为 10 秒。

## 5. 数据模型

### 5.1 `knowledge_base`（既有表，升格为文档级）

新增列全部 nullable，兼容存量行与既有 CRUD API：

| 列 | 类型 | 用途 |
|---|---|---|
| `source_key` | String(32) | 当前语料为 `niddk` / `medlineplus`，支持按源过滤与按源重跑 |
| `source_url` | String(512) | 引用链接，前端可点 |
| `title_en` | String(255) | 英文原标题 |
| `license` | String(255) | 抓取时从源站记录的许可声明 |
| `retrieved_at` | DateTime | 抓取时间，回答中可标注「资料截至」 |
| `content_hash` | String(64) | SHA-256，幂等 upsert 依据 |

既有列语义：`title` 存中文标题，`content` 存中文改写全文，`source` 保留原语义，`tags` 存主题簇标签。

### 5.2 `knowledge_chunks`（新表）

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | String(36) PK | uuid |
| `document_id` | String(36) FK → `knowledge_base.id` | 级联删除 |
| `chunk_index` | Integer | 文档内序号 |
| `text_zh` | Text | 中文改写片段，BM25 索引建立在此列 |
| `text_en` | Text | 对应英文原文摘录，供核对 |
| `char_count` | Integer | 中文字符数 |
| `embedding` | JSON nullable | 离线预计算向量 |
| `embedding_model` | String(64) nullable | 生成该向量的模型名 |
| `created_at` | DateTime | |

唯一约束：`(document_id, chunk_index)`。

### 5.3 迁移

项目没有 Alembic，`Base.metadata.create_all` 能建出 `knowledge_chunks`，但不会给既有 `knowledge_base` 加列。

方案：`seed_knowledge.py` 内置一段幂等的列检测与补齐——SQLite 走 `PRAGMA table_info`，MySQL 走 `information_schema.columns`，缺失列执行 `ALTER TABLE ... ADD COLUMN`。约 30 行，无新依赖，可重复执行。

引入 Alembic 是正确方向，但属独立的基建改造，本次不做，记入 §15。

## 6. 语料管道

### 6.1 `backend/scripts/ingest_knowledge.py`

流水线：`fetch → extract → chunk(英文) → rewrite(逐 chunk) → embed(可选) → emit`

**先切片、后改写**，顺序是刻意的：在英文正文上切好边界再逐片改写，`text_zh` 与 `text_en` 天然一一对齐；若先整篇改写再切分，两种语言的切分边界无法对齐，`text_en` 就失去核对价值。

- **fetch**：按 `sources.py` 白名单抓取，记录 `retrieved_at` 与站点许可声明。
- **extract**：每个源一个 extractor，HTML → 正文纯文本。NIDDK 从真实 `h1` 开始，剥离面包屑、目录、脚注、References、Clinical Trials 与研究尾部；MedlinePlus 只取许可明确覆盖的 `#topic-summary`。
- **chunk**：在英文正文上按句子和单词边界切分，目标 800–1100 英文字符，重叠约 150 英文字符。
- **rewrite**：对每个英文 chunk 调用项目既有的 OpenAI-compatible 客户端做英译中改写，产出对应 `text_zh`。Prompt 硬约束：
  1. 只做语言转换与压缩，禁止新增任何原文没有的事实；
  2. 数字、单位、阈值、百分比原样保留；
  3. 禁止产出诊断结论、处方或剂量建议；
  4. 保持科普语气，不使用第一人称。
- **rewrite fallback**：默认仍使用项目 OpenAI-compatible 客户端；构建环境无可用端点时可显式传 `--rewrite-provider google`。fallback 会缓存逐段结果、轮换地区入口、保护数字表达，并拒绝包含连续未翻译英文句子的结果。
- **quality gates**：全部 chunk 逐条校验数字一致性、中文完整性、字符数和来源字段；默认只有 40–60 篇、300–500 chunks 且 0 失败时才覆盖现有产物，调试部分输出必须显式传 `--allow-partial`。
- **embed**（可选）：`EMBEDDING_ENABLED=true` 时对每个 chunk 的 `text_zh` 调 `/v1/embeddings` 预计算向量。
- **emit**：写出三个产物。文档级 `content` 为该文档全部 `text_zh` 按序拼接。

命令行开关：`--only <source_key>` / `--url <allowlisted-url>` / `--rewrite-provider <llm|google>` / `--no-rewrite` / `--no-embed` / `--dry-run` / `--allow-partial` / `--limit <n>`。

### 6.2 产物

| 文件 | 内容 |
|---|---|
| `data/knowledge/corpus.jsonl` | 每行一个文档，含 meta 与 chunks 数组 |
| `data/knowledge/corpus.meta.json` | 源清单、文档数、chunk 数、生成时间、改写模型名、embedding 模型名 |
| `data/knowledge/LICENSES.md` | 逐源许可声明与抓取时间，供人工复核 |

三项产物均提交进 Git。当前 `corpus.jsonl` 约 1.3 MB。

### 6.3 `backend/scripts/seed_knowledge.py`

读 `corpus.jsonl` → 补齐列（§5.3）→ 按 `content_hash` 幂等 upsert 文档与 chunk。同 hash 跳过，hash 变更则替换该文档全部 chunk。支持 `--corpus <path>` 指向测试语料。

## 7. 检索器

`backend/app/services/knowledge_retrieval.py`

对外只暴露一个入口：

```python
class Citation(BaseModel):
    index: int            # 本次检索结果内的 1-based 序号，即回复中 [1][2] 的角标
    chunk_id: str
    document_id: str
    title: str
    source_key: str
    source_url: str | None
    license: str | None
    retrieved_at: str | None
    text_zh: str
    text_en: str | None
    score: float

class RetrievalResult(BaseModel):
    citations: list[Citation]
    count: int
    retrieval: Literal["bm25", "bm25+vector"]
    degraded: bool

class KnowledgeRetriever:
    def __init__(self, db: Session, embedder: Embedder | None = None) -> None: ...
    def search(self, query: str, *, limit: int = 3, source_key: str | None = None) -> RetrievalResult: ...
```

### 7.1 中文分词

字符 bigram + ASCII 词的混合切分，不引入 jieba。`低血糖怎么办` → `低血 / 血糖 / 糖怎 / 怎么 / 么办`。

取舍说明：jieba 分词质量更好，但需要一个带词典的额外依赖；bigram 零依赖、召回略糙，对几百条 chunk 的语料足够，且「血糖」「胰岛素」「并发症」这类关键术语能稳定命中。

完整语料验收后补充一层小型确定性同义词扩展（如「运动」→「身体活动 / 体力活动 / 健康生活」、「A1C」→「糖化血红蛋白」），并把文档标题 token 以 4 倍频次加入对应 chunk 的 BM25 词频。该层不调用模型、不改变原始 query 的向量检索输入。

### 7.2 BM25

标准参数 `k1=1.5`、`b=0.75`，纯 Python 实现倒排索引。

索引在模块级单例中缓存，首次查询时从 DB 拉全量 chunk 构建，以语料 `content_hash` 汇总值做失效判断。500 chunk 的索引内存占用低于 5MB，构建耗时低于 100ms。

### 7.3 向量层（可选）

新增配置：

| 变量 | 默认 | 说明 |
|---|---|---|
| `EMBEDDING_ENABLED` | `false` | 总开关 |
| `EMBEDDING_BASE_URL` | 空 | OpenAI-compatible `/v1` |
| `EMBEDDING_API_KEY` | 空 | |
| `EMBEDDING_MODEL` | 空 | |
| `EMBEDDING_TIMEOUT_SECONDS` | `10` | |

chunk 向量离线预计算并随语料入库；运行时只对 query 调一次 `/v1/embeddings`，纯 Python 计算余弦相似度。

性能说明：500 chunk × 1536 维在纯 Python 约 100–200ms。整个 Agent 请求本就要等 LLM 数秒，该量级可接受，故不为此引入 numpy。

### 7.4 融合

RRF（Reciprocal Rank Fusion）：`score = Σ 1 / (60 + rank_i)`。不要求两路分数同量纲，比加权和稳定。

仅 BM25 可用时，`retrieval="bm25"`；向量层因故不可用时额外置 `degraded=true`。

## 8. Agent 集成

### 8.1 工具定义

在 `HealthToolRegistry._specs` 中新增：

```python
class _SearchKnowledgeArgs(_StrictArgs):
    query: str = Field(min_length=2, max_length=200)
    limit: int = Field(default=3, ge=1, le=5)
```

描述：`检索糖尿病自我管理的权威科普资料；回答常识性问题前必须先调用。不用于查询用户本人的血糖、饮食或档案数据。`

`ToolResultDTO.data` 载荷：

```json
{
  "citations": [
    {"index": 1, "title": "低血糖的识别与处理", "source_key": "niddk",
     "source_url": "https://…", "license": "…", "retrieved_at": "2026-07-28",
     "text_zh": "…", "text_en": "…", "score": 0.031}
  ],
  "count": 2,
  "retrieval": "bm25",
  "degraded": false
}
```

`ToolResultDTO.data` 已是 `Optional[Any]`，`backend/app/agent/schemas.py` 无需修改。

### 8.2 系统提示

`backend/app/agent/prompts.py` 的 `SYSTEM_PROMPT` 追加两条规则：

7. 用户询问糖尿病常识、并发症、运动与饮食原则等非个人数据的问题时，必须先调用 `search_knowledge`；只能基于返回片段作答，并在相应句子末尾用 `[1]` `[2]` 标注对应来源序号。
8. 检索无结果时，直接说明「知识库中没有找到相关资料」，不得凭记忆作答。

### 8.3 规则模式降级

`backend/app/agent/runtime.py` 的 `fallback()` 新增知识路由，**位置在现有写入 / 统计 / 查询分支之后、兜底文案之前**。

顺序是硬性要求：「记录血糖 6.5」这类写意图必须优先匹配，顺序错了会破坏已有的 I10–I12 行为。测试须包含针对该优先级的回归断言。

触发条件：命中知识关键词集合（低血糖 / 高血糖 / 并发症 / 运动 / 胰岛素 / 糖化 / 足部 / 眼底 / 饮食原则 / 碳水 等）且未命中前序分支。行为：调用检索器，渲染 top-k 的标题 + 首段 + 来源链接。

由此，断网状态下知识问答仍可用，与项目既有降级哲学一致。

## 9. REST 接口

`GET /api/v1/knowledge/search` 重写：

| 项 | 旧 | 新 |
|---|---|---|
| 路径 | `/search/{query}` | `/search` |
| 参数 | 路径参数 | `?q=&limit=&source=` |
| 分数 | 恒为 `1.0` | 真实 RRF 分数 |
| 返回 | `List[dict]` | `RetrievalResult` |

**这是破坏性变更。** 前端无任何调用方——`KnowledgeView.vue` 中没有一行 API import——故无消费者受影响。变更须记入 `docs/api.md`。

鉴权维持现状（`get_current_user`）。

## 10. 前端

`frontend/src/views/AssistantView.vue` 已有 `tool-trace-item` 结构，改动收敛于此：

- `trace.name === 'search_knowledge'` 且 `trace.result.ok` 时，不再渲染原始 JSON `<pre>`，改渲染来源引用卡列表：序号角标、中文标题、源站 tag、「查看原文」外链（`target="_blank"` + `rel="noopener noreferrer"`）、可折叠的英文原句。
- `degraded === true` 时显示「向量检索不可用，已用关键词检索」小 tag。
- `count === 0` 时显示「知识库中未找到相关资料」空态。

`frontend/src/api/agent.ts` 增加 `Citation` 与 `KnowledgeToolData` 接口定义。

其余页面不动。

## 11. 错误处理

| 情况 | 行为 |
|---|---|
| 语料未 seed（0 chunk） | `ok=true, count=0`，Agent 回复知识库为空，不报错 |
| `EMBEDDING_ENABLED=false` | 静默走纯 BM25，`retrieval="bm25"`，`degraded=false` |
| embedding 端点超时 / 5xx | 记 info 日志，退回 BM25，`degraded=true` |
| query 过短或非法 | Pydantic 校验拒绝，`ok=false` 并附原因 |
| 索引构建失败 | 记 exception 日志，`ok=false`；由 `HealthToolRegistry.dispatch` 既有 try/except 兜住 |

原则与既有六个工具一致：工具层异常不上抛到 HTTP 层，Agent 不返回 500。

## 12. 测试

全部离线执行，不联网、不依赖真实 LLM、不依赖真实 `corpus.jsonl`。

| 测试文件 | 覆盖点 |
|---|---|
| `tests/test_knowledge_retrieval.py`（新） | BM25 打分与排序正确性；bigram 切分；RRF 融合；空语料；`source_key` 过滤；embedder mock 抛异常时退回 BM25 且 `degraded=true` |
| `tests/test_agent_tools.py`（扩充） | `search_knowledge` 参数校验（额外字段被拒、`limit` 边界）；citations 结构完整；空库返回 `count=0` |
| `tests/test_agent_runtime.py`（扩充） | mock LLM 返回 `search_knowledge` tool_call → citations 进入 `tool_results`；未检索、空检索、缺失/越界引用和错误工具耗尽轮次时强制降级；**回归断言：写意图优先级不被知识路由抢占** |
| `tests/test_knowledge_api.py`（新） | 新 search 端点鉴权、参数校验、分数非恒定 |
| `tests/fixtures/knowledge_sample.jsonl`（新） | 约 10 条小语料 fixture |
| `tests/test_ingest_knowledge.py`（新） | 60 个唯一白名单 URL；HTML 范围过滤；句子/单词边界切片；数字保护与修复；中文完整性；robots crawl-delay |

CI 配置不变，`ingest_knowledge.py` 永不进 CI。

## 13. 验收标准

- [ ] `LICENSES.md` 经人工复核，每个保留来源确认为公共领域或允许再分发
- [x] `corpus.jsonl` 提交进仓库，文档数 60、chunk 数 429
- [x] 全新 clone 执行 `seed_knowledge.py` 后，知识问答可用
- [x] 未配置 LLM 与 embedding 端点时，规则模式仍能回答「低血糖怎么办」并给出来源链接
- [x] Agent 模式下回复带 `[1][2]` 角标，`tool_results` 中 citations 的 `source_url` 可点开原文
- [x] 全量 429 条 chunk 自动校验数字、阈值与百分比一致，并抽查中文完整性
- [x] `python -m pytest -q` 全绿，且不产生任何网络请求
- [x] `npm run build` 通过
- [x] `docs/api.md`、`docs/architecture.md`、`docs/agent-design.md`、`docs/agent-behavior-spec.md`（I24 勾选）、`README.md` 同步更新

当前仓库提交 60 篇、429 chunks 的完整双语语料：NIDDK 38 篇/344 chunks，MedlinePlus 22 篇/85 chunks。`corpus.meta.json` 状态为 `complete_unreviewed`，自动质量门禁已完成，但 `license_reviewed=false` 与 `LICENSES.md` 的“人工复核：待完成”必须保持真实，不将自动核对冒充维护者许可签字。

## 14. 风险

| 风险 | 缓解 |
|---|---|
| 翻译改写篡改数字或阈值 | `text_en` 同行保留；数字表达先保护再恢复；429 条全量自动一致性校验；中文完整性门禁拒绝残留英文句子 |
| 源站许可与预期不符 | 许可随抓取落盘 + 交付前人工复核；存疑来源移出白名单重跑 |
| bigram 分词召回不足 | 已加入小型确定性同义词扩展和标题加权；继续以离线查询集评估，不引入运行时分词模型 |
| 模型该检索时不检索 | system prompt 硬规则 + fallback 关键词路由兜底 |
| 知识路由破坏既有写入行为 | 路由置于写/统计/查询分支之后，并加回归断言 |
| 源站改版导致 URL 失效 | 语料已提交，运行时不依赖源站；重跑时脚本报告失效 URL |
| 范围膨胀 | `KnowledgeView.vue` 与 Alembic 明确排除，见 §15 |

## 15. 待办（本次明确不做）

1. **引入 Alembic**。当前靠 `create_all` 加 seed 脚本内的 `ALTER TABLE` 补列，可用但不是长久之计。下一次涉及 schema 变更时应一并引入。
2. **`KnowledgeView.vue` 接入真实语料**。该页目前是 477 行纯 mock，本特性落地后它会成为与真语料矛盾的展示面，应在后续单独处理——接 `/api/v1/knowledge` 真实数据，或直接下线该路由。
3. **清理 `backend/app/ml/llm_service.py` 中的 ChromaDB 遗留代码**。本特性落地后，该文件里的 `diabetes_knowledge` 向量检索实验彻底失去存在理由。

## 16. 涉及文件

新增：

```
backend/scripts/ingest_knowledge.py
backend/scripts/sources.py
backend/scripts/seed_knowledge.py
backend/app/services/knowledge_retrieval.py
backend/tests/test_knowledge_retrieval.py
backend/tests/test_knowledge_api.py
backend/tests/fixtures/knowledge_sample.jsonl
data/knowledge/corpus.jsonl
data/knowledge/corpus.meta.json
data/knowledge/LICENSES.md
```

修改：

```
backend/app/db/models.py              KnowledgeBase 加列；新增 KnowledgeChunk
backend/app/agent/tools.py            第 7 个工具
backend/app/agent/prompts.py          两条系统规则
backend/app/agent/runtime.py          fallback 知识路由
backend/app/api/endpoints/knowledge.py  重写 search
backend/app/core/config.py            EMBEDDING_* 配置
backend/tests/test_agent_tools.py     扩充
backend/tests/test_agent_runtime.py   扩充
frontend/src/api/agent.ts             Citation 类型
frontend/src/views/AssistantView.vue  来源引用卡
.env.example                          EMBEDDING_*
docs/api.md docs/architecture.md docs/agent-design.md
docs/agent-behavior-spec.md docs/agent-intelligence-plan.md README.md
```

## 17. 修订记录

| 日期 | 变更 |
|---|---|
| 2026-07-28 | 初版：数据源与许可策略、双语语料管道、BM25+可选向量混合检索、search_knowledge 工具、前端来源引用 |
| 2026-07-28 | 第一阶段实现：核心 RAG/Agent/REST/前端/测试落地；提交启动语料，保留完整语料与许可复核门禁 |
| 2026-07-28 | 完整语料：排除 CDC syndication；提交 NIDDK/MedlinePlus 60 篇、429 chunks；加入 robots、正文范围、翻译完整性和防部分覆盖门禁 |
