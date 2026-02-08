from sqlalchemy import BigInteger, String, ForeignKey, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String(32))
    full_name: Mapped[str | None] = mapped_column(String(128))
    reg_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class ConversionLog(Base):
    __tablename__ = 'conversion_logs'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.tg_id', ondelete='CASCADE'))
    file_type: Mapped[str] = mapped_column(String(20))  # Например: "jpg_to_pdf"
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())