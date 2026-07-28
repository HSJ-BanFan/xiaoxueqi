# RAG 完整语料来源、许可与抓取入口核对

> 核对日期：2026-07-28
>
> 范围：NIDDK、MedlinePlus、CDC 的官方许可说明、robots、官方数据入口，以及仓库完整语料的来源选择
>
> 方法：只使用机构官网、官网 robots/sitemap、官方 API 和 CDC 官方 Archive/Search 服务
>
> 说明：本文是工程侧来源审查，不构成法律意见，也不能代替维护者最终人工许可签字。

## 结论

完整语料可以随仓库提交，但本次应只使用 **NIDDK + MedlinePlus**：最终 [`backend/scripts/sources.py`](../../backend/scripts/sources.py) 的活跃白名单为 NIDDK 38 篇、MedlinePlus 22 篇，共 60 个唯一文档；生成产物为 429 个 chunks。

CDC 暂不进入可提交语料，原因不是“CDC 正文一定受版权保护”，而是当前可用入口不能同时满足可抓取、可改写和可随 Git 再分发三个条件：

- CDC 的一般政策称多数站内信息属于美国公共领域，但要求署名、免责声明、不得改变实质内容，并提醒美国政府作品在其他司法辖区仍可能受保护。[CDC《Use of Agency Materials》](https://www.cdc.gov/other/agencymaterials.html)；本环境可通过 [CDC 官方搜索索引](https://search.cdc.gov/srch/internet/browse2?q=%22Use%20of%20Agency%20Materials%22&wt=json&rows=10&fl=id,title,url,description,dc_date)核对完整条文。
- CDC Media Library/API 虽然可访问正文，但其官方 Usage Guidelines 明确写有 “Redistribution of CDC syndicated content is not allowed”，同时要求不得更改内容和措辞。因此 API 返回物不适合打包进 Git，更不适合走“LLM 中文改写”流程。[CDC Media Library Usage Guidelines](https://tools.cdc.gov/medialibrary/index.aspx#/usageguidelines/info)
- CDC Archive 对原 13 条候选 URL 的精确查询均为 0；它有旧版相关页面，但不是当前页面的无损替代，也存在过时风险。[CDC Archive](https://archive.cdc.gov/)

因此，本轮完整语料的稳妥交付边界是：提交 60 篇 NIDDK/MedlinePlus 双语语料，继续保持 `license_reviewed=false`，由维护者抽查正文范围、署名和全球再分发风险后再签字。不得把本次自动核对伪装成“人工许可复核完成”。

## 来源决策表

| 来源 | 可纳入范围 | 必须排除 | 抓取入口与节流 | 本轮决定 |
|---|---|---|---|---|
| NIDDK | 普通健康信息正文；中文可做忠实编辑/翻译 | Logo、图片/图形、第三方授权材料、联合出版且权利归其他方的材料 | 官方页面或 sitemap 白名单；robots 要求 10 秒 crawl delay | 纳入 38 篇 |
| MedlinePlus | health topic page 的 summary | A.D.A.M. 百科、ASHP 药品专论、未明确属于 NLM 公共领域的图片/照片/插图、RSS 内容 | 当前 health topic 页面；也有官方 Web Service/XML | 纳入 22 篇，仅取 `#topic-summary` |
| CDC | 一般政策下多数 CDC 自有正文可能属于美国公共领域 | 第三方/承包商材料、图片、Logo，以及任何受单独条款约束的内容 | `www.cdc.gov` 在本环境 403；Media API 有再分发禁令；Archive 不覆盖当前候选页 | 本轮排除 |

## NIDDK

### 许可边界

[NIDDK Copyright](https://www.niddk.nih.gov/copyright) 的原文边界很清楚：

- “The majority of information on this site is copyright free and can be freely downloaded and reproduced.”
- 未改动转载应注明 NIDDK 为来源。
- 与私营公司或其他组织共同资助的文档，其他参与方可能保留权利。
- NIDDK Logo 未经明确审批不得使用；部分图形由第三方授权，使用受限。
- 编辑内容时必须移除 NIDDK/NIH Logo，不得暗示机构背书，也不得把内容用于推荐具体医疗建议、治疗或转诊。

对本项目的含义是：只抽取健康信息正文文字；不摄取图片、图注所依赖的视觉材料、Logo 或带单独版权声明的块；每个文档保留原始 URL 和 NIDDK 署名。中文内容应是忠实翻译/改写，不能改变数字、阈值、单位和医学含义，也不能制造 NIDDK 为本产品背书的印象。

### robots 与官方入口

[NIDDK robots.txt](https://www.niddk.nih.gov/robots.txt) 当前声明：

```text
User-agent: *
Crawl-delay: 10
Disallow: /system
Disallow: /_internal
```

并公开 [内容 sitemap](https://www.niddk.nih.gov/sitemap-sc.xml)。该 sitemap 在核对时包含足够的 `/health-information/diabetes...` URL，可在自我管理范围内组成 38 篇白名单，无需递归爬站。

完整摄取必须按 robots 的 10 秒间隔执行，不能只按设计文档中的 1 秒最低间隔。仓库 Fetcher 应读取 `RobotFileParser.crawl_delay()`，并使用 `max(本地最低间隔, robots crawl-delay)`。

另外，旧地址 `.../overview/diet-eating-physical-activity` 当前会重定向到 [`.../overview/healthy-living-with-diabetes`](https://www.niddk.nih.gov/health-information/diabetes/overview/healthy-living-with-diabetes)，两者不能同时计为两个文档。当前白名单已使用独立的 [`Gestational Diabetes: After Your Baby is Born`](https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/gestational/after-your-baby-is-born) 替换重复项。

## MedlinePlus

### 许可边界

[Linking to and Using Content from MedlinePlus](https://medlineplus.gov/about/using/usingcontent/) 明确区分公共领域与授权内容：

- 美国联邦政府创作的非版权内容可自由复制、再分发和链接。
- 明确列入公共领域的内容包括 “Summaries on health topic pages”。
- 官方要求注明来源，可使用 “Source: MedlinePlus, National Library of Medicine.”
- A.D.A.M. Medical Encyclopedia、ASHP drug monographs，以及大部分图片、插图和照片受版权保护；不得把这些受保护内容摄取并重新品牌化到健康 IT 系统。
- MedlinePlus RSS feeds 仅供个人使用，不能作为本站语料入口。

仓库当前只提取 health topic 页的 `#topic-summary`，与许可页点名允许再分发的范围一致。2026-07-28 实测最终 22 个白名单 URL 均返回 HTTP 200，且都存在 `id="topic-summary"`。

### robots 与官方数据入口

[MedlinePlus robots.txt](https://medlineplus.gov/robots.txt) 公开 sitemap，并未禁止当前 22 个 health topic 页面；它同时明确禁止通用爬虫访问 `/xml/` 等路径。因此当前“显式页面白名单 + 只取 summary”方案可继续使用。

MedlinePlus 还提供两个第一方数据入口：

- [MedlinePlus Web Service](https://medlineplus.gov/about/developers/webservices/)：免费、无需注册或许可，返回 health topic summary 等 XML 数据，官方限速为每 IP 每分钟不超过 85 个请求，并要求标明数据来自 MedlinePlus.gov。
- [MedlinePlus XML Files](https://medlineplus.gov/xml.html)：官方称可下载使用，包含全部英文/西班牙文 health topic 的 full summary 等字段。

本项目共有 22 条 MedlinePlus 显式 URL，继续抓取允许的页面 summary 最简单。若以后改用 bulk XML，应做成独立、显式的官方文件下载流程，并先人工协调“XML 下载页欢迎使用”与 robots 对 `/xml/` 的限制；不能让现有通用爬虫遍历该目录。

## CDC

### 一般内容政策

[CDC《Use of Agency Materials》](https://www.cdc.gov/other/agencymaterials.html) 当前页面在本环境被 Akamai 返回 403，但页面内容可由 [CDC 官方 Search 服务](https://search.cdc.gov/srch/internet/browse2?q=%22Use%20of%20Agency%20Materials%22&wt=json&rows=10&fl=id,title,url,description,dc_date)核对。政策要点是：

- 多数 CDC/ATSDR 网站信息不受版权保护，属于美国公共领域，可以自由使用或复制。
- 例外包括由承包商、受资助者或第三方制作/授权的资源和图片；州、地方政府作品也不自动属于美国联邦政府作品。
- 美国政府作品在美国之外仍可能受当地版权法保护。
- 使用 CDC 公共领域内容时必须署名、显著声明不构成 CDC/HHS/美国政府背书、不得改变实质内容，并说明该材料可在机构网站免费获得。
- CDC/ATSDR/HHS Logo 和标志未经书面许可不得使用。

这意味着，即使以后重新启用 CDC，也不能只写一个笼统的 `public domain`。逐文档 metadata 应准确记录“美国联邦政府作品/美国法下公共领域，存在第三方和境外司法辖区例外”，并保留署名、免责声明与免费原文链接。现有“LLM 中文改写”是否满足“不得改变实质内容”，必须由维护者人工抽查，不能自动推定。

### 当前站点抓取

2026-07-28 在本环境实测：CDC 许可页、候选正文页和 `https://www.cdc.gov/robots.txt` 均由 Akamai 返回 403。因此仓库的 robots 强制门禁会正确阻止直接抓取；不能为了完成数量而绕过 robots 或伪造许可声明。

403 是当前网络环境的访问事实，不代表 CDC 永久禁止访问，但它足以说明本轮离线构建不能依赖 `www.cdc.gov` 主站。

### Media Library / Content Syndication API

CDC 的第一方 API `https://tools.cdc.gov/api/v2/resources/media` 当前可访问。媒体记录会返回 `sourceUrl`、`contentUrl`、`syndicateUrl`、更新时间和官方 attribution，例如：

- [Type 1 Diabetes，media 419813](https://tools.cdc.gov/api/v2/resources/media/419813.json)
- [Type 2 Diabetes，media 335189](https://tools.cdc.gov/api/v2/resources/media/335189.json)
- [Diabetes and Smoking，media 398746](https://tools.cdc.gov/api/v2/resources/media/398746.json)
- [Diabetes and Mental Health，media 471001](https://tools.cdc.gov/api/v2/resources/media/471001.json)

对移除前的 13 条 CDC 候选 URL 使用精确 `?url=<sourceUrl>` 查询时，仅以上 4 条命中，其余 9 条返回 0。因此它本身也不是原候选白名单的完整替代。

更关键的是，[Media Library Usage Guidelines](https://tools.cdc.gov/medialibrary/index.aspx#/usageguidelines/info) 要求：

- syndicated material 的内容和措辞不得改变或歪曲；
- CDC 原链接、attribution 和回链必须完整保留；
- “Redistribution of CDC syndicated content is not allowed.”
- 未经单独许可不得使用 CDC Logo。

把 API 正文和中文改写一起提交到 Git 是再分发，也会改变措辞，和这组 syndication 条款直接冲突。该 API 适合按官方 embed/syndication 方式在线展示，不适合作为本项目版本化语料的构建输入。

[tools.cdc.gov robots.txt](https://tools.cdc.gov/robots.txt) 没有禁止 `/api/v2/resources/`，但 robots 允许访问不等于获得再分发许可；最终仍以 Usage Guidelines 为准。

### CDC Archive 与 Search

[CDC Archive](https://archive.cdc.gov/) 是官方归档入口，[Archive robots.txt](https://archive.cdc.gov/robots.txt) 当前允许所有路径，并公开 sitemap。归档应用通过官方搜索服务查找 `original_url` 和 `archive_url`。

对移除前 13 条当前候选 URL 做 `original_url` 精确查询时全部为 0。Archive 能找到一些旧版 diabetes 页面，但标题、路径和复核日期与当前候选页不同，不能静默替换成“当前官方正文”。若以后明确采用归档材料，必须把 `source_url`、`retrieved_at`、归档日期和“历史资料”状态展示给用户，并重新做医学时效性审查。

CDC 官方 Search 服务可以返回搜索索引和高亮片段，本次用它核对了被 403 阻断的许可页；但它是搜索后端，不是 CDC 发布的内容再分发接口，没有稳定的语料摄取契约，不能据此绕过主站 robots、Media Library 条款或逐页许可审查。

## 完整语料交付门禁

本轮按以下门禁提交 60 篇、429 chunks 的完整语料：

1. `source_key` 只包含 `niddk`、`medlineplus`；CDC 不进入 `corpus.jsonl`。
2. NIDDK 每次请求遵守 robots 的 10 秒 crawl delay；MedlinePlus 继续使用可识别 User-Agent 和显式白名单。
3. NIDDK 只取正文文字；MedlinePlus 只取 `#topic-summary`。任何图片、Logo、第三方卡片、药品专论、百科正文和 RSS 内容均不得进入 corpus。
4. 每个文档保留官方标题、原始 URL、抓取时间、精确许可说明、来源署名和内容 hash；中文片段保留对应英文原文。
5. 数字、百分比、单位、阈值和时间范围必须通过自动一致性校验；本次对 429 个 chunk 全量执行，并额外抽查中文完整性。
6. `LICENSES.md` 应记录上述范围与例外，但 `license_reviewed` 必须继续为 `false`，直到维护者完成人工页面抽查并确认全球再分发风险。

## 官方资料

- NIDDK：[Copyright](https://www.niddk.nih.gov/copyright)；[robots.txt](https://www.niddk.nih.gov/robots.txt)；[sitemap-sc.xml](https://www.niddk.nih.gov/sitemap-sc.xml)；[Get Free Web Content](https://www.niddk.nih.gov/health-information/community-health-outreach/free-web-content)
- MedlinePlus：[Using Content](https://medlineplus.gov/about/using/usingcontent/)；[robots.txt](https://medlineplus.gov/robots.txt)；[Web Service](https://medlineplus.gov/about/developers/webservices/)；[XML Files](https://medlineplus.gov/xml.html)
- CDC：[Use of Agency Materials](https://www.cdc.gov/other/agencymaterials.html)；[官方 Search 核对结果](https://search.cdc.gov/srch/internet/browse2?q=%22Use%20of%20Agency%20Materials%22&wt=json&rows=10&fl=id,title,url,description,dc_date)；[Media Library](https://tools.cdc.gov/medialibrary/index.aspx#/usageguidelines/info)；[Media API](https://tools.cdc.gov/api/v2/resources/media?max=1)；[Archive](https://archive.cdc.gov/)
