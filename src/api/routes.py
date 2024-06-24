from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from src.orchestrator import Orchestrator
from src.config import load_config

router = APIRouter()
templates = Jinja2Templates(directory="templates")
config = load_config()
orchestrator = Orchestrator(
    llm_client=config.get_llm_client(),
    serper_api_key=config.SERPER_API_KEY,
    github_api_key=config.GITHUB_API_KEY
)

@router.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/customize-resume")
async def customize_resume(
    request: Request,
    job_url: str = Form(...),
    linkedin_url: str = Form(...),
    github_url: str = Form(None),
    resume_file: UploadFile = File(...)
):
    # Save the uploaded resume file
    resume_path = f"uploads/{resume_file.filename}"
    with open(resume_path, "wb") as buffer:
        buffer.write(await resume_file.read())

    # Process the resume
    try:
        final_resume = await orchestrator.process_resume_request(
            job_url, linkedin_url, resume_path, github_url
        )
        return templates.TemplateResponse("resume_result.html", {
            "request": request,
            "resume_content": final_resume
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": str(e)
        })