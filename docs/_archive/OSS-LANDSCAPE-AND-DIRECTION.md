> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-enterprise.md;此為歷史版本。

# OSS 生態與方向 — 企業知識／內部文件 RAG

> **範圍。** phantom-enterprise 在開源**企業知識／內部文件 RAG／內部問答代理**
> 生態中的定位，以及對一個**單人、整合 phantom-mesh、隱私優先**專案的
> 建議方向。關於*本*儲存庫的狀態主張，一律以 [`/ROADMAP.md`](../ROADMAP.md)
> 為準（狀態的唯一真實來源）；本文件談的是**方向**，而非狀態。
>
> 每一項外部主張都標註於 **2026-06**，並附上來源連結。星數與
> 授權條款會隨時間漂移 — 各項數字皆為概略快照，凡本次無法對照
> 標準儲存庫確認者，皆以 `[unverified]` 標示。

---

## 1. phantom-enterprise 的現況（有所本）

擷取自截至 2026-06-19 的 `ROADMAP.md` 與 `master` 合併歷史，而非願景：

- **真實、經密封式測試（hermetic-tested）、已納入 CI：** VPN 感知路由（`tailscale status --json`
  → tailnet IP、以 `*.ts.net` 為錨點的 MagicDNS 比對）、地端 Git 連接器
  （Gitea `/api/v1` + GitLab `/api/v4`，真實 HTTP+驗證）、Confluence/Jira 連接器
  （透過 Atlassian REST 的 `search_pages`/`get_page`/`list_issues`/`add_comment`，
  Basic-auth，8 個密封式測試，**現場驗證延後**）、Apple-Silicon-HA
  可注入健康探針，以及 **`code_qa` 私有 `ask` CLI**。
- **設計上的介面接縫：** `ldap_sso/` — 真實的 RFC 4515/4514 filter+DN
  跳脫處理並附注入合約測試；`LdapAuth`/`SamlAuth`/`OidcAuth` 在真實 IdP 出現前
  會拋出 `NotImplementedError`。
- **0-LOC 佔位符：** `mes_connector/`、`erp_connector/`（受 NDA／客戶閘控）。

本儲存庫的 **RAG／內部問答**核心是 `code_qa` 套件：
`phantom-enterprise ask` 在**本機**讀取儲存庫（或透過地端
Gitea/GitLab 連接器），建構一個有所本的提示詞（`PROMPT_TEMPLATE`：「僅使用
所提供的檔案內容……並引用檔案路徑」），並透過一個**本機
`phantom exec` 代理**回答 — *位元組永不離開機器*。這就是整個
隱私論旨濃縮於一項工具：對私有原始碼進行檢索有所本、強制引用、全本機的
問答，並乘載於 phantom-mesh 代理基底之上。

**誠實的定調：** 本儲存庫**並非**通用企業搜尋產品，
也不應試圖變成那樣。它是一個**輕薄、隱私優先的連接器套件 +
本機有所本問答黏合層**，將 phantom-mesh 延伸至地端企業
系統。下方的生態地圖是為了*防守此利基*而繪製，而非追逐
RAG 平台領先者。

---

## 2. 生態地圖

### 2a. 完整企業搜尋／內部問答平台（「全包」層級）

| 專案 | URL | 星數 `[~2026-06]` | 語言 | 授權 | 成熟度 | 對單人、整合 mesh、隱私優先專案的契合度／落差 |
|---|---|---|---|---|---|---|
| **Onyx**（前身 Danswer） | github.com/onyx-dot-app/onyx | ~30k | Python | **MIT**（CE） | 生產級；代理式 RAG、40–50+ 連接器、MCP、Deep Research | **最接近的直接對照。** 已具備 Confluence/Jira/Slack/GitHub/GitLab 連接器 + RAG + 存取控制，可自架。**落差：** 沉重的多服務堆疊（Postgres + Vespa/向量 + worker + 網頁 UI）；它是一個*要部署與運維的產品*，而非可嵌入 mesh 的函式庫。對一個輕薄的單人套件而言高度不對 — 但它是連接器形狀與有所本回答 UX 的**參考標竿**。 |
| **Dify** | github.com/langgenius/dify | ~146k | TypeScript | **Dify OSS License**（Apache-2.0 + 多租戶／品牌標識限制） | 非常成熟；代理 + RAG + 工作流程 studio + LLMOps | 龐大、精緻，但屬於**平台/BaaS**，其授權帶有商業條件、非純 OSS。對自架 Apache-2.0 單人利基而言過度且授權不匹配。僅作為工作流程編排 UX 的參考。 |
| **RAGFlow** | github.com/infiniflow/ragflow | ~83k | Python | **Apache-2.0** | 成熟；深度文件理解 RAG、可追溯引用 | 同類最佳的*文件解析／切塊與可解釋引用*。**落差：** 它是完整 RAG 引擎（DeepDoc 解析器、infinity/elastic 儲存、網頁 UI）— 同樣是要運行的服務，而非黏合層。若 `code_qa` 日後需要更豐富的文件擷取，是引用／有所本模型的有力**候選參考**。 |
| **Quivr** | github.com/QuivrHQ/quivr | ~39k | Python | **Apache-2.0**（核心）`[unverified exact]` | 成熟的「第二大腦」RAG 框架 | 隱私友善、可自架、任意 LLM／任意向量庫。比起企業地端連接器，更偏向**個人知識**定調。可作為本機優先理念的參考；非連接器來源。 |
| **Glean** | glean.com（專有） | n/a（封閉） | — | **專有、SaaS** | 市場領導者，企業搜尋 | phantom-enterprise 用以*界定自身*的商業基準線：每位使用者每月 $25–50+、僅雲端、不可自架、無原始碼。**我們整套差異化** = 自架 + 資料永不外流 + 單人可掌控。不可採用；它是反襯。 |

