# LangChain 在本项目 RAG 中的适用性 Spike

> 日期：2026-07-28  
> 实验分支：`spike/langchain-rag`  
> 对接分支：`feat/rag-knowledge`  
> 基线：两条分支当前都指向 `407e820`（RAG 设计规格提交）  
> 范围：离线代码 spike；没有修改现有 Agent 主路径，也没有把 LangChain 加入默认生产依赖。

## 结论

LangChain 可以在本项目中使用，但应当是**窄范围、可选的适配层**：只考虑 `langchain-core`、`langchain-openai` 和 `langchain-text-splitters`，用于 LCEL 组合、OpenAI-compatible 模型适配和文本切分实验。

不建议引入顶层 `langchain` 包，也不建议用 LangChain Agent/LangGraph、`langchain-classic` 或 `langchain-community` 的 BM25 替换项目已有或已设计的核心能力。以下组件继续由项目自己拥有：

- `HealthAgent` 的工具循环、登录用户绑定、审计与轮次控制；
- 中文 bigram + BM25、可选向量召回和 RRF 融合；
- 写操作确认门禁；
- LLM 不可用时的规则 fallback；
- `Citation`、`retrieval`、`degraded` 等对外业务契约。

换言之，LangChain 在这里适合作为“胶水”，不适合作为业务运行时的所有者。

## LangChain v1 的官方现状

### 1. v1 已按职责拆包

LangChain v1 将顶层 `langchain` 收窄到 Agent 等高层入口；基础抽象、模型提供商集成和文本切分分别由独立发行包承载：

