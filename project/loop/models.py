from sqlalchemy import Column, Integer, String, DateTime, Time, Float
from sqlalchemy.orm import relationship

import datetime
from project.database import Base



class StoreStatus(Base):
    __tablename__ = "store_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(128), default='False')


class StoreMenuHours(Base):
    __tablename__ = "store_menu_hours"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, default=0)
    dayofweek = Column(Integer, default=0)
    start_time_local = Column(Time, default=datetime.time)
    end_time_local = Column(Time, default=datetime.time)


class StoreTimeZones(Base):
    __tablename__ = "store_timezones"
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, default=0)
    status = Column(String(300), default='America/Chicago')


class Report(Base):
    __tablename__ = "report"
    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(128), default='Open')
    report_data = relationship(
        "ReportData",
        cascade="all,delete-orphan",
        back_populates="report",
        uselist=True,
    )


class ReportData(Base):
    __tablename__ = "report_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(Integer, default=0, unique=True)
    uptime_last_hour = Column(Float, default=0.0, precision=1)
    uptime_last_day = Column(Float, default=0.0, precision=1)
    uptime_last_week = Column(Float, default=0.0, precision=1)
    downtime_last_hour = Column(Float, default=0.0, precision=1)
    downtime_last_day = Column(Float, default=0.0, precision=1)
    downtime_last_week = Column(Float, default=0.0, precision=1)
    downtime_last_week = Column(Float, default=0.0, precision=1)
    report = relationship("Report", back_populates="report_data")

