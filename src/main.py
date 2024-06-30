from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.api.routes import router
from src.config import get_settings
import logfire

app = FastAPI()
settings = get_settings()
logfire.configure()

# Include the router
app.include_router(router)

# Initialize templates
templates = Jinja2Templates(directory="templates")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)