# UNIX 系統程式設計課程大綱

## 課程資訊

- **課程名稱**: UNIX 系統程式設計
- **課程時數**: 4 週，每週 2 小時（共 8 小時）
- **目標受眾**: 資訊工程系大學二年級學生
- **先修知識**: C 程式語言、資料結構、作業系統基礎概念
- **教學語言**: 繁體中文
- **程式語言**: C 語言

## 課程目標

完成本課程後，學生將能夠：
1. 理解 UNIX/Linux 系統的核心概念與架構
2. 熟練使用命令列工具進行系統管理
3. 掌握進程（Process）的建立、控制與同步
4. 理解並應用進程間通訊（IPC）機制
5. 熟悉信號（Signal）處理機制
6. 了解執行緒（Thread）的基本概念與應用
7. 具備系統程式設計的實作能力

---

## Week 1: UNIX 基礎與進程概念

### 時間分配 (2 小時)

#### 1.1 UNIX/Linux 系統簡介 (30 分鐘)
- **學習目標**:
  - 了解 UNIX 系統的歷史與發展
  - 認識 Linux 作業系統
  - 理解使用者權限與檔案系統概念

- **內容大綱**:
  - UNIX 的歷史演變：從 Bell Labs 到現代 Linux
  - Linux 核心概念：核心（Kernel）、殼層（Shell）、使用者空間
  - 檔案系統架構：樹狀結構、路徑、權限（rwx）
  - 標準輸入/輸出/錯誤（stdin, stdout, stderr）

- **實作練習**:
  - 使用基本命令：`ls`, `cd`, `pwd`, `mkdir`, `rm`, `cat`
  - 檢視檔案權限與修改權限：`chmod`, `chown`

#### 1.2 進程（Process）基礎 (30 分鐘)
- **學習目標**:
  - 理解進程的定義與特性
  - 掌握進程識別符（PID）與父進程（PPID）
  - 學習進程狀態與轉換

- **內容大綱**:
  - 進程的定義：執行中的程式實例
  - 進程與程式的區別
  - 進程屬性：PID, PPID, UID, GID, 狀態
  - 進程生命週期：建立 → 執行 → 等待 → 終止
  - `ps`, `top`, `htop` 命令的使用

- **實作練習**:
  - 觀察系統進程：使用 `ps` 指令
  - 建立背景進程與前台進程
  - 監控進程狀態變化

#### 1.3 進程建立：fork() (30 分鐘)
- **學習目標**:
  - 理解 `fork()` 系統呼叫的工作原理
  - 掌握父進程與子進程的關係
  - 學習 `fork()` 的返回值處理

- **內容大綱**:
  - `fork()` 函數原型與返回值
  - Copy-on-Write 機制
  - 父進程與子進程的執行順序
  - `wait()` 與 `waitpid()`：等待子進程終止
  - 僵屍進程（Zombie Process）與孤兒進程（Orphan Process）

- **程式範例**:
  ```c
  #include <stdio.h>
  #include <unistd.h>
  #include <sys/wait.h>

  int main() {
      pid_t pid = fork();

      if (pid == 0) {
          // 子進程
          printf("子進程: PID=%d\n", getpid());
      } else if (pid > 0) {
          // 父進程
          printf("父進程: PID=%d, 子進程 PID=%d\n", getpid(), pid);
          wait(NULL);  // 等待子進程
      } else {
          // fork 失敗
          perror("fork 失敗");
      }
      return 0;
  }
  ```

- **實作練習**:
  - 實作簡單的 fork 程式
  - 觀察父子進程的執行順序
  - 實作多層 fork（fork tree）

#### 1.4 exec() 函數家族 (30 分鐘)
- **學習目標**:
  - 理解 `exec()` 系列函數的用途
  - 區分不同 `exec()` 函數的差異
  - 學習如何用新程式替換進程映像

- **內容大綱**:
  - `exec()` 的作用：替換進程映像
  - `exec` 函數家族：`execl`, `execv`, `execlp`, `execvp`, `execle`, `execve`
  - `l` 系列 vs `v` 系列：參數列表 vs 參數陣列
  - `p` 系列：從 PATH 環境變數搜尋
  - `fork()` + `exec()` 的典型使用模式

