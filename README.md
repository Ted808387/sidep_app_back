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

---

## 後端開發進度

### 階段一：專案初始化與資料庫設定

1.  **創建後端專案資料夾：**
    *   在 `sidep_app` 的同層目錄下創建了 `sidep_backend` 資料夾。

2.  **複製開發計畫到後端專案：**
    *   將 `sidep_app/BACKEND_DEV_PLAN.md` 的內容複製到 `sidep_backend/README.md`。

3.  **初始化 Python 虛擬環境與安裝核心套件：**
    *   在 `sidep_backend` 資料夾內創建並啟用了 Python 虛擬環境 (`venv`)。
    *   安裝了 `fastapi` 和 `uvicorn`。

4.  **創建 FastAPI 應用程式入口檔案：**
    *   在 `sidep_backend` 資料夾內創建了 `main.py`，包含一個基本的 FastAPI 應用和根路由。

5.  **PostgreSQL 安裝與設定：**
    *   使用者手動安裝了 PostgreSQL (版本 14.18)。
    *   確認 PostgreSQL 服務已啟動。
    *   透過 `psql` 創建了資料庫使用者 `sidep_user` 和資料庫 `sidep_db`。
    *   在 `sidep_backend` 虛擬環境中安裝了 `psycopg2-binary` (PostgreSQL 驅動) 和 `SQLAlchemy` (ORM)。

### 階段二：資料庫模型與 API 認證實作

1.  **設定資料庫連接 (database.py)：**
    *   創建了 `sidep_backend/database.py` 檔案，配置了 SQLAlchemy 的資料庫引擎、會話和聲明基類。

2.  **定義資料庫模型 (models.py)：**
    *   創建了 `sidep_backend/models.py` 檔案，並定義了 `User`、`Service`、`Booking`、`BusinessHour`、`Holiday` 和 `UnavailableDate` 等核心資料庫模型。
    *   修正了 `models.py` 中 `Base` 導入的問題，確保所有模型都正確註冊到 `database.py` 的 `Base` 物件上。

3.  **初始化資料庫表格：**
    *   修改了 `sidep_backend/main.py`，在應用程式啟動時自動創建所有定義在 `models.py` 中的資料庫表格。
    *   修正了 `main.py` 中導入 `database` 和 `models` 的方式，從相對導入改為絕對導入，解決了 `ImportError`。

4.  **定義 Pydantic Schemas (schemas.py)：**
    *   創建了 `sidep_backend/schemas.py` 檔案，並為所有核心資料庫模型定義了對應的 Pydantic Schemas (Base, Create, Response)。
    *   安裝了 `email-validator` 函式庫，解決了 Pydantic `EmailStr` 類型驗證的依賴問題。

5.  **實作用戶認證 API 端點：**
    *   安裝了 `passlib[bcrypt]` 用於密碼雜湊。
    *   在 `sidep_backend/main.py` 中實作了 `/auth/register` (用戶註冊) 和 `/auth/login` (用戶登入) API 端點。
    *   修正了 `login` 函數的參數類型為 `schemas.UserCreate`。
    *   成功測試了用戶註冊和登入功能。

### 階段三：服務管理 API 實作

1.  **實作服務管理 API 端點：**
    *   在 `sidep_backend/main.py` 中添加了 `service_router`，包含了以下端點：
        *   `GET /services/`：獲取所有服務列表。
        *   `GET /services/{service_id}`：獲取單一服務。
        *   `POST /services/`：新增服務 (待添加管理員權限驗證)。
        *   `PUT /services/{service_id}`：更新服務 (待添加管理員權限驗證)。
        *   `DELETE /services/{service_id}`：刪除服務 (待添加管理員權限驗證)。
    *   成功測試了所有服務管理 API 端點 (新增、獲取、更新、刪除)。

    *   在 `sidep_backend/main.py` 的 `service_router` 中新增了 `PATCH /services/{service_id}/status` 端點，用於快速切換服務的上架/下架狀態。

    *   在 `sidep_backend/main.py` 的 `service_router` 中新增了 `POST /services/bulk-action` 端點，用於批次上架、下架或刪除服務。

### 階段四：預約管理 API 實作

1.  **實作預約管理 API 端點：**
    *   在 `sidep_backend/main.py` 中添加了 `booking_router`，包含了以下端點：
        *   `POST /bookings/`：創建預約 (待添加用戶認證和時間可用性檢查)。
        *   `GET /bookings/my`：獲取當前用戶的預約紀錄 (待從認證中獲取用戶 ID)。
        *   `GET /bookings/`：獲取所有預約 (待添加管理員權限驗證)。
        *   `PUT /bookings/{booking_id}/status`：更新預約狀態 (待添加管理員權限驗證)。
        *   `PUT /bookings/{booking_id}`：更新預約的詳細資訊（例如備註）。
        *   `DELETE /bookings/{booking_id}`：刪除預約 (待添加管理員權限驗證)。
    *   成功測試了所有預約管理 API 端點 (創建、獲取、更新狀態、刪除)。

