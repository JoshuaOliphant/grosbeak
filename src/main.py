import logfire
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.api.routes import router
from src.config import load_config

# Initialize Logfire
logfire.configure()

app = FastAPI()

# Set up templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(router)

# Load configuration
config = load_config()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
