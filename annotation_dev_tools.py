from typing import Union, Path

class AnnotationDevTools:
    def __init__(self, project_root: Union[str, Path]):
        self.project_root = Path(project_root) if isinstance(project_root, str) else project_root
        self.regex_file = self.project_root / "data" / "regex" / "hop_patterns.yml"
        self.prompts_dir = self.project_root / "data" / "prompts" 