# def main():
#     print("Hello from all-agents-tutorial!")


# if __name__ == "__main__":
#     main()

from fastapi import FastAPI
from backend.api.router import api_router
from backend.core.lifespan import lifespan
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="All Agents Tutorial API",
    description="API for the All Agents Tutorial project",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
