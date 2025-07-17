from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List, Optional
from datetime import date, datetime, time, timedelta
from jose import JWTError, jwt
from fastapi.security import HTTPBearer

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
    },
    security=[{"BearerAuth": []}]
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

def get_current_user(credentials: HTTPBearer = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials # 從 HTTPBearer 獲取 token 字串
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub") # 這裡也需要是字串
        print(f"Payload sub: {user_id}, type: {type(user_id)}") # 新增偵錯輸出
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        print(f"JWTError occurred: {e}")
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == int(user_id)).first() # 轉換回整數
    print(f"User retrieved from DB in get_current_user: {user}")
    if user is None:
        raise credentials_exception
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
async def login_for_access_token(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
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
    db_service = models.Service(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@service_router.put("/{service_id}", response_model=schemas.ServiceResponse)
async def update_service(service_id: int, service: schemas.ServiceCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if db_service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    for key, value in service.model_dump().items():
        setattr(db_service, key, value)
    
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

app.include_router(service_router)

# 預約路由
booking_router = APIRouter(prefix="/bookings", tags=["Bookings"])

@booking_router.post("/", response_model=schemas.BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_user)):
    # 確保 user_id 與當前登入用戶匹配
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create booking for another user")
    
    # 檢查 service_id 是否存在
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    # TODO: 檢查預約時間是否可用 (例如：營業時間內，沒有衝突)
    db_booking = models.Booking(**booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

@booking_router.get("/my", response_model=List[schemas.BookingResponse])
async def get_my_bookings(db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_user)):
    bookings = db.query(models.Booking).filter(models.Booking.user_id == current_user.id).all()
    return bookings

@booking_router.get("/", response_model=List[schemas.BookingResponse])
async def get_all_bookings(db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    bookings = db.query(models.Booking).all()
    return bookings

@booking_router.put("/{booking_id}/status", response_model=schemas.BookingResponse)
async def update_booking_status(booking_id: int, status: str, db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    db_booking.status = status
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
async def get_business_settings(db: Session = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_admin_user)):
    business_hours = db.query(models.BusinessHour).all()
    holidays = db.query(models.Holiday).all()
    unavailable_dates = db.query(models.UnavailableDate).all()
    
    return schemas.BusinessSettingsResponse(
        business_hours=business_hours,
        holidays=holidays,
        unavailable_dates=unavailable_dates
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

app.include_router(business_settings_router)

@app.get("/")
async def read_root():
    return {"message": "Hello from FastAPI backend!"}