### 2b. RAG 構件函式庫（「自行組合」層級）

| 專案 | URL | 星數 `[~2026-06]` | 語言 | 授權 | 成熟度 | 契合度／落差 |
|---|---|---|---|---|---|---|
| **LangChain / LangGraph** | github.com/langchain-ai/langchain | ~119k `[unverified vs canonical repo]` | Python | **MIT** | 成熟、龐雜 | 可提供檢索／代理管線，但相依面龐大且變動頻繁。phantom-mesh **已**提供代理基底（`phantom exec`），引入 LangChain 只會重複造輪。**參考，勿採用。** |
| **LlamaIndex** | github.com/run-llama/llama_index | ~50k（標準儲存庫，2026-06） | Python | **MIT** | 成熟；300+ 資料連接器／載入器、檢索能力強 | 若 `code_qa` 超出「把檔案塞進單一提示詞」的階段，這是最*符合用途*的構件：階層式切塊、子問題拆解、300+ 載入器。**值得包裝（wrap）的候選**，作為一個*本機*索引／檢索層 — 有所選擇地藏在我們自己的介面後，而非由框架接管。 |
| **Cognita**（TrueFoundry） | github.com/truefoundry/cognita | ~4.4k | Python | **Apache-2.0** | 模組化；至 2026 仍有活躍開發（Neo4j/Chroma、向量量化） | 帶 UI 可比較設定的模組化 RAG。心智佔有率較小；與 TrueFoundry 的部署敘事綁定。可作為*模組化元件邊界*的參考；對 mesh 原生單人套件的採用價值低。 |

