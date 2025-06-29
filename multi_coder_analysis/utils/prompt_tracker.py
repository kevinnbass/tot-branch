"""Track which prompts are used during a pipeline run."""
from pathlib import Path
from typing import Set, Optional
import logging
import shutil
import threading

class PromptTracker:
    """Track prompts used during a pipeline run."""
    
    def __init__(self):
        self.used_prompts: Set[Path] = set()
        self._lock = threading.Lock()
    
    def track_prompt(self, prompt_path: Path) -> None:
        """Record that a prompt file was used."""
        with self._lock:
            self.used_prompts.add(prompt_path)
            logging.debug(f"Tracked prompt usage: {prompt_path.name}")
    
    def copy_used_prompts(self, src_dir: Path, dst_dir: Path) -> None:
        """Copy only the prompts that were actually used."""
        dst_dir.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            if not self.used_prompts:
                logging.warning("No prompts were tracked as used")
                return
                
            logging.info(f"Copying {len(self.used_prompts)} used prompts to {dst_dir}")
            
            for prompt_path in self.used_prompts:
                try:
                    # Get relative path from src_dir
                    if prompt_path.is_absolute():
                        try:
                            rel_path = prompt_path.relative_to(src_dir)
                        except ValueError:
                            # If not relative to src_dir, just use the filename
                            rel_path = prompt_path.name
                    else:
                        rel_path = prompt_path
                    
                    dst_path = dst_dir / rel_path
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if prompt_path.exists():
                        shutil.copy2(prompt_path, dst_path)
                        logging.debug(f"Copied {prompt_path.name} to {dst_path}")
                    else:
                        logging.warning(f"Prompt file not found: {prompt_path}")
                        
                except Exception as e:
                    logging.error(f"Error copying prompt {prompt_path}: {e}")
    
    def get_used_prompt_names(self) -> Set[str]:
        """Get the names of all used prompts."""
        with self._lock:
            return {p.name for p in self.used_prompts}

# Global tracker instance
_global_tracker: Optional[PromptTracker] = None

def get_prompt_tracker() -> PromptTracker:
    """Get the global prompt tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = PromptTracker()
    return _global_tracker

def reset_prompt_tracker() -> None:
    """Reset the global prompt tracker."""
    global _global_tracker
    _global_tracker = PromptTracker() 