| 职责 | v1 包 | 本项目判断 |
|---|---|---|
| Runnable、Prompt、Document、Tool、输出解析等基础抽象 | [`langchain-core`](https://pypi.org/project/langchain-core/) | 可选采用 |
| OpenAI / OpenAI-compatible 模型适配 | [`langchain-openai`](https://pypi.org/project/langchain-openai/) | 可选采用 |
| 通用文本切分器 | [`langchain-text-splitters`](https://pypi.org/project/langchain-text-splitters/) | 仅作切分实验或非领域文本切分 |
| 高层 Agent API | [`langchain`](https://pypi.org/project/langchain/) | 不采用 |
| 旧版 chains、retrievers 等 | [`langchain-classic`](https://pypi.org/project/langchain-classic/) | 不采用 |
| 大量第三方/社区集成 | [`langchain-community`](https://pypi.org/project/langchain-community/) | 当前不采用 |

官方的 [LangChain v1 发布说明](https://docs.langchain.com/oss/python/releases/langchain-v1) 和 [v1 迁移指南](https://docs.langchain.com/oss/python/migrate/langchain-v1) 都体现了这一边界。各包的官方源码也分别位于 [`libs/core`](https://github.com/langchain-ai/langchain/tree/master/libs/core)、[`libs/partners/openai`](https://github.com/langchain-ai/langchain/tree/master/libs/partners/openai) 和 [`libs/text-splitters`](https://github.com/langchain-ai/langchain/tree/master/libs/text-splitters)。

### 2. 顶层 `langchain` 的 Agent 建在 LangGraph 上

官方 [LangChain 概览](https://docs.langchain.com/oss/python/langchain/overview) 明确说明 LangChain Agent 构建在 LangGraph 之上；顶层包的 [`pyproject.toml`](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/pyproject.toml) 也直接声明 LangGraph 依赖。因此，采用顶层 `langchain` 的 Agent API，实际上也接受了 LangGraph 的运行时和依赖边界。

这不是本项目当前所需。本项目的 `backend/app/agent/runtime.py` 已经实现一个更贴合业务的受控工具循环；为了少量 RAG 组合能力引入顶层包和 LangGraph，收益不足以覆盖迁移、调试和行为回归成本。实验依赖因此刻意没有安装 `langchain`。

### 3. 旧 chains/retrievers 已迁到 `langchain-classic`

v1 迁移指南说明，旧式 chains、retrievers、hub 等遗留功能已移到 `langchain-classic`，对应发行包见 [PyPI](https://pypi.org/project/langchain-classic/)。这意味着旧教程中常见的 `RetrievalQA`、legacy chain 或 retriever 组合不再是 v1 顶层包的主路径。

本项目不应为了复用旧 RAG 教程而引入 `langchain-classic`。当前 RAG 设计已经有清晰的 `KnowledgeRetriever.search()` 接口和项目自有响应契约，直接用 LCEL 的 `Runnable` 组合即可，不需要 legacy chain。

### 4. `langchain-community` 的 BM25 不适合直接替换项目实现

官方源码中的 [`BM25Retriever`](https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/retrievers/bm25.py) 本质上是对 [`rank-bm25`](https://pypi.org/project/rank-bm25/) 中 `BM25Okapi` 的轻量包装：从一组文本/Document 建立内存索引，默认预处理函数是 Python 的 `text.split()`，查询时调用 `get_top_n()` 返回文档。

对本项目而言有四个直接局限：

1. 中文正文通常没有空格，默认 `split()` 不能替代设计中的字符 bigram + ASCII 词切分。
2. 包装器没有本项目要求的数据库语料缓存、基于 `content_hash` 的失效判断和 `source_key` 过滤契约。
3. 它只解决单路 BM25 排序，不提供“BM25 + 可选向量”的 RRF 融合，也不提供 `retrieval` / `degraded` 降级语义。
4. 为一个很薄的包装层需要额外引入 `langchain-community` 和 `rank-bm25`；而本项目语料规模仅数百个 chunk，设计中的纯 Python BM25 足够小且更可控。

因此，不采用 community BM25；BM25、RRF、过滤、引用和降级继续由 `feat/rag-knowledge` 的 `KnowledgeRetriever` 实现。

## 与本项目自研 Agent/RAG 的对照

| 能力 | 项目现有/主 RAG 设计 | LangChain 能提供什么 | 决策 |
|---|---|---|---|
| Agent 运行时 | `HealthAgent` 自研 tool loop，绑定当前用户和请求级 DB session，限制轮次并保留工具轨迹 | LangChain Agent/LangGraph 可提供通用编排 | 保留自研，不替换 |
| 写入安全 | `add_glucose_record` 未确认只返回 preview，确认后才写库 | 通用 Tool 本身不了解本项目确认协议 | 保留确认门禁 |
| 断网/模型失败 | 写入、统计、最近血糖已有确定性规则 fallback；RAG 设计要求知识问答也可纯 BM25 降级 | LangChain 模型调用失败仍需业务侧处理 | 保留项目 fallback |
| RAG 检索 | 中文 bigram、BM25、可选 query embedding、RRF、来源过滤、引用与降级标记 | 可包装任意检索函数，但不自动满足这些契约 | 保留 `KnowledgeRetriever.search()` |
| LLM 接入 | `OpenAICompatibleClient` 已直接调用 `/chat/completions` | `ChatOpenAI` 可减少模型消息适配代码 | 可选使用，必须继续读取项目配置 |
| RAG 组合 | 项目需要“确定性检索 → 引用上下文 → 模型 → 结构化响应” | LCEL `Runnable`、Prompt 和 Parser 很适合表达该流程 | 可选使用 |
| 工具描述/参数校验 | `HealthToolRegistry` 使用严格 Pydantic 参数并禁止传入 `user_id` | `StructuredTool` 可在边界复用同类校验 | 仅作适配，不取代 registry |
| 文本切分 | 主设计要求按标题优先、英中 chunk 对齐并保持数字/单位 | `RecursiveCharacterTextSplitter` 提供通用递归切分 | 只作辅助；不能替代领域入库规则 |

## 已完成的 spike

实现文件如下：

- `backend/requirements-langchain.txt`：在默认 `requirements.txt` 之上，仅增加 `langchain-core`、`langchain-openai`、`langchain-text-splitters`；不增加顶层 `langchain`、LangGraph、classic、community 或 `rank-bm25`。
- `backend/experiments/langchain_rag/adapter.py`：定义实验用请求、响应和引用模型；包装未来的 `KnowledgeRetriever.search()`；构建 `StructuredTool`、LCEL RAG chain、OpenAI-compatible `ChatOpenAI` 和递归切分器。
- `backend/experiments/langchain_rag/__init__.py`：集中导出实验接口。
- `backend/experiments/langchain_rag/README.md`：说明安装、专项测试和与主 RAG 的对接方式。
- `backend/tests/experiments/test_langchain_rag_adapter.py`：6 项离线专项测试。

实验 chain 保留项目字段 `answer`、`citations`、`count`、`retrieval` 和 `degraded`。检索仍先由项目代码确定性执行，LangChain 只负责把检索结果放入受约束 Prompt、调用模型并解析回复。Prompt 明确把引用正文视为不可信数据，禁止执行其中的指令；空检索时要求明确回答知识库无结果。

当前安装验证使用的版本为 `langchain-core 1.5.1`、`langchain-openai 1.4.1`、`langchain-text-splitters 1.1.2`。`langchain`、LangGraph、`langchain-classic`、`langchain-community` 和 `rank-bm25` 均未安装。

## 测试结果

2026-07-28 在 `backend` 目录执行：

```powershell
python -m pytest tests/experiments/test_langchain_rag_adapter.py -q
# 6 passed

python -m pytest -q
# 40 passed
```

6 项专项测试覆盖：

1. `StructuredTool` 保留项目检索结果和引用契约；
2. 严格拒绝未知参数，尤其不能透传 `user_id`；
3. LCEL chain 返回模型答案及原始 citations，并把引用安全约束写入 Prompt；
4. 空检索结果进入明确的“未检索到资料”上下文；
5. `RecursiveCharacterTextSplitter` 保留来源 metadata 和连续 `chunk_index`；
6. `ChatOpenAI` 正确复用项目的 OpenAI-compatible base URL、鉴权、模型、温度和非流式 `/chat/completions` 请求。

后端全量 40 项测试同时通过，说明当前可选实验没有破坏既有 Agent、API、工具和健康服务行为。

## 采用边界

只有同时满足以下条件，才把实验适配器带入 RAG 特性分支：

- 实际 `KnowledgeRetriever.search()` 与实验的严格输入/输出契约对齐；
- citations、`source_key` 过滤、RRF 排名、`retrieval` 和 `degraded` 不因适配层丢失；
- 默认安装与默认运行路径仍不依赖 LangChain；
- 专项测试和合并后的后端全量测试都通过；
- 对比直接调用后，LCEL/`ChatOpenAI` 的维护收益足以覆盖 LangSmith、OpenAI SDK 等传递依赖和额外调试层。

即使采用，也只采用以下三包：

```text
langchain-core
langchain-openai
langchain-text-splitters
```

明确不替换：`HealthAgent`、项目 BM25/RRF、写确认门禁、规则 fallback、项目引用契约。

## 与 `feat/rag-knowledge` 的后续合并步骤

当前两条分支同基线，建议不要立即把整个 spike 混入正在开发的主 RAG，而是按下面顺序收敛：

1. 先在 `spike/langchain-rag` 把实验代码、测试和本文作为独立提交保存，保持它可单独撤销。
2. 等 `feat/rag-knowledge` 完成数据库模型、语料管道、`KnowledgeRetriever`、BM25/RRF、`search_knowledge`、引用 UI 和 fallback 测试。
3. 将 spike rebase 到最新的 `feat/rag-knowledge`，以真实 `KnowledgeRetriever.search()` 替换测试中的模拟 seam，校准 `Citation`/`RetrievalResult` 字段；发生冲突时以 RAG 特性分支的业务契约为准。
4. 增加一项真实集成测试：绑定测试 DB 的 `KnowledgeRetriever.search()` → LangChain adapter → 保留原始 citations、RRF 顺序和 degraded 状态。同时回归“写意图优先于知识 fallback”。
5. 重新执行 6 项专项测试、RAG 分支新增测试和后端全量测试；另外比较直接调用与 LCEL 路径的依赖体积、启动时间、单次请求延迟和错误栈可读性。
6. 若采用，只把“可选依赖 + 小型 adapter + 集成测试”整理成一个独立提交，cherry-pick/合并到 `feat/rag-knowledge`；不要改写 `backend/app/agent/runtime.py` 的核心循环，也不要用 `StructuredTool` 替换 `HealthToolRegistry`。
7. 若收益不明显，只合并本文研究结论，保留自研 RAG 实现并删除/归档实验分支，不给生产环境增加依赖。

## 官方资料

- [LangChain v1 发布说明](https://docs.langchain.com/oss/python/releases/langchain-v1)
- [LangChain v1 迁移指南](https://docs.langchain.com/oss/python/migrate/langchain-v1)
- [LangChain Agent 概览（基于 LangGraph）](https://docs.langchain.com/oss/python/langchain/overview)
- [`langchain` PyPI](https://pypi.org/project/langchain/) / [顶层包 `pyproject.toml`](https://github.com/langchain-ai/langchain/blob/master/libs/langchain/pyproject.toml)
- [`langchain-core` PyPI](https://pypi.org/project/langchain-core/) / [源码](https://github.com/langchain-ai/langchain/tree/master/libs/core)
- [`langchain-openai` PyPI](https://pypi.org/project/langchain-openai/) / [源码](https://github.com/langchain-ai/langchain/tree/master/libs/partners/openai)
- [`langchain-text-splitters` PyPI](https://pypi.org/project/langchain-text-splitters/) / [源码](https://github.com/langchain-ai/langchain/tree/master/libs/text-splitters)
- [`langchain-classic` PyPI](https://pypi.org/project/langchain-classic/)
- [`langchain-community` PyPI](https://pypi.org/project/langchain-community/) / [`BM25Retriever` 源码](https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/retrievers/bm25.py)
- [`rank-bm25` PyPI](https://pypi.org/project/rank-bm25/)
