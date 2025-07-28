# 後端開發進度紀錄 (由 AI 生成)

## 專案初始化與環境設定

1.  **創建後端專案資料夾：**
    *   在 `sidep_app` 的同層目錄下創建了 `sidep_backend` 資料夾。
    *   指令：`mkdir -p /Users/rd02wcs/Desktop/created_app/sidep_backend`

2.  **複製開發計畫到後端專案：**
    *   將 `sidep_app/BACKEND_DEV_PLAN.md` 的內容複製到 `sidep_backend/README.md`。

3.  **初始化 Python 虛擬環境與安裝核心套件：**
    *   在 `sidep_backend` 資料夾內創建並啟用了 Python 虛擬環境 (`venv`)。
    *   安裝了 `fastapi` 和 `uvicorn`。
    *   指令：`cd /Users/rd02wcs/Desktop/created_app/sidep_backend && source venv/bin/activate && pip install fastapi uvicorn`

4.  **創建 FastAPI 應用程式入口檔案：**
    *   在 `sidep_backend` 資料夾內創建了 `main.py`，包含一個基本的 FastAPI 應用和根路由。

## 資料庫設定 (PostgreSQL)

1.  **PostgreSQL 安裝：**
    *   使用者手動安裝了 PostgreSQL (透過 Homebrew)。
    *   確認版本為 14.18，並確認服務已啟動。

2.  **創建資料庫使用者與資料庫：**
    *   使用者手動透過 `psql` 命令列工具，使用其 macOS 使用者名稱 (`rd02wcs`) 連接到 `postgres` 資料庫。
    *   創建了新的資料庫使用者 `sidep_user`，密碼為 `tedke808387`。
    *   創建了新的資料庫 `sidep_db`，並將所有權賦予 `sidep_user`。
    *   指令範例：
        ```sql
        psql -U rd02wcs -d postgres
        CREATE USER sidep_user WITH PASSWORD tedke808387;
        CREATE DATABASE sidep_db OWNER sidep_user;
        \q
        ```

3.  **安裝資料庫驅動與 ORM：**
    *   在 `sidep_backend` 虛擬環境中安裝了 `psycopg2-binary` (PostgreSQL 驅動) 和 `SQLAlchemy` (ORM)。
    *   指令：`cd /Users/rd02wcs/Desktop/created_app/sidep_backend && source venv/bin/activate && pip install psycopg2-binary sqlalchemy`

## 第一階段：核心後端改造 - 建立資料所有權 (已完成)

### 1. 修改資料庫模型 (`sidep_backend/models.py`)
*   為 `Service`, `Booking`, `BusinessHour`, `Holiday`, `UnavailableDate`, `BookableTimeSlot` 模型增加了 `owner_id` 欄位，並設為指向 `users.id` 的外鍵與索引。
*   更新了 `sqlalchemy.orm` 的 import 語句，加入了 `Mapped` 和 `mapped_column`。

### 2. 執行資料庫遷移 (Alembic)
*   初始化了 Alembic 環境，並生成了初始遷移檔案。
*   執行了 `alembic revision --autogenerate -m "Add owner_id for multi-tenancy support"`，成功生成了包含 `owner_id` 變更的遷移檔案。
*   執行了 `alembic upgrade head`，成功應用了遷移，將 `owner_id` 欄位添加到資料庫中。

### 3. 調整 API 邏輯 (`sidep_backend/main.py`)
*   修改了 `get_current_admin_user` 函數，使其返回 `models.User`。
*   **Service 相關 API：**
    *   `POST /services/`: 在創建服務時，自動將 `current_user.id` 寫入 `owner_id`。
    *   `GET /services/`: 查詢服務列表時，添加 `owner_id = current_user.id` 過濾條件。
    *   `GET /services/{service_id}`: 查詢單個服務時，添加 `owner_id = current_user.id` 過濾條件。
    *   `PUT /services/{service_id}`: 更新服務時，驗證 `owner_id` 與 `current_user.id` 是否一致。
    *   `PATCH /services/{service_id}/status`: 更新服務狀態時，驗證 `owner_id` 與 `current_user.id` 是否一致。
    *   `DELETE /services/{service_id}`: 刪除服務時，驗證 `owner_id` 與 `current_user.id` 是否一致。
    *   `POST /services/bulk-action`: 批量操作服務時，添加 `owner_id = current_user.id` 過濾條件。
