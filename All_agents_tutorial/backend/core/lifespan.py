from contextlib import asynccontextmanager
from data.loader import load_csv_data, DB_PATH
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    connection,_ = load_csv_data(DB_PATH)
    connection.close()
    yield
    