- **程式範例**:
  ```c
  #include <unistd.h>
  #include <sys/wait.h>

  int main() {
      pid_t pid = fork();

      if (pid == 0) {
          // 子進程執行 ls 指令
          execlp("ls", "ls", "-l", NULL);
          perror("exec 失敗");  // 只在 exec 失敗時執行
      } else if (pid > 0) {
          wait(NULL);
      }
      return 0;
  }
  ```

- **實作練習**:
  - 實作簡單的 Shell（執行使用者輸入的指令）
  - 觀察 exec 前後進程屬性的變化

### 週末作業
- 實作一個程式：建立 3 個子進程，每個子進程列印自己的 PID 並輸出 1 到 10 的數字
- 寫一篇 500 字的心得：說明 fork() 與 exec() 的應用場景

---

## Week 2: 進程控制與進程間通訊（IPC）

### 時間分配 (2 小時)

#### 2.1 進程終止與退出狀態 (20 分鐘)
- **學習目標**:
  - 理解進程正常與異常終止
  - 掌握退出狀態的處理
  - 學習 `exit()` 與 `_exit()` 的差異

- **內容大綱**:
  - 正常終止：`exit()`, `_exit()`, `return`
  - 異常終止：訊號（Signal）、abort()
  - 退出狀態碼（Exit Status）
  - `wait()` 與 `waitpid()` 的返回值
  - `WIFEXITED`, `WEXITSTATUS`, `WIFSIGNALED` 等宏的使用

- **程式範例**:
  ```c
  #include <stdio.h>
  #include <stdlib.h>
  #include <sys/wait.h>

  int main() {
      pid_t pid = fork();
      if (pid == 0) {
          exit(42);  // 子進程返回 42
      } else {
          int status;
          wait(&status);
          if (WIFEXITED(status)) {
              printf("子進程退出狀態: %d\n", WEXITSTATUS(status));
          }
      }
      return 0;
  }
  ```

#### 2.2 管道（Pipe）通訊 (40 分鐘)
- **學習目標**:
  - 理解管道的工作原理
  - 掌握匿名管道（Anonymous Pipe）的使用
  - 學習管道的讀寫特性

- **內容大綱**:
  - 管道的基本概念：單向、先進先出（FIFO）
  - `pipe()` 系統呼叫：建立管道
  - 父子進程通過管道通訊
  - 管道的讀寫特性：寫端關閉後讀端讀取 EOF
  - 命令列管道 `|` 的實現原理

- **程式範例**:
  ```c
  #include <stdio.h>
  #include <unistd.h>
  #include <string.h>

  int main() {
      int pipefd[2];
      char buf[100];

      pipe(pipefd);  // 建立管道

      if (fork() == 0) {
          close(pipefd[1]);  // 子進程關閉寫端
          read(pipefd[0], buf, sizeof(buf));
          printf("子進程收到: %s\n", buf);
          close(pipefd[0]);
      } else {
          close(pipefd[0]);  // 父進程關閉讀端
          write(pipefd[1], "Hello from parent", 17);
          close(pipefd[1]);
          wait(NULL);
      }
      return 0;
  }
  ```

- **實作練習**:
  - 實作父子進程雙向通訊（使用兩個管道）
  - 實作多進程管道鏈：P1 → P2 → P3

#### 2.3 命名管道（FIFO） (20 分鐘)
- **學習目標**:
  - 理解命名管道的用途
  - 掌握 `mkfifo()` 的使用
  - 區匿名管道與命名管道的應用場景

- **內容大綱**:
  - 命名管道：存在於檔案系統中
  - `mkfifo()` 系統呼叫
  - 無關聯進程間的通訊
  - 命名管道的讀寫特性

- **實作練習**:
  - 建立命名管道
  - 兩個獨立程式透過命名管道通訊

#### 2.4 信號（Signal）基礎 (20 分鐘)
- **學習目標**:
  - 理解信號的概念與用途
  - 認識常見信號類型
  - 學習 `kill()` 系統呼叫

- **內容大綱**:
  - 信號的定義：軟體中斷機制
  - 常見信號：`SIGINT` (Ctrl+C), `SIGKILL`, `SIGTERM`, `SIGSTOP`, `SIGCONT`
  - 信號的預設行為：終止、忽略、暫停、繼續
  - `kill()` 命令與系統呼叫
  - `kill -l` 列出所有信號

- **實作練習**:
  - 使用 `kill()` 命令終止進程
  - 發送不同信號並觀察進程行為

