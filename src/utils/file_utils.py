import markdown
import aiofiles
async def read_resume_file(self, file_path: str) -> str:
    try:
        async with aiofiles.open(file_path, mode="r") as file:
            file_content = await file.read()
            return markdown.markdown(file_content)
    except IOError as e:
        raise ValueError(
            f"Unable to read resume file at {file_path}: {str(e)}")