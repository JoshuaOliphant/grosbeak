import markdown


class ResumeContent:

    def __init__(self, content: str):
        self.markdown_content = content

    @property
    def html_content(self) -> str:
        return markdown.markdown(self.markdown_content)
