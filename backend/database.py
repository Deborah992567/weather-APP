from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


URL_DATABASE = 'postgresql://weatherapp_q104_user:9jQeAZMgaU1DqWGDemBLjdRS9AV2fXz3@dpg-d2hhq1v5r7bs7384bcpg-a:5432/weatherapp_q104'

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autoflush=False , autocommit=False , bind= engine)

Base = declarative_base()