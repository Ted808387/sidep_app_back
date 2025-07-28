import random
import string
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from jose import JWTError, jwt
from fastapi.security import HTTPBearer
from fastapi import Security
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base, get_db
import models, schemas

app = FastAPI(
    title="Sidep App Backend API",
    description="API for Sidep App booking system",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    security_schemes={
        "BearerAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Enter your bearer token in the format **Bearer &lt;token&gt;**"
        }
    }
)

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 創建所有資料庫表格
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

# JWT 相關配置
SECRET_KEY = "nail-beautiful-and-secret-key-for-your-fastapi-app-TTTEEEDDD" # 請替換為一個複雜且保密的字串
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

bearer_scheme = HTTPBearer() # 使用 HTTPBearer
optional_bearer_scheme = HTTPBearer(auto_error=False) # 用於可選認證

# 密碼雜湊上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 工具函數
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 檢查 token 是否在黑名單中
    blacklisted_token = db.query(models.BlacklistedToken).filter(models.BlacklistedToken.token == token).first()
    if blacklisted_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been blacklisted")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(optional_bearer_scheme), db: Session = Depends(get_db)) -> Optional[models.User]:
    if credentials is None:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    blacklisted_token = db.query(models.BlacklistedToken).filter(models.BlacklistedToken.token == token).first()
    if blacklisted_token:
        return None

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    return user

