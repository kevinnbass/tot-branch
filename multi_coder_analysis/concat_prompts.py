import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

def concatenate_prompts(
    prompts_dir: str = "prompts",
    output_file: str = "concatenated_prompts.txt",
    target_dir: Optional[str | Path] = None,
):
    """
    Concatenates all text files in the prompts directory into a single file.
    
    Args:
        prompts_dir (str): Directory containing prompt files
        output_file (str): Name of the concatenated file.
        target_dir (str | Path | None): Directory where the file should be
            written. If None, a directory called "concatenated_prompts" is
            created alongside the script (legacy behaviour).
        
    Returns:
        str: Path to the concatenated prompts file
    """
    try:
        prompts_path = Path(prompts_dir)
        
        # Decide output directory
        if target_dir is None:
            dest_dir = Path("concatenated_prompts")
        else:
            dest_dir = Path(target_dir)

        dest_dir.mkdir(parents=True, exist_ok=True)

        output_path = dest_dir / output_file
        
        if not prompts_path.exists():
            logging.error(f"Prompts directory does not exist: {prompts_path}")
            return None
            
        # Get all .txt files in the prompts directory, sorted by name
        prompt_files = sorted(prompts_path.glob("*.txt"))
        
        # Load global footer for appending to hop files
        global_footer_path = prompts_path / "GLOBAL_FOOTER.txt"
        global_footer = ""
        if global_footer_path.exists():
            global_footer = global_footer_path.read_text(encoding='utf-8')
        
        if not prompt_files:
            logging.warning(f"No .txt files found in {prompts_path}")
            return None
            
        logging.info(f"Concatenating {len(prompt_files)} prompt files...")
        
        with open(output_path, 'w', encoding='utf-8') as outfile:
            # Write header with timestamp
            outfile.write(f"# Concatenated Prompts - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            outfile.write("=" * 80 + "\n\n")
            
            for i, prompt_file in enumerate(prompt_files):
                logging.info(f"  Adding: {prompt_file.name}")
                
                # Write file separator
                outfile.write(f"## File {i+1}: {prompt_file.name}\n")
                outfile.write("-" * 60 + "\n")
                
                # Read and write file content
                try:
                    with open(prompt_file, 'r', encoding='utf-8') as infile:
                        content = infile.read().strip()
                        outfile.write(content)
                        
                        # Append footer to hop files (files starting with "hop_")
                        if prompt_file.name.startswith("hop_") and global_footer:
                            outfile.write("\n\n")
                            outfile.write(global_footer)
                        
                        outfile.write("\n\n")
                except Exception as e:
                    logging.error(f"Error reading {prompt_file}: {e}")
                    outfile.write(f"[ERROR: Could not read {prompt_file.name}]\n\n")
                    
            # Write footer
            outfile.write("=" * 80 + "\n")
            outfile.write(f"# End of concatenated prompts ({len(prompt_files)} files)\n")
            
        logging.info(f"Prompts concatenated successfully to: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logging.error(f"Error concatenating prompts: {e}")
        return None

def main():
    """Standalone execution for testing"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    result = concatenate_prompts()
    if result:
        print(f"Concatenation successful: {result}")
    else:
        print("Concatenation failed")

if __name__ == "__main__":
    main() 