#### 2.5 信號處理 (20 分鐘)
- **學習目標**:
  - 掌握 `signal()` 與 `sigaction()` 的使用
  - 理解信號處理函數的編寫規則
  - 學習信號遮罩（Signal Masking）

- **內容大綱**:
  - `signal()` 函數：註冊信號處理函數
  - `sigaction()`：更安全的信號處理
  - 信號處理函數的限制：只能呼叫非同步安全函數
  - 重新啟動中斷的系統呼叫
  - `SIG_IGN`（忽略）與 `SIG_DFL`（預設行為）

- **程式範例**:
  ```c
  #include <stdio.h>
  #include <signal.h>
  #include <unistd.h>

  void handle_sigint(int sig) {
      printf("\n收到 SIGINT，但程式不會終止\n");
  }

  int main() {
      signal(SIGINT, handle_sigint);

      while (1) {
          printf("執行中... 按 Ctrl+C 測試\n");
          sleep(1);
      }
      return 0;
  }
  ```

- **實作練習**:
  - 實作 Ctrl+C 的友善退出（清理資源）
  - 實作定時器（使用 SIGALRM）

### 週末作業
- 實作一個程式：使用管道建立一個簡單的生產者-消費者模型
  - 生產者進程產生數字 1-20，寫入管道
  - 消費者進程讀取數字並計算總和
- 寫一篇心得：說明管道與信號的應用差異

---

## Week 3: 執行緒與同步機制

### 時間分配 (2 小時)

#### 3.1 執行緒（Thread）基礎 (30 分鐘)
- **學習目標**:
  - 理解執行緒的概念與特性
  - 區分進程與執行緒
  - 掌握執行緒的優缺點

- **內容大綱**:
  - 執行緒的定義：進程內的執行單元
  - 進程 vs 執行緒：
    - 進程：獨立的記憶體空間
    - 執行緒：共享記憶體空間
  - 多執行緒的優點：資源共享、輕量、快速切換
  - 多執行緒的挑戰：競爭條件（Race Condition）、死鎖（Deadlock）
  - Pthread 函式庫介紹

#### 3.2 執行緒的建立與終止 (30 分鐘)
- **學習目標**:
  - 掌握 `pthread_create()` 的使用
  - 學習執行緒終止與等待
  - 理解執行緒參數的傳遞

- **內容大綱**:
  - `pthread_create()`: 建立新執行緒
  - `pthread_exit()`: 終止執行緒
  - `pthread_join()`: 等待執行緒終止
  - `pthread_detach()`: 分離執行緒
  - 執行緒函數的參數傳遞（使用結構體）
  - 編譯時需要連結 Pthread 函式庫：`-lpthread`

- **程式範例**:
  ```c
  #include <stdio.h>
  #include <pthread.h>

  void* thread_func(void* arg) {
      int id = *(int*)arg;
      printf("執行緒 %d 開始\n", id);
      return NULL;
  }

  int main() {
      pthread_t tid1, tid2;
      int id1 = 1, id2 = 2;

      pthread_create(&tid1, NULL, thread_func, &id1);
      pthread_create(&tid2, NULL, thread_func, &id2);

      pthread_join(tid1, NULL);
      pthread_join(tid2, NULL);

      printf("主執行緒結束\n");
      return 0;
  }
  ```

- **實作練習**:
  - 建立 5 個執行緒，每個執行緒列印自己的 ID
  - 實作執行緒參數傳遞

#### 3.3 執行緒同步：互斥鎖（Mutex） (30 分鐘)
- **學習目標**:
  - 理解競爭條件問題
  - 掌握互斥鎖的使用
  - 學習避免死鎖

- **內容大綱**:
  - 競爭條件（Race Condition）的例子
  - 互斥鎖（Mutex）的概念：保證同一時間只有一個執行緒存取臨界區
  - `pthread_mutex_init()`: 初始化互斥鎖
  - `pthread_mutex_lock()`: 獲取鎖
  - `pthread_mutex_unlock()`: 釋放鎖
  - `pthread_mutex_destroy()`: 銷毀鎖
  - 死鎖的發生條件與預防