### 階段五：客戶管理 API 實作

1.  **實作客戶管理 API 端點：**
    *   在 `sidep_backend/main.py` 中添加了 `client_router`，包含了以下端點：
        *   `GET /admin/clients/`：獲取所有客戶列表 (待添加管理員權限驗證)。
        *   `GET /admin/clients/{client_id}`：獲取單一客戶詳細資訊 (待添加管理員權限驗證)。
        *   `PUT /admin/clients/{client_id}`：更新客戶的詳細資訊 (待添加管理員權限驗證)。
    *   成功測試了所有客戶管理 API 端點 (獲取、更新)。

### 階段六：營業設定管理 API 實作

1.  **實作營業設定管理 API 端點：**
    *   在 `sidep_backend/main.py` 中添加了 `business_settings_router`，包含了以下端點：
        *   `GET /admin/settings/`：獲取營業設定 (待添加管理員權限驗證)。
        *   `PUT /admin/settings/business-hours`：更新營業時間 (待添加管理員權限驗證)。
        *   `POST /admin/settings/holidays`：新增假日 (待添加管理員權限驗證)。
        *   `DELETE /admin/settings/holidays/{holiday_date}`：刪除假日 (待添加管理員權限驗證)。
        *   `POST /admin/settings/unavailable-dates`：新增不可預約日期 (待添加管理員權限驗證)。
        *   `DELETE /admin/settings/unavailable-dates/{unavailable_date}`：刪除不可預約日期 (待添加管理員權限驗證)。
    *   成功測試了所有營業設定管理 API 端點 (獲取、更新營業時間、新增/刪除假日、新增/刪除不可預約日期)。

### 階段七：實作完整的 JWT 認證與授權

1.  **安裝 JWT 函式庫：**
    *   安裝了 `python-jose[cryptography]`。

2.  **配置 JWT 相關參數：**
    *   在 `main.py` 中定義了 `SECRET_KEY`、`ALGORITHM` 和 `ACCESS_TOKEN_EXPIRE_MINUTES`。

3.  **實作 JWT 工具函數：**
    *   `create_access_token`：用於生成 JWT Token。
    *   `get_current_user`：用於驗證 Token 並獲取當前用戶。
    *   `get_current_admin_user`：用於檢查用戶是否為管理員。

4.  **應用 JWT 認證與授權：**
    *   將 `Depends(get_current_user)` 或 `Depends(get_current_admin_user)` 應用到所有需要保護的 API 端點。
    *   修正了 `main.py` 中 `HTTPBearer` 實例化時不應包含 `tokenUrl` 參數的問題，以確保 Swagger UI 正確顯示 Bearer Token 輸入框。
    *   修正了 `JWTError: Subject must be a string` 的問題，確保 `sub` 聲明為字串。
    *   **成功測試了 JWT 認證與授權功能，確認受保護的端點可以正常訪問。**

### 階段八：使用者個人資料 API 實作

1.  **實作使用者個人資料 API 端點：**
    *   在 `sidep_backend/main.py` 中添加了 `user_router`，包含了以下端點：
        *   `GET /users/me`：獲取當前登入使用者的詳細資訊。
        *   `PUT /users/me`：更新當前登入使用者的個人資料。
        *   `POST /users/me/change-password`：變更當前登入使用者的密碼。
    *   成功測試了所有使用者個人資料 API 端點。

### 階段九：營業設定統一管理 API 實作

1.  **實作營業設定統一管理 API 端點：**
    *   在 `sidep_backend/main.py` 的 `business_settings_router` 中新增了 `PUT /admin/settings/` 端點，用於統一更新營業時間、假日和不可預約日期。
    *   在 `schemas.py` 中新增了 `BusinessSettingsUpdate` 模型。

### 階段十：可預約時間段管理 API 實作

1.  **實作可預約時間段管理 API 端點：**
    *   在 `sidep_backend/models.py` 中新增了 `BookableTimeSlot` 模型。
    *   在 `sidep_backend/schemas.py` 中新增了 `BookableTimeSlotBase`, `BookableTimeSlotCreate`, `BookableTimeSlotResponse` 模型。
    *   在 `sidep_backend/main.py` 的 `business_settings_router` 中新增了 `POST /admin/settings/time-slots` 和 `DELETE /admin/settings/time-slots/{time_slot_id}` 端點。

**目前狀態：**

