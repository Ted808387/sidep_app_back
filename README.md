# 後端開發計畫

## 推薦後端技術棧：Python + FastAPI + PostgreSQL

### 理由：

1.  **FastAPI 的高效與現代化：**
    *   **高性能：** FastAPI 基於 Starlette (Web 部分) 和 Pydantic (資料驗證) 構建，性能非常接近 Go 和 Node.js，遠超傳統 Python 框架如 Flask 或 Django。
    *   **易於學習和使用：** 語法簡潔，基於 Python 類型提示，開發效率高。
    *   **自動生成 API 文件：** 內建 Swagger UI 和 ReDoc，自動生成互動式 API 文件，這對於前端開發者來說非常方便，可以清晰了解每個 API 的輸入、輸出和錯誤碼。
    *   **異步支持：** 原生支持 `async/await`，非常適合處理高併發的 I/O 操作，例如資料庫查詢和外部 API 呼叫。
2.  **Python 的生態系統：**
    *   Python 擁有龐大且活躍的生態系統，有豐富的函式庫和工具，可以輕鬆處理資料處理、排程任務、機器學習等未來可能的需求。
3.  **PostgreSQL 的穩定與強大：**
    *   PostgreSQL 是一個功能強大、穩定且符合標準的開源關聯式資料庫，非常適合儲存預約、服務、用戶等結構化資料。它支持複雜的查詢、事務處理和資料完整性。

---

## 開始後端開發的步驟概述：

1.  **建立新的後端專案資料夾：**
    *   在 `sidep_app` 的同層目錄下，創建一個新的資料夾，例如 `sidep_backend`。

2.  **初始化 Python 虛擬環境和 FastAPI 專案：**
    *   進入 `sidep_backend` 資料夾。
    *   創建並啟用 Python 虛擬環境。
    *   安裝 FastAPI 和 Uvicorn (ASGI 伺服器)。
    *   創建一個基本的 `main.py` 檔案來啟動 FastAPI 應用。

3.  **設定 PostgreSQL 資料庫：**
    *   確保您的系統上安裝了 PostgreSQL。
    *   創建一個新的資料庫和使用者。
    *   在 FastAPI 專案中安裝資料庫驅動 (例如 `psycopg2-binary`) 和 ORM (例如 SQLAlchemy 或 Alembic)。

4.  **定義資料庫模型 (Models)：**
    *   根據 `README.md` 中描述的功能，定義預約 (Bookings)、服務 (Services)、客戶 (Clients)、用戶 (Users)、營業設定 (Business Settings) 等資料的模型。

5.  **實作 API 端點 (Endpoints)：**
    *   根據前端的需求，逐步實作 RESTful API 端點，例如：
        *   用戶註冊、登入 (`/auth/register`, `/auth/login`)
        *   獲取服務列表 (`/services`)
        *   創建預約 (`/bookings`)
        *   管理員操作 (例如 `/admin/clients`, `/admin/services`)

6.  **替換前端的 `dataService`：**
    *   一旦後端 API 準備就緒，逐步修改前端 `src/api/index.js` 中的模擬 `dataService` 呼叫，改為實際的 HTTP 請求 (例如使用 `axios` 或 `fetch`) 到後端 API。

7.  **實作認證與授權：**
    *   在 FastAPI 中實作 JWT (JSON Web Tokens) 認證，並根據用戶角色實作基於角色的訪問控制 (RBAC)。

---

## 資料庫模型大綱

根據專案的需求，我們需要以下核心資料庫表格 (Entities) 來儲存應用程式的資料：

1.  **User (用戶)**
    *   **用途：** 儲存所有使用者資訊，包括客戶和管理員。
    *   **欄位範例：** `id` (主鍵), `email` (唯一), `password` (雜湊後), `name`, `phone_number`, `role` (例如 customer, admin), `registration_date`。
    *   **關係：** 一個用戶可以有多個預約。

2.  **Service (服務項目)**
    *   **用途：** 儲存所有可提供的服務項目資訊。
    *   **欄位範例：** `id` (主鍵), `name`, `description`, `price`, `duration` (或 `min_duration`, `max_duration`), `is_active` (是否上架), `category` (可選), `image_url` (可選)。
    *   **關係：** 一個服務項目可以有多個預約。

3.  **Booking (預約)**
    *   **用途：** 儲存客戶的預約資訊。
    *   **欄位範例：** `id` (主鍵), `user_id` (外鍵，關聯到 User), `service_id` (外鍵，關聯到 Service), `date`, `time`, `status` (例如 pending, confirmed, cancelled, completed), `notes` (備註), `created_at`, `updated_at`。
    *   **關係：** 一個預約屬於一個用戶和一個服務項目。

4.  **BusinessSetting (營業設定)**
    *   **用途：** 儲存店舖的營業時間、假日、不可預約日期和可預約時段等。這部分可以拆分成多個小表或合併。為了清晰起見，我們可以考慮以下子模型：
        *   **BusinessHour (營業時間):** `id`, `day_of_week`, `open_time`, `close_time`
        *   **Holiday (假日):** `id`, `date`, `description`
        *   **UnavailableDate (不可預約日期):** `id`, `date`, `reason`
        *   **BookableTimeSlot (可預約時段):** `id`, `start_time`, `end_time` (這可能更適合動態生成，而不是固定儲存)

## 資料庫模型建立步驟

我建議按照以下邏輯順序來建立這些模型：

1.  **設定資料庫連接 (database.py)：**
    *   創建一個 `database.py` 檔案，用於配置 SQLAlchemy 的資料庫引擎、會話 (Session) 和聲明基類 (Base)。這是所有模型定義的基礎。

2.  **定義 User 模型 (models/user.py 或 models.py)：**
    *   首先定義 `User` 模型，因為它是許多其他操作的基礎。

3.  **定義 Service 模型 (models/service.py 或 models.py)：**
    *   `Service` 模型相對獨立，可以接著定義。

4.  **定義 Booking 模型 (models/booking.py 或 models.py)：**
    *   `Booking` 模型需要引用 `User` 和 `Service`，所以要在它們之後定義。

5.  **定義 Business Settings 相關模型 (models/settings.py 或 models.py)：**
    *   `BusinessHour`, `Holiday`, `UnavailableDate` 等模型可以獨立定義，或根據複雜度合併。

6.  **初始化資料庫表格：**
    *   在 `main.py` 或一個單獨的腳本中，添加程式碼來創建所有定義好的資料庫表格。

7.  **定義 Pydantic Schemas (schemas.py)：**
    *   為每個資料庫模型創建對應的 Pydantic 模型，用於 FastAPI 的請求驗證和響應序列化。這將確保 API 傳輸的資料格式正確。

### **實作流程：**

我將從第一步開始：**設定資料庫連接**。

我會在 `sidep_backend` 資料夾中創建一個 `database.py` 檔案，並配置 SQLAlchemy。
