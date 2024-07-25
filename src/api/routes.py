from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import aiofiles
import os
from src.orchestrator import Orchestrator
from src.config import get_settings
from src.models.resume import ResumeContent
import uuid
import logfire

router = APIRouter()
settings = get_settings()
templates = Jinja2Templates(directory="templates")

orchestrator = Orchestrator(settings.get_llm_client(), settings.SERPER_API_KEY,
                            settings.GITHUB_API_KEY)

# Dictionary to store generated resumes
generated_resumes = {}


@router.post("/customize-resume", response_class=HTMLResponse)
async def customize_resume(request: Request,
                           job_url: str = Form(...),
                           linkedin_url: str = Form(...),
                           github_url: str = Form(None),
                           resume_file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_path = os.path.join(settings.UPLOAD_DIR, resume_file.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await resume_file.read()
            await out_file.write(content)

        # Process the resume
        customized_resume: ResumeContent = await orchestrator.process_resume_request(
            job_url, linkedin_url, file_path, github_url)

        # Clean up the uploaded file
        os.remove(file_path)

        # Generate a unique ID for this resume
        resume_id = str(uuid.uuid4())

        # Store the generated resume
        generated_resumes[resume_id] = customized_resume

        # Render the result template
        return templates.TemplateResponse(
            "resume_result.html", {
                "request": request,
                "resume_html": customized_resume.html_content,
                "resume_id": resume_id
            })

    except Exception as e:
        logfire.error("Error during resume customization", error=str(e))
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": str(e)
        },
                                          status_code=500)


@router.get("/download-resume/{resume_id}")
async def download_resume(resume_id: str):
    if resume_id not in generated_resumes:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_content = generated_resumes[resume_id]

    # Create a temporary file
    temp_file_path = f"/tmp/{resume_id}.md"
    with open(temp_file_path, "w") as f:
        f.write(resume_content.markdown_content)

    # Serve the file
    return FileResponse(temp_file_path,
                        media_type="text/markdown",
                        filename="customized_resume.md")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
