# RAG 离线检索效果评测

- 评测集：共 50 题（dev 25 / test 25）
- 本次评测范围：`test` split，共 25 题
- 语料规模：60 documents / 429 chunks
- 截断位置：top-3
- 运行约束：内存 SQLite、禁用 embedding、无网络、无真实 LLM
- 评测集 SHA-256：`3648b3cff0b3727d23d01fe8c82874215b1760ad7f6c55a5d4c7406724bbecae`
- 语料 SHA-256：`debd5a54fce29ada2392664baaa5a63e963ccd76e8b0cd4ac509bdbd8bcc7081`
- 旧基线提交：`9a37edc`

## 评测协议

问题由维护者根据健康助理的非个人知识意图人工策划，每题显式绑定语料文档 UUID 与官方 URL。
dev split 仅用于分析和通用检索调优；test split 在实现与输入哈希冻结后首次运行，不根据 test 失败清单继续调参。

## 指标定义

- Macro Recall@3：逐题计算 gold 文档被 top-3 覆盖的比例，再做宏平均。
- Citation Hit@3：至少一个文档 ID 与来源 URL 均属于 gold 的引用进入 top-3 的问题占比。
- Citation Precision@3：逐题计算返回引用中，文档 ID 与来源 URL 同时属于 gold 的比例，再做宏平均。

## 结果

| 系统 | 题数 | Macro Recall@3 | Citation Hit@3 | Citation Precision@3 | 未完整召回题数 |
|---|---:|---:|---:|---:|---:|
| `legacy_sql_like` | 25 | 0.0% | 0.0% | 0.0% | 25 |
| `bigram_bm25_rrf` | 25 | 84.0% | 92.0% | 41.3% | 6 |

## 逐题失败清单

### `legacy_sql_like`

- `test-severe-hypoglycemia-01`：严重低血糖昏迷时，家人应该怎么急救？
  - gold：f7b53be2-4f32-5c98-82ae-4a9894260b18, dc385fba-1f5d-5db1-ad7e-5c1bc2bf3038
  - top-3：无结果
  - Recall@3：0.0%
- `test-exercise-hypoglycemia-02`：运动前后怎样防止血糖降得太低？
  - gold：f7b53be2-4f32-5c98-82ae-4a9894260b18, 04e0a445-f91a-5d61-a7c9-8482176b269c
  - top-3：无结果
  - Recall@3：0.0%
- `test-high-low-glucose-03`：血糖过低和过高分别会有哪些症状？
  - gold：dc385fba-1f5d-5db1-ad7e-5c1bc2bf3038, 158a7cca-cc75-5bb5-8093-97cef1c3791c
  - top-3：无结果
  - Recall@3：0.0%
- `test-glucose-vs-a1c-04`：日常血糖检查和 A1C 检查有什么区别？
  - gold：72979808-7469-5139-a271-c7f943f23489, 7202ba70-ece2-536a-8e0f-4d851023c056
  - top-3：无结果
  - Recall@3：0.0%
- `test-type1-autoimmune-05`：1 型糖尿病是不是免疫系统破坏了产生胰岛素的细胞？
  - gold：6f3e85b9-9e1d-5fe6-9d92-95e3daa0d0a7, db15824e-4381-53da-89d8-4d1080aeba73
  - top-3：无结果
  - Recall@3：0.0%
- `test-insulin-resistance-06`：什么是胰岛素抵抗，它和糖尿病前期有什么关系？
  - gold：88631dc1-d7f9-5dfe-997d-07ece38fc8e6
  - top-3：无结果
  - Recall@3：0.0%
- `test-children-diabetes-07`：儿童和青少年也会得 2 型糖尿病吗？
  - gold：2a51efd5-32a5-58ec-86bc-ea9df9f0dc4a
  - top-3：无结果
  - Recall@3：0.0%
- `test-mody-08`：MODY 是什么，和常见的 1 型、2 型糖尿病有什么不同？
  - gold：105f86f8-2cdc-50b4-bee4-86c5aeb16d3d
  - top-3：无结果
  - Recall@3：0.0%
- `test-metabolic-syndrome-09`：代谢综合征包括哪些危险因素？
  - gold：7dcf1e0a-c575-5ceb-9cf0-443f3609b905
  - top-3：无结果
  - Recall@3：0.0%