*   **Booking 相關 API：**
    *   `POST /bookings/`: 在創建預約時，自動將 `current_user.id` 寫入 `owner_id`，並驗證服務的 `owner_id`。
    *   `GET /bookings/`: 查詢預約列表時，添加 `owner_id = current_user.id` 過濾條件。
    *   `PUT /bookings/{booking_id}/status`: 更新預約狀態時，驗證 `owner_id` 與 `current_user.id` 是否一致。
    *   `PUT /bookings/{booking_id}`: 更新預約時，驗證 `owner_id` 與 `current_user.id` 是否一致。
    *   `DELETE /bookings/{booking_id}`: 刪除預約時，驗證 `owner_id` 與 `current_user.id` 是否一致。
*   **Business Settings 相關 API：**
    *   `GET /admin/settings/`: 查詢營業設定時，添加 `owner_id` 過濾條件。
    *   `PUT /admin/settings/`: 更新營業設定時，在刪除舊資料和新增新資料時都添加 `owner_id` 處理。
    *   `PUT /admin/settings/business-hours`: 更新營業時間時，添加 `owner_id` 處理。
    *   `POST /admin/settings/holidays`: 添加假日時，添加 `owner_id` 處理。
    *   `DELETE /admin/settings/holidays/{holiday_date}`: 刪除假日時，驗證 `owner_id` 與 `current_user.id` 是否一致。
    *   `POST /admin/settings/unavailable-dates`: 添加不可預約日期時，添加 `owner_id` 處理。
    *   `DELETE /admin/settings/unavailable-dates/{unavailable_date}`: 刪除不可預約日期時，驗證 `owner_id` 與 `current_user.id` 是否一致。
    *   `POST /admin/settings/time-slots`: 添加可預約時間段時，添加 `owner_id` 處理。
    *   `DELETE /admin/settings/time-slots/{time_slot_id}`: 刪除可預約時間段時，驗證 `owner_id` 與 `current_user.id` 是否一致。

## 第二階段：前後端串接 - 實現專屬預約流程 (後端部分已完成)

### 1. 後端 - 建立管理員的公開識別碼與 API (`sidep_backend`)
*   **修改 `models.py`:** 在 `User` 模型中新增 `public_slug` 欄位。
*   **執行 Alembic 遷移:** 成功應用了 `public_slug` 欄位到資料庫。
*   **修改 `main.py` (`/auth/register`):** 在管理員註冊的邏輯中，自動生成一個唯一的 `public_slug` 並存入資料庫。
*   **新增 `main.py` (公開 API):** 建立了一個無需認證的 API 端點 `GET /public/profile/{slug}`，用於根據 slug 回傳店家的公開資訊（服務、設定等）。
*   **修改 `schemas.py`:** 為 `BookingCreate` 添加 `public_slug` 欄位，並為 `UserResponse` 添加 `public_slug` 欄位，同時定義了 `UserPublicProfileResponse`。
*   **修改 `main.py` (`POST /bookings`):** 讓此 API 能接收 `public_slug` 參數，以便在建立預約時，能根據 slug 查找到正確的 `owner_id` 並寫入。

## 目前狀態

*   後端專案 `sidep_backend` 已建立，並配置了 Python 虛擬環境。
*   FastAPI 和 Uvicorn 已安裝。
*   `main.py` 檔案已創建，包含一個基本的 FastAPI 應用。
*   PostgreSQL 已安裝並運行，`sidep_db` 資料庫和 `sidep_user` 已創建。
*   `psycopg2-binary` 和 `SQLAlchemy` 已安裝。
*   **第一階段「核心後端改造 - 建立資料所有權」已全部完成。**
*   **第二階段「前後端串接 - 實現專屬預約流程」的後端部分已全部完成。**

**下一步：** 進入第二階段「前後端串接 - 實現專屬預約流程」的前端部分。
