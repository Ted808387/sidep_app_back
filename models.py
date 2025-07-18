from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base # 從 database.py 導入 Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False) # 儲存雜湊後的密碼
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    role = Column(String, default="customer") # customer 或 admin
    registration_date = Column(DateTime(timezone=True), server_default=func.now())

    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    min_duration = Column(Integer, nullable=False) # 服務所需最短時間，單位分鐘
    max_duration = Column(Integer, nullable=False) # 服務所需最長時間，單位分鐘
    is_active = Column(Boolean, default=True) # 是否上架
    category = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    bookings = relationship("Booking", back_populates="service")

    def __repr__ (self):
        return f"<Service(id={self.id}, name={self.name}, price={self.price})>"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    time = Column(String, nullable=False) # 儲存時間字串，例如 "10:00"
    status = Column(String, default="pending") # pending, confirmed, cancelled, completed
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")

    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, service_id={self.service_id}, date={self.date}, status={self.status})>"

class BusinessHour(Base):
    __tablename__ = "business_hours"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(Integer, nullable=False) # 0=Monday, 6=Sunday
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)
    is_closed = Column(Boolean, default=False) # 新增欄位，表示當天是否休息

    def __repr__(self):
        return f"<BusinessHour(id={self.id}, day_of_week={self.day_of_week}, open_time={self.open_time}, close_time={self.close_time})>"

class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, nullable=False)
    description = Column(String, nullable=True)

    def __repr__(self):
        return f"<Holiday(id={self.id}, date={self.date}, description={self.description})>"

class UnavailableDate(Base):
    __tablename__ = "unavailable_dates"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, nullable=False)
    reason = Column(String, nullable=True)

    def __repr__(self):
        return f"<UnavailableDate(id={self.id}, date={self.date}, reason={self.reason})>"

class BookableTimeSlot(Base):
    __tablename__ = "bookable_time_slots"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    def __repr__(self):
        return f"<BookableTimeSlot(id={self.id}, start_time={self.start_time}, end_time={self.end_time})>"