- `test-financial-help-10`：负担不起糖尿病药物和用品费用时可以去哪里求助？
  - gold：af4fbc63-43a6-5fbb-8eb3-33d80b25ac36
  - top-3：无结果
  - Recall@3：0.0%
- `test-foot-wounds-11`：糖尿病为什么容易造成脚部伤口和感染？
  - gold：ff3eea95-617e-5d85-9739-a71adcdb2864, 783bffc2-9311-573e-9edd-21c3b72d7d1a
  - top-3：无结果
  - Recall@3：0.0%
- `test-eye-exam-12`：糖尿病患者为什么要定期做散瞳眼底检查？
  - gold：8f9a0462-7501-5c05-8394-1f830d2a0eb4
  - top-3：无结果
  - Recall@3：0.0%
- `test-kidney-early-13`：糖尿病肾病早期会有明显症状吗？
  - gold：cca73494-d5b8-5457-ae78-b740eae97e54, 6f2aa0d4-529f-5cbb-9cb4-64daf6290539
  - top-3：无结果
  - Recall@3：0.0%
- `test-autonomic-neuropathy-14`：糖尿病自主神经病变会影响哪些器官和功能？
  - gold：9a79cba0-0c69-5eb2-83b9-42f3cbfe333c
  - top-3：无结果
  - Recall@3：0.0%
- `test-focal-neuropathy-15`：糖尿病会不会突然造成某一根神经疼痛或无力？
  - gold：8351974d-6d45-5dc2-9a97-444594ee26c6
  - top-3：无结果
  - Recall@3：0.0%
- `test-proximal-neuropathy-16`：大腿、臀部疼痛和无力可能是哪种糖尿病神经病变？
  - gold：e8e28e04-0c2b-5c8d-b4c6-298925c2e37e
  - top-3：无结果
  - Recall@3：0.0%
- `test-neuropathy-types-17`：糖尿病神经病变主要分为哪些类型？
  - gold：2a49cdf7-cda6-5b1c-a3e1-f028cdebbc6b, 05c5e1f4-76f3-59b1-b045-6561a3b95626
  - top-3：无结果
  - Recall@3：0.0%
- `test-gum-disease-18`：糖尿病和牙龈疾病、口腔感染有什么关系？
  - gold：0479b961-b5af-5bc7-b29e-5ab45b8319d0
  - top-3：无结果
  - Recall@3：0.0%
- `test-sex-bladder-19`：糖尿病会影响性功能或膀胱排尿吗？
  - gold：a7070340-48ef-51e2-b57b-5f25865ee2e4
  - top-3：无结果
  - Recall@3：0.0%
- `test-preexisting-pregnancy-20`：本来就有糖尿病的人还能安全怀孕吗？
  - gold：e3c417c4-b110-51ef-b23c-41cb91f71a6a, 83ad1405-b4bb-5404-b220-727c63e889a4
  - top-3：无结果
  - Recall@3：0.0%
- `test-gestational-definition-21`：妊娠糖尿病是什么，会给孕妇和宝宝带来哪些风险？
  - gold：e2ceba95-4659-5eac-b6e0-578d2fae3ba9, 83ad1405-b4bb-5404-b220-727c63e889a4
  - top-3：无结果
  - Recall@3：0.0%
- `test-gestational-prevention-22`：怀孕前和孕期能做什么来降低妊娠糖尿病风险？
  - gold：1b0a4345-7da1-5acf-92e2-c4019509f27f
  - top-3：无结果
  - Recall@3：0.0%
- `test-diet-portions-23`：糖尿病饮食中怎样安排碳水化合物和食物份量？
  - gold：5728f1c4-db12-57f6-9726-557aa304d194, 90197080-425f-55ea-b34d-e7164502c986
  - top-3：无结果
  - Recall@3：0.0%
- `test-insulin-requirement-24`：得了糖尿病就一定需要注射胰岛素吗？
  - gold：3a0feb7f-3233-5f58-baeb-93675067ef0c, bf73bb6f-12d7-51a5-a6bc-43eab1ece019
  - top-3：无结果
  - Recall@3：0.0%
