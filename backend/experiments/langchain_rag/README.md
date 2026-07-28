# LangChain RAG spike

这个目录验证一个收敛的集成方式：项目继续拥有检索、权限、写入门禁和降级逻辑，LangChain 只作为可选的编排适配层。

## 验证内容

- 用 `RecursiveCharacterTextSplitter` 对参考文本做带元数据的试验切片。
- 把主 RAG 设计中的 `KnowledgeRetriever.search()` 包装成 LangChain `StructuredTool`。
- 用 LCEL 组合“确定性检索 → 引用上下文 → OpenAI-compatible 模型 → 结构化响应”。
- 检索结果和引用继续使用项目定义的契约，不引入 LangChain 向量库。

## 安装与测试

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-langchain.txt
python -m pytest tests/experiments/test_langchain_rag_adapter.py -q
```

建议使用独立虚拟环境，因为 `langchain-core` 仍会带入 LangSmith 等传递依赖。默认
`requirements.txt` 不包含这些包，因此未选择该方案时不会增加生产依赖。

## 与主 RAG 实现对接

主分支完成 `KnowledgeRetriever` 后，可以把绑定数据库会话的 `search` 方法直接传入：

```python
retriever = KnowledgeRetriever(db=db, embedder=embedder)
chain = build_rag_chain(retriever.search)
result = chain.invoke({"query": "低血糖怎么办", "limit": 3})
```

`result` 保留 `answer`、`citations`、`retrieval` 和 `degraded`，因此可以继续复用当前 Agent API 的工具轨迹和前端引用卡契约。

## 当前建议

不要用 LangChain Agent 替换 `backend/app/agent/runtime.py`。现有 runtime 的用户绑定、写确认、审计和规则 fallback 都是项目价值所在；若采用 LangChain，优先只采用这里演示的 RAG 组合与可选工具适配。
