# Course Parameters - Planner Agent 輸入規範

本文檔說明使用 `@planner` agent 時的參數規範。

---

## 必需參數

### 1. Topic（課程主題）

**描述**：本週課程的核心主題

**格式**：字串

**範例**：
- `"Binary Tree"`
- `"Dynamic Programming"`
- `"Markov Decision Process"`
- `"Neural Networks"`

---

### 2. Week Number（週次編號）

**描述**：課程所屬的週次（用於決定輸出目錄）

**格式**：整數（1, 2, 3...）

**輸出影響**：
- 週次 `N` 的內容將輸出到 `./week{N}/plan/` 目錄
- Blackboard 中的配置鍵為 `week_{XX}_config`（如 `week_02_config`）

**範例**：
- `1` → 輸出到 `./week01/plan/`
- `2` → 輸出到 `./week02/plan/`

---

### 3. Hours（時長）

**描述**：課程預計時長（小時）

**格式**：正數（浮點數）

**常見時長**：
- 短課程：0.25 小時（15 分鐘）
- 標準課程：1-4 小時
- 深度課程：6-8 小時

**範例**：
- `0.25` → 15 分鐘課程
- `1.0` → 1 小時課程
- `4.0` → 4 小時課程

---

### 4. Audience（目標對象）

**描述**：課程的預期聽眾背景

**格式**：字串

**標準選項**：

| 選項 | 說明 | 內容調整 |
|------|------|----------|
| `beginner` | 初學者，無或少技術背景 | 增加直覺解釋與範例 |
| `intermediate` | 有一定經驗的學生 | 聚焦於最佳實踐、實作細節與邊緣情況 |
| `advanced` | 專家或有豐富經驗 | 深入探討優化、進階技術、系統設計 |
| `decision-maker` | 管理者或決策者 | 強調權衡分析、應用場景與效益評估 |

**範例**：
- `"beginner"` → 入門級課程
- `"intermediate"` → 中級課程
- `"CS 3rd Year"` → 特定對象（大三學生）

---

### 5. Direction（教學方向）

**描述**：課程的教學取向，決定內容呈現方式

**格式**：字串

**標準選項**：

| 選項 | 說明 | 內容特點 |
|------|------|----------|
| `theory` | 理論導向 | 數學定義、證明要點、公式推導、學術嚴謹性 |
| `implementation` | 實作導向 | 代碼範例、框架使用、工具應用、最佳實踐 |
| `application` | 應用導向 | 實際案例、場景應用、權衡分析、決策建議 |

**範例**：
- `"theory"` → 數學證明、演算法分析
- `"implementation"` → 程式碼實作、框架使用
- `"application"` → 應用場景、案例研究

---

### 6. Emphasis（強調重點）

**描述**：課程內容的側重點

**格式**：字串

**標準選項**：

| 選項 | 說明 | 內容調整 |
|------|------|----------|
| `depth` | 理論深度 | 數學嚴謹性、證明細節、深入分析 |
| `practice` | 實作體驗 | 手把手教學、程式碼練習、實作技巧 |
| `cases` | 案例分析 | 真實案例、對比分析、最佳實踐 |

**範例**：
- `"depth"` → 理論深度與嚴謹性
- `"practice"` → 實作練習與技巧
- `"cases"` → 案例研究與分析

---

## 參數關係

### 時長與章節規劃

| 時長 | 建議章節數量 | 時間分配 |
|------|--------------|----------|
| 0.25 小時（15 分鐘） | 1-2 個章節 | 每節 7-10 分鐘 + 緩衝 |
| 1 小時 | 2-3 個章節 | 每節 15-20 分鐘 |
| 4 小時 | 4-5 個章節 | 每節 45-50 分鐘 |
| 6 小時以上 | 6-8 個章節 | 每節 40-50 分鐘 |

### Audience 與 Direction 的搭配