- **程式範例**:
  ```c
  #include <stdio.h>
  #include <pthread.h>

  int counter = 0;
  pthread_mutex_t mutex;

  void* increment(void* arg) {
      for (int i = 0; i < 100000; i++) {
          pthread_mutex_lock(&mutex);
          counter++;
          pthread_mutex_unlock(&mutex);
      }
      return NULL;
  }

  int main() {
      pthread_t tid1, tid2;
      pthread_mutex_init(&mutex, NULL);

      pthread_create(&tid1, NULL, increment, NULL);
      pthread_create(&tid2, NULL, increment, NULL);

      pthread_join(tid1, NULL);
      pthread_join(tid2, NULL);

      printf("Counter: %d\n", counter);  // 應該是 200000
      pthread_mutex_destroy(&mutex);
      return 0;
  }
  ```

- **實作練習**:
  - 實作一個不使用互斥鎖的程式，觀察競爭條件
  - 加入互斥鎖修正問題
  - 實作多個互斥鎖，注意死鎖預防

#### 3.4 執行緒同步：條件變數（Condition Variable） (30 分鐘)
- **學習目標**:
  - 理解條件變數的用途
  - 掌握 `pthread_cond_wait()` 與 `pthread_cond_signal()`
  - 學習生產者-消費者問題的解決

- **內容大綱**:
  - 條件變數的概念：等待特定條件滿足
  - `pthread_cond_init()`: 初始化條件變數
  - `pthread_cond_wait()`: 等待條件
  - `pthread_cond_signal()`: 喚醒一個等待的執行緒
  - `pthread_cond_broadcast()`: 喚醒所有等待的執行緒
  - 條件變數與互斥鎖的配合使用
  - 生產者-消費者問題的解決

- **程式範例**:
  ```c
  #include <stdio.h>
  #include <pthread.h>

  int buffer = 0;
  pthread_mutex_t mutex;
  pthread_cond_t cond;

  void* producer(void* arg) {
      pthread_mutex_lock(&mutex);
      buffer = 1;
      printf("生產者：生產完成\n");
      pthread_cond_signal(&cond);  // 喚醒消費者
      pthread_mutex_unlock(&mutex);
      return NULL;
  }

  void* consumer(void* arg) {
      pthread_mutex_lock(&mutex);
      while (buffer == 0) {
          pthread_cond_wait(&cond, &mutex);  // 等待生產
      }
      printf("消費者：消費完成\n");
      buffer = 0;
      pthread_mutex_unlock(&mutex);
      return NULL;
  }

  int main() {
      pthread_t tid1, tid2;
      pthread_mutex_init(&mutex, NULL);
      pthread_cond_init(&cond, NULL);

      pthread_create(&tid1, NULL, producer, NULL);
      pthread_create(&tid2, NULL, consumer, NULL);

      pthread_join(tid1, NULL);
      pthread_join(tid2, NULL);

      pthread_mutex_destroy(&mutex);
      pthread_cond_destroy(&cond);
      return 0;
  }
  ```

- **實作練習**:
  - 實作有界緩衝區（Bounded Buffer）的生產者-消費者
  - 實作多個生產者與多個消費者

### 週末作業
- 實作一個程式：使用多執行緒計算矩陣乘法
  - 主執行緒建立 N 個工作執行緒
  - 每個工作執行緒計算矩陣的一部分
  - 主執行緒等待所有執行緒完成並輸出結果
- 寫一篇心得：比較進程與執行緒的應用場景

---

## Week 4: 進階主題與實戰專案

### 時間分配 (2 小時)

#### 4.1 檔案 I/O 系統呼叫 (30 分鐘)
- **學習目標**:
  - 理解低階檔案 I/O 與標準 I/O 函式庫的差異
  - 掌握基本檔案 I/O 系統呼叫
  - 學習檔案描述符（File Descriptor）的概念

- **內容大綱**:
  - 檔案描述符（File Descriptor）的概念
  - `open()`: 開啟檔案
  - `read()`: 讀取檔案
  - `write()`: 寫入檔案
  - `close()`: 關閉檔案
  - `lseek()`: 移動檔案讀寫位置
  - 標準輸入/輸出/錯誤的檔案描述符：0, 1, 2
  - 低階 I/O vs 高階 I/O（`fopen`, `fread`, `fwrite`）

- **程式範例**:
  ```c
  #include <stdio.h>
  #include <fcntl.h>
  #include <unistd.h>

  int main() {
      int fd = open("test.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
      if (fd == -1) {
          perror("開啟檔案失敗");
          return 1;
      }

      write(fd, "Hello, UNIX!\n", 13);
      close(fd);
      return 0;
  }
  ```

- **實作練習**:
  - 使用系統呼叫實作檔案複製程式
  - 實作簡單的 `cat` 命令

