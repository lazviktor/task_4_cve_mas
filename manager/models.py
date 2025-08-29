from sqlalchemy import Column, Integer, String
from .database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, index=True)
    vulnerabilities = Column(String, nullable=True)
    analysis = Column(String, nullable=True)