| Audience \ Direction | Theory | Implementation | Application |
|------------------|--------|----------------|-------------|
| Beginner | 高直覺解釋，避免過度數學化 | 每步驟詳細說明，代碼註解完整 | 日常案例，易懂的應用場景 |
| Intermediate | 數學與直覺並重 | 最佳實踐與邊緣情況 | 常見問題與解決方案 |
| Advanced | 高度數學嚴謹性 | 優化技巧、系統設計 | 架構權衡、設計決策 |
| Decision-maker | 概念理解，避免過度技術細節 | 原則與最佳實踐 | ROI 分析、效益評估 |

### Direction 與 Emphasis 的搭配

| Direction \ Emphasis | Depth | Practice | Cases |
|------------------|-------|----------|--------|
| Theory | 證明細節、推導過程 | 定理應用、驗證方法 | 理論發展史、應用案例 |
| Implementation | API 設計原則 | 實作技巧、常見陷阱 | 最佳實踐、反模式 |
| Application | 決策模型、權衡框架 | 部署策略、監控方法 | 成功案例、失敗教訓 |

---

## 使用範例

### 範例 1：15 分鐘基礎課程

```
Topic: Binary Tree
Week: 2
Hours: 0.25
Audience: CS 3rd Year
Direction: implementation
Emphasis: practical
```

**預期輸出**：
- 1-2 個章節（每節 7-10 分鐘）
- 重點在基本概念與術語定義
- 實作導向的直覺解釋

---

### 範例 2：4 小時深度課程

```
Topic: Dynamic Programming
Week: 1
Hours: 4.0
Audience: intermediate
Direction: theory
Emphasis: depth
```

**預期輸出**：
- 4-5 個章節（每節 45-50 分鐘）
- 數學定義、證明要點、公式推導
- 適合有一定經驗的學生

---

### 範例 3：2 小時應用導向課程

```
Topic: Neural Networks
Week: 3
Hours: 2.0
Audience: decision-maker
Direction: application
Emphasis: cases
```

**預期輸出**：
- 2-3 個章節（每節 30-40 分鐘）
- 真實應用案例、ROI 分析
- 決策建議與權衡分析

---

## 完整執行命令範例

### 方法 1：使用參數說明文件

```bash
@planner
- 主題: Binary Tree
- 時長: 15 分鐘
- 週別: week 02
- 對象： 資工系大三
- 注意： 只要一個 session
```

### 方法 2：直接呼叫 init_week_blackboard 工具

```bash
python3 .opencode/tools/init_week_blackboard.py \
    --week 2 \
    --topic "Binary Tree" \
    --duration 0.25 \
    --audience "CS 3rd Year" \
    --direction implementation \
    --emphasis practical
```

---

## 輸出位置規則

### 週次目錄結構

所有 planner 生成的檔案將放置在對應的週次目錄下：

```
week{XX}/
└── plan/
    ├── research_summary.md
    ├── section_01_research.md
    ├── section_02_research.md
    ├── section_03_research.md
    ├── references.md
    └── narrative_map.md
```

### Blackboard 配置

Planner 會將週次配置存儲�到 Blackboard：

```python
# 配置鍵格式
week_{XX}_config

# 範例
week_02_config = {
    "topic": "Binary Tree",
    "duration_hours": 0.25,
    "audience": "CS 3rd Year",
    "direction": "implementation",
    "emphasis": "practical",
    "created_at": "2026-01-12T15:13:37.356302"
}
```

---

## 注意事項

1. **目錄約束**：
   - 所有輸出檔案必須在 `./week{XX}/plan/` 下
   - 禁止在 `.opencode/` 下創建任何週次特定檔案

2. **時長合理性**：
   - 15 分鐘課程：1-2 個章節
   - 1 小時課程：2-3 個章節
   - 4 小時課程：4-5 個章節

3. **參數一致性**：
   - Audience 和 Direction 應該搭配合理（見上表）
   - Emphasis 應該與 Direction 呼應（見上表）

4. **Blackboard 初始化**：
   - 必須使用 `.opencode/tools/init_week_blackboard.py` 工具
   - 不要手動寫初始化代碼

---

## 相關文件

- `.opencode/agent/planner.md` - Planner agent 完整規範
- `.opencode/tools/init_week_blackboard.py` - Blackboard 初始化工具
- `.opencode/tools/blackboard.py` - Blackboard 管理工具