#### 4.2 Socket 程式設計入門 (40 分鐘)
- **學習目標**:
  - 理解 Socket 的基本概念
  - 掌握 TCP 客戶端/伺服器的基本架構
  - 學習基本的 Socket API

- **內容大綱**:
  - Socket 的定義：網路通訊的端點
  - TCP vs UDP：可靠連線 vs 無連線
  - `socket()`: 建立 Socket
  - `bind()`: 綁定位址與埠號
  - `listen()`: 監聽連線請求
  - `accept()`: 接受連線
  - `connect()`: 連線到伺服器
  - `send()`/`recv()`: 傳送與接收資料
  - 用戶端-伺服器模型

- **伺服器範例**:
  ```c
  #include <stdio.h>
  #include <sys/socket.h>
  #include <netinet/in.h>

  int main() {
      int server_fd = socket(AF_INET, SOCK_STREAM, 0);

      struct sockaddr_in address;
      address.sin_family = AF_INET;
      address.sin_addr.s_addr = INADDR_ANY;
      address.sin_port = htons(8080);

      bind(server_fd, (struct sockaddr*)&address, sizeof(address));
      listen(server_fd, 3);

      int client_fd = accept(server_fd, NULL, NULL);
      send(client_fd, "Hello from server", 17, 0);

      close(client_fd);
      close(server_fd);
      return 0;
  }
  ```

- **用戶端範例**:
  ```c
  #include <stdio.h>
  #include <sys/socket.h>
  #include <netinet/in.h>

  int main() {
      int sock = socket(AF_INET, SOCK_STREAM, 0);

      struct sockaddr_in serv_addr;
      serv_addr.sin_family = AF_INET;
      serv_addr.sin_port = htons(8080);
      serv_addr.sin_addr.s_addr = inet_addr("127.0.0.1");

      connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr));

      char buffer[1024];
      recv(sock, buffer, sizeof(buffer), 0);
      printf("收到: %s\n", buffer);

      close(sock);
      return 0;
  }
  ```

- **實作練習**:
  - 實作簡單的 Echo 伺服器
  - 實作多用戶端伺服器（使用多進程或多執行緒）

#### 4.3 實戰專案：簡單的 Shell (40 分鐘)
- **學習目標**:
  - 綜合應用本課程所學概念
  - 實作一個功能完整的簡易 Shell
  - 理解 Shell 的工作原理

- **專案需求**:
  - 讀取使用者輸入的指令
  - 解析指令與參數
  - 建立子進程執行指令
  - 支援內建指令：`cd`, `exit`, `pwd`
  - 支援管道（`|`）：將一個指令的輸出作為另一個指令的輸入
  - 支援背景執行（`&`）：指令在背景執行
  - 支援輸入/輸出重導向（`<`, `>`, `>>`）

- **實作提示**:
  1. 主迴圈：讀取輸入 → 解析 → 執行
  2. 指令解析：分割指令與參數，識別特殊符號（`|`, `&`, `<`, `>`, `>>`）
  3. 執行指令：
     - 內建指令：直接執行
     - 外部指令：`fork()` + `exec()`
  4. 管道處理：建立管道，重導向 stdin/stdout
  5. 重導向處理：使用 `open()` + `dup2()` 重導向檔案描述符

- **程式架構**:
  ```c
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>
  #include <unistd.h>
  #include <sys/wait.h>

  // 解析指令
  void parse_command(char* input, char** args, int* background, char* input_file, char* output_file) {
      // 實作指令解析邏輯
  }

  // 執行指令
  void execute_command(char** args, int background) {
      pid_t pid = fork();
      if (pid == 0) {
          execvp(args[0], args);
      } else {
          if (!background) {
              wait(NULL);
          }
      }
  }

  // 處理管道
  void handle_pipe(char** cmd1, char** cmd2) {
      int pipefd[2];
      pipe(pipefd);

      pid_t pid1 = fork();
      if (pid1 == 0) {
          dup2(pipefd[1], STDOUT_FILENO);
          close(pipefd[0]);
          execvp(cmd1[0], cmd1);
      }

      pid_t pid2 = fork();
      if (pid2 == 0) {
          dup2(pipefd[0], STDIN_FILENO);
          close(pipefd[1]);
          execvp(cmd2[0], cmd2);
      }

      close(pipefd[0]);
      close(pipefd[1]);
      wait(NULL);
      wait(NULL);
  }

  int main() {
      char input[256];
      while (1) {
          printf("myshell> ");
          fgets(input, sizeof(input), stdin);
          // 解析並執行指令
      }
      return 0;
  }
  ```