*   後端專案 `sidep_backend` 已建立，並配置了 Python 虛擬環境。
*   FastAPI 和 Uvicorn 已安裝並正常運行。
*   PostgreSQL 已安裝並運行，`sidep_db` 資料庫和所有預期的表格已成功創建。
*   所有核心資料庫模型和 Pydantic Schemas 已定義。
*   用戶認證 API 端點已實作並測試成功。
*   服務管理 API 端點已實作並測試成功。
*   預約管理 API 端點已實作並測試成功。
*   客戶管理 API 端點已實作並測試成功。
*   營業設定管理 API 端點已實作並測試成功。
*   **完整的 JWT 認證與授權已實作並測試成功。**

**下一步：** 替換前端的 `dataService`，使其呼叫實際的後端 API。

### **後端 API 開發與測試狀態**

**目標：** 實作所有必要的 API 端點，並透過與前端的整合測試來驗證其功能。

**測試原則：**
*   每個 API 端點在開發完成後，都應先進行單元測試（例如使用 Postman 或 `curl`）。
*   與前端整合後，進行完整的端到端測試。
*   測試完成後，在此處更新狀態。

---

#### **階段一：認證與使用者資料**

1.  **用戶註冊 (`/auth/register`)**
    *   **開發狀態：** 已完成。
    *   **整合測試狀態：** **已完成**。✅

2.  **用戶登入 (`/auth/login`)**
    *   **開發狀態：** 已完成。
    *   **整合測試狀態：** **已完成**。✅

3.  **使用者個人資料 (`/users/me`)**
    *   **API 端點：** `GET /users/me`, `PUT /users/me`, `POST /users/me/change-password`
    *   **開發狀態：** 已完成。
    *   **整合測試狀態：** 待測試。

---

#### **階段二：服務管理**

1.  **服務管理 (`/services`)**
    *   **API 端點：** `GET, POST /services/`, `PUT, DELETE /services/{service_id}`, `PATCH /services/{service_id}/status`, `POST /services/bulk-action`
    *   **開發狀態：** 已完成。
    *   **整合測試狀態：** **已完成** (獲取、新增、編輯服務)。其餘待測試。

---

#### **階段三：預約管理**

1.  **預約管理 (`/bookings`)**
    *   **API 端點：** `GET /bookings/`, `POST /bookings/`, `GET /bookings/my`, `PUT /bookings/{booking_id}/status`, `DELETE /bookings/{booking_id}`
    *   **開發狀態：** 已完成。
    *   **整合測試狀態：** 待測試。

---

#### **階段四：客戶管理**

1.  **客戶管理 (`/admin/clients`)**
    *   **API 端點：** `GET /admin/clients/`, `GET, PUT /admin/clients/{client_id}`
    *   **開發狀態：** 已完成。
    *   **整合測試狀態：** 待測試。

---

#### **階段五：營業設定**

1.  **營業設定 (`/admin/settings`)**
    *   **API 端點：** `GET, PUT /admin/settings/`, `POST, DELETE /admin/settings/holidays`, `POST, DELETE /admin/settings/unavailable-dates`, `POST, DELETE /admin/settings/time-slots`
    *   **開發狀態：** 已完成。
    *   **整合測試狀態：** **已完成** (設定營業時間)。其餘待測試。

### **登出功能完善**

**目標：** 確保登出功能不僅清除前端狀態，還能通知後端使 JWT Token 失效。

**進度：**

1.  **後端 `sidep_backend/models.py`：** 已添加 `BlacklistedToken` 模型。✅
2.  **後端 `sidep_backend/schemas.py`：** 已添加 `BlacklistedToken` 的 Pydantic Schema。✅
3.  **後端 `sidep_backend/main.py`：**
    *   已新增 `/auth/logout` 端點，將 Token 加入黑名單。✅
    *   已修改 `get_current_user` 函數，檢查 Token 是否在黑名單中。✅

**下一步：** 測試登出功能，確認 Token 是否正確失效。

### **Alembic 資料庫遷移工具整合**

**目標：** 引入 Alembic 以便安全、高效地管理資料庫結構變更，避免手動刪除資料庫。

**進度：**

1.  **安裝 Alembic：** 已完成。✅
2.  **初始化 Alembic 環境：** 已完成。✅
3.  **配置 Alembic (`alembic.ini`, `alembic/env.py`)：** 已完成。✅
4.  **生成第一個遷移腳本：** 已完成，用於添加 `User` 模型中的 `avatar_url`、`email_notifications_enabled`、`sms_notifications_enabled` 欄位，以及 `BlacklistedToken` 模型。✅
5.  **應用遷移腳本：** 已完成。✅
6.  **生成新的遷移腳本：** 已完成，用於添加 `User` 模型中的通知設定欄位。✅
7.  **應用新的遷移腳本：** 已完成。✅

**下一步：** 重新啟動後端應用程式，並測試所有功能，特別是涉及 `User` 模型新欄位的操作。
