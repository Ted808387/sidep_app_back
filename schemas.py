from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date, time
from typing import Optional, List

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None # 新增 avatar_url

class UserCreate(UserBase):
    password: str = Field(..., min_length=6) # 密碼至少6位
    role: Optional[str] = "customer"

class UserResponse(UserBase):
    id: int
    role: str
    registration_date: datetime
    avatar_url: Optional[str] = None
    email_notifications_enabled: bool
    sms_notifications_enabled: bool

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    email_notifications_enabled: Optional[bool] = None
    sms_notifications_enabled: Optional[bool] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

# Service Schemas
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    min_duration: int # 服務所需最短時間，單位分鐘
    max_duration: int # 服務所需最長時間，單位分鐘
    is_active: Optional[bool] = True
    category: Optional[str] = None
    image_url: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: int
    minDuration: int = Field(..., alias="min_duration")
    maxDuration: int = Field(..., alias="max_duration")

    class Config:
        from_attributes = True

class ServiceStatusUpdate(BaseModel):
    is_active: bool

class BulkServiceActionRequest(BaseModel):
    action: str # e.g., "activate", "deactivate", "delete"
    service_ids: List[int]

# Booking Schemas
class BookingBase(BaseModel):
    user_id: Optional[int] = None # 允許為 None，表示匿名預約
    service_id: int
    date: date # 僅日期部分
    time: str # 儲存時間字串，例如 "10:00"
    status: Optional[str] = "pending"
    notes: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingResponse(BaseModel):
    id: int
    booking_reference_id: Optional[str] = None # 新增預約編號
    user_id: Optional[int] = None
    service_id: int
    date: date
    time: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    clientName: Optional[str] = None
    serviceName: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True

class BookingUpdate(BaseModel):
    notes: Optional[str] = None
    status: Optional[str] = None # 允許更新狀態

# Business Settings Schemas
class BusinessHourBase(BaseModel):
    day_of_week: int # 0=Monday, 6=Sunday
    open_time: time
    close_time: time
    is_closed: Optional[bool] = False

class BusinessHourCreate(BusinessHourBase):
    pass

class BusinessHourResponse(BusinessHourBase):
    id: int
    isClosed: bool = Field(..., alias="is_closed")

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

class UnavailableDateResponse(UnavailableDateBase):
    id: int

    class Config:
        from_attributes = True

class UnavailableDateResponse(UnavailableDateBase):
    id: int

    class Config:
        from_attributes = True

class BookableTimeSlotBase(BaseModel):
    start_time: time
    end_time: time

class BookableTimeSlotCreate(BookableTimeSlotBase):
    pass

class BookableTimeSlotResponse(BookableTimeSlotBase):
    id: int

    class Config:
        from_attributes = True

class BusinessSettingsUpdate(BaseModel):
    business_hours: Optional[List[BusinessHourCreate]] = None
    holidays: Optional[List[HolidayCreate]] = None
    unavailable_dates: Optional[List[UnavailableDateCreate]] = None
    bookable_time_slots: Optional[List[BookableTimeSlotCreate]] = None

class BusinessSettingsResponse(BaseModel):
    business_hours: List[BusinessHourResponse]
    holidays: List[HolidayResponse]
    unavailable_dates: List[UnavailableDateResponse]
    bookable_time_slots: List[BookableTimeSlotResponse] # 新增可預約時間段落

    class Config:
        from_attributes = True

class BlacklistedTokenBase(BaseModel):
    token: str

class BlacklistedTokenCreate(BlacklistedTokenBase):
    pass

class BlacklistedTokenResponse(BlacklistedTokenBase):
    id: int
    blacklisted_on: datetime

    class Config:
        from_attributes = True