#### 4.4 課程總結與後續學習 (10 分鐘)
- **本週重點**:
  - 檔案 I/O 系統呼叫
  - Socket 程式設計
  - 綜合專案實作

- **課程回顧**:
  - Week 1: UNIX 基礎與進程概念
  - Week 2: 進程控制與 IPC
  - Week 3: 執行緒與同步機制
  - Week 4: 進階主題與實戰

- **後續學習建議**:
  - 進階 IPC：共享記憶體（Shared Memory）、訊息佇列（Message Queue）
  - 網路程式設計：非阻塞 I/O、I/O 多路複用（select, poll, epoll）
  - 系統效能分析：strace, perf, valgrind
  - 深入 Linux 核心：理解系統呼叫的實作
  - 開源專案貢獻：參與 Linux 開源專案

### 週末作業（期末專案）
- **專案主題**：實作一個簡單的多人線上聊天室
- **功能需求**：
  1. 伺服器端：
     - 監聽指定埠號
     - 接受多個用戶端連線
     - 廣播訊息給所有連線的用戶端
     - 使用多執行緒處理多個用戶端
  2. 用戶端：
     - 連線到伺服器
     - 輸入訊息並傳送
     - 接收並顯示其他用戶的訊息
     - 使用多執行緒分離讀寫操作
- **提交要求**：
  - 完整的程式碼（含註釋）
  - README 文件（說明編譯與執行方法）
  - 功能測試截圖
  - 系統架構圖（說明設計思路）
  - 1000 字心得報告（學習歷程與遇到的問題）

---

## 評量標準

### 週末作業（40%）
- 每週作業佔 10%
- 評分項目：
  - 程式碼正確性（40%）
  - 程式碼品質（30%）
  - 心得報告（30%）

### 期末專案（30%）
- 聊天室專案
- 評分項目：
  - 功能完整性（40%）
  - 程式碼品質與架構（30%）
  - 文件完整性（20%）
  - 創意與特色（10%）

### 期末考（30%）
- 理論題（60%）：概念理解、原理說明
- 程式題（40%）：讀程式碼、填空、改錯

---

## 參考資源

### 推薦書籍
1. **Advanced Programming in the UNIX Environment** (APUE) - W. Richard Stevens
2. **UNIX Network Programming** - W. Richard Stevens
3. **Linux 程式設計** - 陳鍾誠、張銘傑

### 線上資源
- [Linux Manual Pages](https://man7.org/linux/man-pages/)
- [Beej's Guide to C Programming](https://beej.us/guide/bgc/)
- [The C Programming Language](https://www.cs.princeton.edu/~bwk/cbook.html)

### 開發工具
- 編譯器：gcc, clang
- 除錯工具：gdb, valgrind
- 編輯器：VS Code, Vim, Emacs
- 系統監控：top, htop, strace

---

## 課程常見問題（FAQ）

**Q: 為什麼要學習系統程式設計？**
A: 系統程式設計是理解作業系統原理的基礎，對於後端開發、系統優化、效能分析等領域非常重要。

**Q: 這門課程會不會太難？**
A: 本課程從基礎概念開始，逐步深入。只要具備 C 語言基礎，配合練習，應該能夠跟上進度。

**Q: 需要使用特定的 Linux 發行版嗎？**
A: 不需要，任何 Linux 或 UNIX-like 系統（Ubuntu, Debian, CentOS, macOS）都可以。推薦使用 Ubuntu 20.04 或更新版本。

**Q: 如何練習系統程式設計？**
A: 建議多實作，例如：
  - 重現課堂範例
  - 完成週末作業
  - 閱讀開源專案程式碼
  - 參加線上程式設計競賽

**Q: 遇到問題該怎麼辦？**
A: 可以：
  - 查閱 Manual Pages (`man` 指令)
  - 使用 Google 搜尋錯誤訊息
  - 詢問同學或助教
  - 在論壇（如 Stack Overflow）發問

---

## 備註

- 本課程以實務為導向，強調「做中學」
- 鼓勵學生主動探索與實驗
- 程式碼風格要求：遵循 GNU Coding Standard
- 所有程式碼需包含適當的註釋
- 鼓勵學生使用版本控制（Git）
- 歡迎學生提出問題與建議