- `test-long-term-damage-25`：长期高血糖可能损伤哪些器官，怎样减少这些问题？
  - gold：dcf311eb-e567-5bc8-89c4-5b32027ee4ab, d45a3612-67dc-55fe-b596-8e4ba71a82e1
  - top-3：无结果
  - Recall@3：0.0%

### `bigram_bm25_rrf`

- `test-high-low-glucose-03`：血糖过低和过高分别会有哪些症状？
  - gold：dc385fba-1f5d-5db1-ad7e-5c1bc2bf3038, 158a7cca-cc75-5bb5-8093-97cef1c3791c
  - top-3：血糖 (72979808-7469-5139-a271-c7f943f23489), 低血糖 (dc385fba-1f5d-5db1-ad7e-5c1bc2bf3038), 低血糖（低血糖） (f7b53be2-4f32-5c98-82ae-4a9894260b18)
  - Recall@3：50.0%
- `test-type1-autoimmune-05`：1 型糖尿病是不是免疫系统破坏了产生胰岛素的细胞？
  - gold：6f3e85b9-9e1d-5fe6-9d92-95e3daa0d0a7, db15824e-4381-53da-89d8-4d1080aeba73
  - top-3：类型 1 糖尿病 (6f3e85b9-9e1d-5fe6-9d92-95e3daa0d0a7), 糖尿病 (f39a5964-6442-566f-86bc-0e4a90bc8cab), 糖尿病的症状和原因 (4ee5ebbd-7f89-5008-8208-958f9042f63f)
  - Recall@3：50.0%
- `test-mody-08`：MODY 是什么，和常见的 1 型、2 型糖尿病有什么不同？
  - gold：105f86f8-2cdc-50b4-bee4-86c5aeb16d3d
  - top-3：糖尿病 (f39a5964-6442-566f-86bc-0e4a90bc8cab), 什么是糖尿病？ (f1b2289c-e55c-5c5f-a0d1-588b40d7a43c), 类型 2 糖尿病 (d79f241a-9431-5564-bdf5-ec8ba4ab20ab)
  - Recall@3：0.0%
- `test-gestational-definition-21`：妊娠糖尿病是什么，会给孕妇和宝宝带来哪些风险？
  - gold：e2ceba95-4659-5eac-b6e0-578d2fae3ba9, 83ad1405-b4bb-5404-b220-727c63e889a4
  - top-3：妊娠糖尿病的定义和事实 (e2ceba95-4659-5eac-b6e0-578d2fae3ba9), 糖尿病测试与诊断 (1e386c80-c3c0-50a8-a47f-befdff07eb42), 糖尿病 (f39a5964-6442-566f-86bc-0e4a90bc8cab)
  - Recall@3：50.0%
- `test-insulin-requirement-24`：得了糖尿病就一定需要注射胰岛素吗？
  - gold：3a0feb7f-3233-5f58-baeb-93675067ef0c, bf73bb6f-12d7-51a5-a6bc-43eab1ece019
  - top-3：胰岛素、药物和其他糖尿病治疗 (3a0feb7f-3233-5f58-baeb-93675067ef0c), 糖尿病 (f39a5964-6442-566f-86bc-0e4a90bc8cab), 管理和治疗妊娠糖尿病 (cb74d199-4414-55d5-b4fd-5d311ba5dcca)
  - Recall@3：50.0%
- `test-long-term-damage-25`：长期高血糖可能损伤哪些器官，怎样减少这些问题？
  - gold：dcf311eb-e567-5bc8-89c4-5b32027ee4ab, d45a3612-67dc-55fe-b596-8e4ba71a82e1
  - top-3：高血糖 (158a7cca-cc75-5bb5-8093-97cef1c3791c), 血糖 (72979808-7469-5139-a271-c7f943f23489), 如果您患有糖尿病，可以怀孕 (e3c417c4-b110-51ef-b23c-41cb91f71a6a)
  - Recall@3：0.0%

## 口径说明

`legacy_sql_like` 复现 RAG 改造前的整句 SQL `ILIKE '%query%'` 搜索；`bigram_bm25_rrf` 使用当前生产检索器。当前提交语料的 embedding 字段为空，因此本报告只证明 SQL LIKE → 中文 bigram BM25/RRF 的变化，不声称向量召回带来的提升。
