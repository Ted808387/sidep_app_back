from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date, time
from typing import Optional

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6) # 密碼至少6位
    role: Optional[str] = "customer"

class UserResponse(UserBase):
    id: int
    role: str
    registration_date: datetime

    class Config:
        from_attributes = True # 允許從 ORM 對象創建 Pydantic 模型

# Service Schemas
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    duration: int # 服務所需時間，單位分鐘
    is_active: Optional[bool] = True
    category: Optional[str] = None
    image_url: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: int

    class Config:
        from_attributes = True

# Booking Schemas
class BookingBase(BaseModel):
    user_id: int
    service_id: int
    date: date # 僅日期部分
    time: str # 儲存時間字串，例如 "10:00"
    status: Optional[str] = "pending"
    notes: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Business Settings Schemas
class BusinessHourBase(BaseModel):
    day_of_week: int # 0=Monday, 6=Sunday
    open_time: time
    close_time: time

class BusinessHourCreate(BusinessHourBase):
    pass

class BusinessHourResponse(BusinessHourBase):
    id: int

    class Config:
        from_attributes = True

class HolidayBase(BaseModel):
    date: date
    description: Optional[str] = None

class HolidayCreate(HolidayBase):
    pass

class HolidayResponse(HolidayBase):
    id: int

    class Config:
        from_attributes = True

class UnavailableDateBase(BaseModel):
    date: date
    reason: Optional[str] = None

class UnavailableDateCreate(UnavailableDateBase):
    pass

class UnavailableDateResponse(UnavailableDateBase):
    id: int

    class Config:
        from_attributes = True
