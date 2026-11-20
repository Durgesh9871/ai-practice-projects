# def main():
#     print("Hello from all-agents-tutorial!")


# if __name__ == "__main__":
#     main()

from fastapi import FastAPI
from backend.api.router import api_router
from backend.core.lifespan import lifespan


app = FastAPI(
    title="All Agents Tutorial API",
    description="API for the All Agents Tutorial project",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
