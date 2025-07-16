from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List
from datetime import date, datetime

from database import engine, Base, get_db
import models, schemas

app = FastAPI()

# 創建所有資料庫表格
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

# 密碼雜湊上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    # 在實際應用中，這裡會生成 JWT Token
    return {"message": "Login successful", "user_id": db_user.id, "user_role": db_user.role}

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
async def create_service(service: schemas.ServiceCreate, db: Session = Depends(get_db)):
    # TODO: 這裡需要添加管理員權限驗證
    db_service = models.Service(**service.model_dump())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@service_router.put("/{service_id}", response_model=schemas.ServiceResponse)
async def update_service(service_id: int, service: schemas.ServiceCreate, db: Session = Depends(get_db)):
    # TODO: 這裡需要添加管理員權限驗證
    db_service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if db_service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    for key, value in service.model_dump().items():
        setattr(db_service, key, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service

@service_router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: int, db: Session = Depends(get_db)):
    # TODO: 這裡需要添加管理員權限驗證
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
async def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    # TODO: 這裡需要添加用戶認證，並確保 user_id 與當前登入用戶匹配
    # TODO: 檢查 service_id 是否存在
    # TODO: 檢查預約時間是否可用 (例如：營業時間內，沒有衝突)
    db_booking = models.Booking(**booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

@booking_router.get("/my", response_model=List[schemas.BookingResponse])
async def get_my_bookings(user_id: int, db: Session = Depends(get_db)): # TODO: user_id 應該從認證中獲取
    bookings = db.query(models.Booking).filter(models.Booking.user_id == user_id).all()
    return bookings

@booking_router.get("/", response_model=List[schemas.BookingResponse])
async def get_all_bookings(db: Session = Depends(get_db)):
    # TODO: 這裡需要添加管理員權限驗證
    bookings = db.query(models.Booking).all()
    return bookings

@booking_router.put("/{booking_id}/status", response_model=schemas.BookingResponse)
async def update_booking_status(booking_id: int, status: str, db: Session = Depends(get_db)):
    # TODO: 這裡需要添加管理員權限驗證
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    db_booking.status = status
    db.commit()
    db.refresh(db_booking)
    return db_booking

@booking_router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    # TODO: 這裡需要添加管理員權限驗證
    db_booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if db_booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    
    db.delete(db_booking)
    db.commit()
    return

app.include_router(booking_router)

@app.get("/")
async def read_root():
    return {"message": "Hello from FastAPI backend!"}
