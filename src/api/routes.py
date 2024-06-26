from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from src.orchestrator import Orchestrator
from src.config import load_config
import logfire

router = APIRouter()
templates = Jinja2Templates(directory="templates")
config = load_config()
orchestrator = Orchestrator(llm_client=config.get_llm_client(),
                            serper_api_key=config.SERPER_API_KEY,
                            github_api_key=config.GITHUB_API_KEY)

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
    try:
        logfire.info(f"Received request: job_url={job_url}, linkedin_url={linkedin_url}, github_url={github_url}")
        logfire.info(f"Resume file: {resume_file.filename}")

        # Save the uploaded resume file
        resume_path = f"uploads/{resume_file.filename}"
        contents = await resume_file.read()
        with open(resume_path, "wb") as f:
            f.write(contents)

        # Process the resume
        final_resume = await orchestrator.process_resume_request(
            job_url, linkedin_url, resume_path, github_url
        )

        # Check if it's an HTMX request
        is_htmx = request.headers.get("HX-Request") == "true"

        if is_htmx:
            # Return just the content for HTMX
            return HTMLResponse(content=templates.get_template("resume_result.html").render(
                request=request,
                resume_content=final_resume
            ))
        else:
            # Return full page for regular requests
            return templates.TemplateResponse("resume_result.html", {
                "request": request,
                "resume_content": final_resume
            })

    except ValueError as ve:
        logfire.error(f"Validation error: {str(ve)}")
        error_content = f"<p class='text-red-500'>Error: {str(ve)}</p>"
        if request.headers.get("HX-Request") == "true":
            return HTMLResponse(content=error_content, status_code=422)
        else:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": str(ve)
            }, status_code=422)

    except Exception as e:
        logfire.error(f"Unexpected error: {str(e)}")
        error_content = "<p class='text-red-500'>An unexpected error occurred. Please try again.</p>"
        if request.headers.get("HX-Request") == "true":
            return HTMLResponse(content=error_content, status_code=500)
        else:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error_message": str(e)
            }, status_code=500)