def get_current_admin_user(current_user: schemas.UserResponse = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user

# 認證路由
auth_router = APIRouter(prefix="/auth", tags=["Auth"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@auth_router.post("/register", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, name=user.name, phone_number=user.phone_number, role=user.role, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@auth_router.post("/login")
async def login_for_access_token(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not db_user or not verify_password(user_data.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires # 暫時移除 role
    )
    return {"access_token": access_token, "token_type": "bearer", "user_id": db_user.id, "user_role": db_user.role}

@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(credentials: HTTPBearer = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    blacklisted_token = models.BlacklistedToken(token=token)
    db.add(blacklisted_token)
    db.commit()
    return {"message": "Successfully logged out"}

app.include_router(auth_router)

# 服務路由
service_router = APIRouter(prefix="/services", tags=["Services"])

@service_router.get("/", response_model=List[schemas.ServiceResponse])
async def get_all_services(db: Session = Depends(get_db)):
    services = db.query(models.Service).all()
    return services

@service_router.get("/{service_id}", response_model=schemas.ServiceResponse)
async def get_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service

@service_router.post("/", response_model=schemas.ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(service: schemas.ServiceCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_service = models.Service(
        name=service.name,
        description=service.description,
        price=service.price,
        min_duration=service.min_duration,
        max_duration=service.max_duration,
        is_active=service.is_active,
        category=service.category,
        image_url=service.image_url
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@service_router.put("/{service_id}", response_model=schemas.ServiceResponse)
async def update_service(service_id: int, service: schemas.ServiceCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if db_service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    update_data = service.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_service, key, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service

@service_router.patch("/{service_id}/status", response_model=schemas.ServiceResponse)
async def update_service_status(service_id: int, status_update: schemas.ServiceStatusUpdate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if db_service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    db_service.is_active = status_update.is_active
    db.commit()
    db.refresh(db_service)
    return db_service

@service_router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: int, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if db_service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    db.delete(db_service)
    db.commit()
    return

@service_router.post("/bulk-action", status_code=status.HTTP_200_OK)
async def bulk_service_action(request: schemas.BulkServiceActionRequest, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    if request.action not in ["activate", "deactivate", "delete"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action specified")

    services_to_update = db.query(models.Service).filter(models.Service.id.in_(request.service_ids)).all()

    if not services_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No services found for the given IDs")

    for service in services_to_update:
        if request.action == "activate":
            service.is_active = True
        elif request.action == "deactivate":
            service.is_active = False
        elif request.action == "delete":
            db.delete(service)

    db.commit()
    return {"message": f"Services {request.action}d successfully"}

app.include_router(service_router)

# 預約路由
booking_router = APIRouter(prefix="/bookings", tags=["Bookings"])

@booking_router.post("/", response_model=schemas.BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: Optional[schemas.UserResponse] = Depends(get_optional_current_user)
):
    # 如果提供了 user_id，則檢查是否與當前登入用戶匹配
    # 管理員可以為任何用戶創建預約，所以如果當前用戶是管理員，則跳過此檢查
    if booking.user_id is not None:
        if current_user is None or (current_user.role != "admin" and booking.user_id != current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create booking for another user or without proper authentication")
    else:
        # 如果沒有提供 user_id，則必須提供客戶姓名、Email和電話
        if not booking.customer_name or not booking.customer_email or not booking.customer_phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer name, email, and phone are required for anonymous bookings")

    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    db_booking = models.Booking(
        user_id=booking.user_id,
        service_id=booking.service_id,
        date=booking.date,
        time=booking.time,
        status=booking.status,
        notes=booking.notes if booking.notes is not None else "",
        customer_name=booking.customer_name,
        customer_email=booking.customer_email,
        customer_phone=booking.customer_phone
    )
    
    db.add(db_booking)
    db.flush() # 確保 db_booking.id 被賦值

    # 生成預約編號
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    db_booking.booking_reference_id = f"NA{random_string}{db_booking.id}"

    db.commit()
    db.refresh(db_booking)

    # 查詢完整的預約資訊以回傳
    # 對於匿名預約，不需要 joinedload user
    if db_booking.user_id:
        booking_response = db.query(models.Booking).options(
            joinedload(models.Booking.user),
            joinedload(models.Booking.service)
        ).filter(models.Booking.id == db_booking.id).first()
        client_name = booking_response.user.name
    else:
        booking_response = db.query(models.Booking).options(
            joinedload(models.Booking.service)
        ).filter(models.Booking.id == db_booking.id).first()
        client_name = booking_response.customer_name

    return schemas.BookingResponse(
        id=booking_response.id,
        booking_reference_id=booking_response.booking_reference_id,
        user_id=booking_response.user_id,
        service_id=booking_response.service_id,
        date=booking_response.date,
        time=booking_response.time,
        status=booking_response.status,
        notes=booking_response.notes,
        created_at=booking_response.created_at,
        updated_at=booking_response.updated_at,
        clientName=client_name,
        serviceName=booking_response.service.name
    )

@booking_router.get("/my", response_model=List[schemas.BookingResponse])
async def get_my_bookings(db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_user)):
    bookings_with_details = db.query(
        models.Booking,
        models.User.name.label("client_name"),
        models.Service.name.label("service_name")
    ).join(models.User).join(models.Service).filter(models.Booking.user_id == current_user.id).all()

    # 將查詢結果轉換為 BookingResponse 列表
    response_bookings = []
    for booking, client_name, service_name in bookings_with_details:
        response_data = {
            "id": booking.id,
            "user_id": booking.user_id,
            "service_id": booking.service_id,
            "date": booking.date,
            "time": booking.time,
            "status": booking.status,
            "notes": booking.notes if booking.notes is not None else "", # 處理 notes 為 None 的情況
            "created_at": booking.created_at,
            "updated_at": booking.updated_at,
            "clientName": client_name,
            "serviceName": service_name,
        }
        response_bookings.append(schemas.BookingResponse(**response_data))
    return response_bookings

@booking_router.get("/", response_model=List[schemas.BookingResponse])
async def get_all_bookings(db: Session = Depends(get_db)):
    bookings_with_details = db.query(
        models.Booking,
        models.Service.name.label("service_name")
    ).join(models.Service).all()

    response_bookings = []
    for booking, service_name in bookings_with_details:
        client_name = None
        if booking.user_id:
            user = db.query(models.User).filter(models.User.id == booking.user_id).first()
            if user: # 確保用戶存在
                client_name = user.name
        else:
            client_name = booking.customer_name # 匿名預約使用 customer_name

        response_data = {
            "id": booking.id,
            "booking_reference_id": booking.booking_reference_id,
            "user_id": booking.user_id,
            "service_id": booking.service_id,
            "date": booking.date,
            "time": booking.time,
            "status": booking.status,
            "notes": booking.notes if booking.notes is not None else "",
            "created_at": booking.created_at,
            "updated_at": booking.updated_at,
            "clientName": client_name,
            "serviceName": service_name,
        }
        response_bookings.append(schemas.BookingResponse(**response_data))
    return response_bookings

@booking_router.put("/{booking_id}/status", response_model=schemas.BookingResponse)
async def update_booking_status(booking_id: int, status: str, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    db_booking.status = status
    db.commit()
    db.refresh(db_booking)
    return db_booking

@booking_router.put("/{booking_id}", response_model=schemas.BookingResponse)
async def update_booking(booking_id: int, booking_update: schemas.BookingUpdate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_user)):
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    # 只有管理員可以修改狀態，普通用戶只能修改備註
    if current_user.role == "customer" and booking_update.status is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Customers cannot change booking status")

    update_data = booking_update.model_dump(exclude_unset=True)
    if "notes" in update_data and update_data["notes"] is None:
        update_data["notes"] = ""
    if "notes" in update_data and update_data["notes"] is None:
        update_data["notes"] = ""
    for key, value in update_data.items():
        setattr(db_booking, key, value)
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

@booking_router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(booking_id: int, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    db.delete(db_booking)
    db.commit()
    return

app.include_router(booking_router)

# 客戶管理路由 (管理員專用)
client_router = APIRouter(prefix="/admin/clients", tags=["Admin - Clients"])

@client_router.get("/", response_model=List[schemas.UserResponse])
async def get_all_clients(db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    clients = db.query(models.User).filter(models.User.role == "customer").all()
    return clients

@client_router.get("/{client_id}", response_model=schemas.UserResponse)
async def get_client(client_id: int, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    client = db.query(models.User).filter(models.User.id == client_id, models.User.role == "customer").first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client

@client_router.put("/{client_id}", response_model=schemas.UserResponse)
async def update_client(client_id: int, client_update: schemas.UserBase, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_client = db.query(models.User).filter(models.User.id == client_id, models.User.role == "customer").first()
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    
    # 不允許直接更新密碼和角色，這些應該有單獨的端點或更嚴格的控制
    update_data = client_update.model_dump(exclude_unset=True)
    update_data.pop("password", None) # 確保不更新密碼
    update_data.pop("role", None) # 確保不更新角色

    for key, value in update_data.items():
        setattr(db_client, key, value)
    
    db.commit()
    db.refresh(db_client)
    return db_client

app.include_router(client_router)

# 營業設定路由 (管理員專用)
business_settings_router = APIRouter(prefix="/admin/settings", tags=["Admin - Business Settings"])

@business_settings_router.get("/", response_model=schemas.BusinessSettingsResponse)
async def get_business_settings(db: Session = Depends(get_db)):
    business_hours_from_db = db.query(models.BusinessHour).order_by(models.BusinessHour.id).all()
    holidays = db.query(models.Holiday).all()
    unavailable_dates = db.query(models.UnavailableDate).all()
    bookable_time_slots = db.query(models.BookableTimeSlot).all()

    # 如果營業時間是空的，就創建預設值 (週一到週日)
    if not business_hours_from_db:
        default_hours = [
            # 週一到週六 10:00 - 19:00
            models.BusinessHour(day_of_week=i, open_time=time(10, 0), close_time=time(19, 0), is_closed=False) for i in range(1, 7)
        ]
        # 週日公休
        default_hours.append(models.BusinessHour(day_of_week=7, open_time=time(10, 0), close_time=time(19, 0), is_closed=True))
        
        db.add_all(default_hours)
        db.commit()
        # 重新查詢以獲取新創建的數據
        business_hours_from_db = db.query(models.BusinessHour).order_by(models.BusinessHour.day_of_week).all()

    # 標準化輸出，確保 day_of_week 永遠是 1-7
    standardized_hours = []
    if len(business_hours_from_db) == 7:
        for i, hour_model in enumerate(business_hours_from_db):
            # ISO 8601 標準: 星期一=1, 星期日=7
            day_of_week_standard = i + 1
            standardized_hours.append({
                "id": day_of_week_standard,
                "day_of_week": day_of_week_standard,
                "open_time": hour_model.open_time.strftime('%H:%M:%S') if hour_model.open_time else None,
                "close_time": hour_model.close_time.strftime('%H:%M:%S') if hour_model.close_time else None,
                "is_closed": hour_model.is_closed
            })

    return {
        "business_hours": standardized_hours,
        "holidays": holidays,
        "unavailable_dates": unavailable_dates,
        "bookable_time_slots": bookable_time_slots,
    }

@business_settings_router.put("/", response_model=schemas.BusinessSettingsResponse)
async def update_business_settings(settings: schemas.BusinessSettingsUpdate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    # 更新營業時間
    if settings.business_hours is not None:
        db.query(models.BusinessHour).delete()
        for hour in settings.business_hours:
            db_hour = models.BusinessHour(**hour.model_dump())
            db.add(db_hour)

    # 更新假日
    if settings.holidays is not None:
        db.query(models.Holiday).delete()
        for holiday in settings.holidays:
            db_holiday = models.Holiday(**holiday.model_dump())
            db.add(db_holiday)

    # 更新不可預約日期
    if settings.unavailable_dates is not None:
        db.query(models.UnavailableDate).delete()
        for unavailable_date in settings.unavailable_dates:
            db_unavailable_date = models.UnavailableDate(**unavailable_date.model_dump())
            db.add(db_unavailable_date)

    db.commit()
    db.refresh(current_user) # 刷新 current_user 以確保其是最新的

    # 返回更新後的完整設定
    business_hours = db.query(models.BusinessHour).all()
    holidays = db.query(models.Holiday).all()
    unavailable_dates = db.query(models.UnavailableDate).all()
    bookable_time_slots = db.query(models.BookableTimeSlot).all()
    
    return schemas.BusinessSettingsResponse(
        business_hours=business_hours,
        holidays=holidays,
        unavailable_dates=unavailable_dates,
        bookable_time_slots=bookable_time_slots
    )

@business_settings_router.put("/business-hours", response_model=List[schemas.BusinessHourResponse])
async def update_business_hours(hours: List[schemas.BusinessHourCreate], db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    # 簡單的更新邏輯：先刪除所有舊的，再新增新的
    db.query(models.BusinessHour).delete()
    db.commit()
    
    new_hours = []
    for hour in hours:
        db_hour = models.BusinessHour(**hour.model_dump())
        db.add(db_hour)
        new_hours.append(db_hour)
    db.commit()
    return new_hours

@business_settings_router.post("/holidays", response_model=schemas.HolidayResponse, status_code=status.HTTP_201_CREATED)
async def add_holiday(holiday: schemas.HolidayCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_holiday = db.query(models.Holiday).filter(models.Holiday.date == holiday.date).first()
    if db_holiday:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Holiday already exists for this date")
    
    db_holiday = models.Holiday(**holiday.model_dump())
    db.add(db_holiday)
    db.commit()
    db.refresh(db_holiday)
    return db_holiday

@business_settings_router.delete("/holidays/{holiday_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holiday(holiday_date: date, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_holiday = db.query(models.Holiday).filter(models.Holiday.date == holiday_date).first()
    if db_holiday is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    
    db.delete(db_holiday)
    db.commit()
    return

@business_settings_router.post("/unavailable-dates", response_model=schemas.UnavailableDateResponse, status_code=status.HTTP_201_CREATED)
async def add_unavailable_date(unavailable_date: schemas.UnavailableDateCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_unavailable_date = db.query(models.UnavailableDate).filter(models.UnavailableDate.date == unavailable_date.date).first()
    if db_unavailable_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unavailable date already exists")
    
    db_unavailable_date = models.UnavailableDate(**unavailable_date.model_dump())
    db.add(db_unavailable_date)
    db.commit()
    db.refresh(db_unavailable_date)
    return db_unavailable_date

@business_settings_router.delete("/unavailable-dates/{unavailable_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unavailable_date(unavailable_date: date, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_unavailable_date = db.query(models.UnavailableDate).filter(models.UnavailableDate.date == unavailable_date).first()
    if db_unavailable_date is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unavailable date not found")
    
    db.delete(db_unavailable_date)
    db.commit()
    return

@business_settings_router.post("/time-slots", response_model=schemas.BookableTimeSlotResponse, status_code=status.HTTP_201_CREATED)
async def add_time_slot(time_slot: schemas.BookableTimeSlotCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_time_slot = models.BookableTimeSlot(**time_slot.model_dump())
    db.add(db_time_slot)
    db.commit()
    db.refresh(db_time_slot)
    return db_time_slot

@business_settings_router.delete("/time-slots/{time_slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_time_slot(time_slot_id: int, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_time_slot = db.query(models.BookableTimeSlot).filter(models.BookableTimeSlot.id == time_slot_id).first()
    if db_time_slot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time slot not found")
    
    db.delete(db_time_slot)
    db.commit()
    return

app.include_router(business_settings_router)

# 使用者個人資料路由
user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@user_router.put("/me", response_model=schemas.UserResponse)
async def update_user_me(user_update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@user_router.post("/me/change-password")
async def change_password_me(password_update: schemas.PasswordUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not verify_password(password_update.current_password, current_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
    
    hashed_password = get_password_hash(password_update.new_password)
    current_user.password = hashed_password
    db.add(current_user)
    db.commit()
    
    return {"message": "Password updated successfully"}

app.include_router(user_router)

@app.get("/")
async def read_root():
    return {"message": "Hello from FastAPI backend!"}