來源：Onyx [repo](https://github.com/onyx-dot-app/onyx) · [Onyx insights](https://onyx.app/insights/glean-alternatives)；
Dify [repo](https://github.com/langgenius/dify)；
RAGFlow [repo](https://github.com/infiniflow/ragflow)；
Quivr [org](https://github.com/quivrhq) · [overview](https://tossom.com/products/quivr)；
Cognita [repo](https://github.com/truefoundry/cognita)；
LangChain/LlamaIndex [comparison](https://www.morphllm.com/comparisons/langchain-vs-llamaindex)；
Glean pricing [analysis](https://www.gosearch.ai/blog/glean-pricing-explained/) · [alternatives](https://dust.tt/blog/glean-alternatives-ai-enterprise-search)。

---

## 3. 建議方向（adopt／wrap／reference／build）

指導原則：**領先者是用來*運行*的產品；phantom-enterprise 是用來
*嵌入*我已擁有之 mesh 的黏合層。** 不要重造一個平台。

| 裁決 | 對象 | 理由 |
|---|---|---|
| **BUILD（保留）** | 輕薄連接器套件（`vpn_aware_routing`、`on_prem_gitlab`、`confluence_jira`、`ldap_sso` 接縫、`apple_silicon_ha`）+ `code_qa` 本機有所本 `ask`。 | 這*就是*利基：隱私優先、mesh 原生、單人可掌控、無平台需運維。§2 中沒有任何專案佔據「乘載於 phantom-mesh 之上、地端-台廠-形狀的輕薄套件」。 |
| **REFERENCE** | **Onyx** 連接器合約 + 有所本回答／引用 UX；**RAGFlow** 可解釋引用模型。 | 偷取其*形狀*（連接器介面、「引用你的來源」回答格式），而不繼承其堆疊。我們的 `PROMPT_TEMPLATE` 已映照此點 — 持續對齊。 |
| **WRAP（僅在真實需求逼迫時）** | 當「把檔案串接成單一提示詞」不再可擴展（大型儲存庫／多文件語料）時，將 **LlamaIndex** 作為一個*本機*檢索／索引層藏在我們自己的介面後。 | 從天真的 context-stuffing 往上走、最小且可信的一步；MIT；可本機運行；300+ 載入器可重用我們連接器的目標。包裝一個輕薄子集 — 絕不讓它變成框架。 |
| **ADOPT** | *（無整體採用）* | 不應將任何專案採用為脊柱。phantom-mesh 的 `phantom exec` 已是代理／LLM 基底；採用 Onyx/Dify/RAGFlow 會取代 mesh，而非延伸它 — 那會破壞整套論旨。 |

### 為何不「直接部署 Onyx」？
Onyx（MIT，~30k★）已能對 Confluence/Jira/GitLab 進行內部問答。
這誘惑很真實。但採用它意味著：(1) 運行其多服務堆疊
（違背「單人可掌控、跑在我的 Mac／mesh 上」）、(2) 放棄
phantom-mesh 代理基底與跨裝置調度，而那*正是產品本身*、以及
(3) 繼承一條我無法掌控的連接器路線圖。**Onyx 是「好」長什麼樣子的參考、
也是證明利基存在的反襯** — 它無法以 `phantom exec` 黏合層的方式
在*個人 mesh 內部*自架。建議
**參考，永不採用**。

---

## 4. 分階段路徑（需求閘控、保全利基）

依「便宜高價值先行、護城河先行、外部相依最後」排序 — 映照
單人多機開發模型。任何階段在其觸發條件出現前皆不啟動。

- **Phase 0 — 強化黏合層（現在，零外部相依）。** 讓 `code_qa` 保持誠實：
  在回答中強制引用、當儲存庫溢出單一提示詞視窗時加入 token／大小預算 +
  截斷註記、記錄純本機資料路徑。
  *觸發：恆常啟用；最便宜的護城河強化。*
- **Phase 1 — 現場驗證已屬真實之物。** 在首次取得雇主／客戶存取權時，
  針對*真實*的企業 Atlassian/GitLab 操練 Confluence/Jira 與
  GitLab 連接器。*觸發：有真實實例可用（ROADMAP）。*
- **Phase 2 — 檢索升級，僅在痛了之後。** 當單一提示詞塞入法
  在真實儲存庫規模上失效時，**將一個輕薄的 LlamaIndex 本機索引藏在**
  `code_qa.context` 之後 — 在本機切塊 + 檢索 top-k，仍餵給 `phantom exec`、
  仍引用。以實測失敗為閘，而非臆測。
  *觸發：一個會溢出提示詞的真實語料。*
- **Phase 3 — IdP + 地端驗證啟用。** 依既有啟用規格，針對真實目錄／IdP
  實作 `LdapAuth`/`SamlAuth`/`OidcAuth`。
  *觸發：真實 AD／IdP（ROADMAP）。*
- **Phase 4 — 受 NDA 閘控的連接器（MES/ERP）。** 僅在 NDA／客戶範圍內。
  *觸發：鴻海／南亞科／鼎新 存取（ROADMAP）。*

---

## 5. 誠實的過度建造警告

- **切勿變成「另一個 Onyx/Dify」。** 一旦本儲存庫長出網頁 UI、
  背景 worker 機群、向量資料庫服務與連接器市集，它就
  已輸給擁有 30k–146k★ 與全職團隊的專案。利基是*我所擁有之 mesh 上的輕薄
  黏合層* — 刻意放棄廣度。
- **切勿將 RAG 框架採用為脊柱。** phantom-mesh 的 `phantom exec`
  就是代理基底。以 LangChain/LlamaIndex 作為框架取代它，會把
  產品反轉成一個通用 RAG app，並丟棄跨裝置、隱私優先的差異化。
- **切勿在痛了之前建造臆測性檢索。** 天真的
  context-stuffing 在真實語料溢出它之前都是*正確的*。Embeddings／
  向量儲存／重排序是真實成本與真實維護；只在實測失敗時加入
  （Phase 2 觸發），絕不「因為真正的 RAG 都有」就加。
- **切勿在無真實目標時建造 MES/ERP/IdP 連接器。** 依 ROADMAP，
  這些是需求閘控的。對零實例建造臆測性連接器是典型的
  企業鷹架陷阱 — 永遠無法驗證、終將腐朽的程式碼。
- **停留在鷹架階段是可接受的結果。** 若無需求訊號到來，
  本儲存庫已證明 phantom-mesh 能乾淨地延伸至地端企業。
  切勿製造工作以裝得比需求所證成的更忙。

---

*方向文件。狀態權威為 [`/ROADMAP.md`](../ROADMAP.md)。作者：Mark
Lai（[@markl-a](https://github.com/markl-a)）。外部數字快照於 2026-06；
請將星數視為概略值。*
