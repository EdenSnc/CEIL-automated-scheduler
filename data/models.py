from typing import List, Optional
from sqlalchemy import String, Integer, ForeignKey, Float, Date, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

# Junction table for Teacher <-> Language
teacher_languages = Table(
    "teacher_languages",
    Base.metadata,
    Column("teacher_id", ForeignKey("teacher.teacher_id"), primary_key=True),
    Column("lang_id", ForeignKey("language.lang_id"), primary_key=True),
)

class Language(Base):
    __tablename__ = "language"
    lang_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

class Room(Base):
    __tablename__ = "room"
    room_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

class Teacher(Base):
    __tablename__ = "teacher"
    teacher_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    languages: Mapped[List["Language"]] = relationship(secondary="teacher_languages")
    preferences: Mapped[List["TeacherPref"]] = relationship(back_populates="teacher")

class Timeslot(Base):
    __tablename__ = "timeslot"
    slot_id: Mapped[int] = mapped_column(primary_key=True)
    day_of_week: Mapped[str] = mapped_column(String(10), nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)

class TeacherPref(Base):
    __tablename__ = "teacher_prefs"
    pref_id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.teacher_id"))
    slot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.slot_id"))
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    group_id: Mapped[Optional[int]] = mapped_column(ForeignKey("group.group_id"), nullable=True)
    
    teacher: Mapped["Teacher"] = relationship(back_populates="preferences")

class Group(Base):
    __tablename__ = "group"
    group_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    cefr_level: Mapped[str] = mapped_column(String(5), nullable=False)
    track_modifier: Mapped[str] = mapped_column(String(50), nullable=False)
    sessions_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    lang_id: Mapped[int] = mapped_column(ForeignKey("language.lang_id"))
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.teacher_id"))

class Session(Base):
    __tablename__ = "session"
    session_id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.group_id"))
    slot_id: Mapped[int] = mapped_column(ForeignKey("timeslot.slot_id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("room.room_id"))
    session_type: Mapped[str] = mapped_column(String(20), default="Recurrent") # 'Recurrent' or 'Makeup'
    calendar_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True) # ISO Date