from database import Base
from sqlalchemy import Column , String , Integer , Boolean , DateTime , Float
from datetime import datetime



class WeatherApp(Base):
    __tablename__ = "weather"
    id = Column(Integer , primary_key=True , index=True)
    city = Column(String , index=True)
   
    description = Column(String)
    temperature = Column(Float)
    last_updated = Column(DateTime , default=datetime.utcnow)
 