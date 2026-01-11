# ScholarStream

自動生成課程簡報的工具，透過 AI Agent 協作將課程大綱轉化為結構化的簡報文件。

## 功能

- 讀取課程大綱並自動生成教學計劃
- 為每一週的主題生成詳細的研究內容
- 將課程內容轉換為簡報格式
- 支援多週課程的批次處理

## 前置條件

### 必需的 OpenCode Agents

在使用本專案之前，需要確保以下 Agent 可用：

1. **planner** - 分析課程需求並生成敘事地圖與章節規劃
   - 用於生成每週課程的研究內容和教學結構

2. **slide-generator** - 基於規劃文件生成簡報文件
   - 使用 Marp 將規劃轉換為簡報

### 安裝 Agent

如果上述 Agent 不可用，請按照以下步驟安裝：

```bash
# 檢查可用 agents
ls ~/.config/opencode/agent/

# 或者
ls .opencode/agent/
```

## 使用方法

### 1. 準備課程大綱

確保 `course_outlines.md` 文件存在並包含課程內容。文件應包含：

- 課程基本資訊（名稱、時數、目標受眾）
- 每週詳細的教學計劃
- 學習目標、內容大綱、程式範例、實作練習

參考範例：`course_outlines.md`

### 2. 生成課程內容

在 OpenCode Console 中輸入 `driver_prompt.md` 的內容：

```
- 讀取 course_outlines.md
- 依次為每一週的主題，呼叫 planner agent 產生課程研究內容，然後呼叫 slide-generator 將每個session 輸出成獨立的 slides
```

### 3. 輸出結構

執行完成後，會在專案目錄下生成以下結構：

```
ScholarStream/
├── course_outlines.md          # 課程大綱
├── driver_prompt.md             # 驅動提示
├── README.md                    # 本文件
└── weekXX/                     # 每週課程目錄
    ├── plan/                   # 教學計劃
    │   ├── session_01.md       # 每個session的規劃
    │   ├── session_02.md
    │   └── ...
    └── slides/                 # 簡報
        ├── session_01.md       # 簡報源碼（Marp格式）
        ├── session_02.md
        └── ...
```

### 4. 匯出簡報

生成的簡報使用 Marp 格式，可以透過以下方式匯出：

#### 使用 Marp CLI

```bash
# 安裝 Marp CLI
npm install -g @marp-team/marp-cli

# 匯出單個簡報為 PDF
marp week01/slides/session_01.md --pdf

# 批次匯出
for file in week01/slides/*.md; do
  marp "$file" --pdf
done
```

#### 使用 VS Code

1. 安裝 [Marp for VS Code](https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode) 外掛
2. 開啟簡報文件
3. 點擊右上角的預覽按鈕

## 文件說明

| 文件 | 說明 |
|------|------|
| `course_outlines.md` | 課程大綱文件，包含4週的完整教學計劃 |
| `driver_prompt.md` | 驅動提示 |
| `how-to-design-agent.md` | 如何設計和配置 OpenCode Agent 的指南 |
| `weekXX/plan/` | 每週課程的教學計劃 |
| `weekXX/slides/` | 每週課程的簡報文件 |

## 課程內容

本專案包含一個完整的 **UNIX 系統程式設計** 課程範例：

- **Week 1**: UNIX 基礎與進程概念
  - UNIX/Linux 系統簡介
  - 進程（Process）基礎
  - 進程建立：fork()
  - exec() 函數家族

- **Week 2**: 進程控制與進程間通訊（IPC）
  - 進程終止與退出狀態
  - 管道（Pipe）通訊
  - 命名管道（FIFO）
  - 信號（Signal）處理

- **Week 3**: 執行緒與同步機制
  - 執行緒（Thread）基礎
  - 執行緒的建立與終止
  - 互斥鎖（Mutex）
  - 條件變數（Condition Variable）

- **Week 4**: 進階主題與實戰專案
  - 檔案 I/O 系統呼叫
  - Socket 程式設計入門
  - 實戰專案：簡單的 Shell

## 注意事項

1. **Agent 可用性**：確保 planner 和 slide-generator agents 已正確配置
2. **模型選擇**：根據內容複雜度選擇合適的 AI 模型
3. **手動審核**：生成的內容應經過人工審核和調整
4. **Marp 語法**：簡報使用 Marp 語法，確保格式正確

## 擴充使用

### 新增新課程

1. 建立新的 `course_outlines.md` 文件
2. 按照現有格式編寫課程大綱
3. 執行 `driver_prompt.md` 的內容

### 自訂簡報樣式

在 Marp 簡報中可以自訂主題：

```markdown
---
marp: true
theme: gaia
paginate: true
style: |
  /* 自訂樣式 */
  section {
    font-size: 24px;
  }
---
```

## 相關資源

- [Marp 官方文件](https://marp.app/)
- [OpenCode.ai 文件](https://opencode.ai/)
- [課程大綱設計指南](./how-to-design-agent.md)

