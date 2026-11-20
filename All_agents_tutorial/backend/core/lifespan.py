from contextlib import asynccontextmanager
from data.loader import load_csv_data
from fastapi import FastAPI
from agent.persistence.database import initialize_database
from pathlib import Path


data_dir = Path("data/ecommerce_demo")

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    connection,_ = load_csv_data(data_dir)
    connection.close()
    yield
    