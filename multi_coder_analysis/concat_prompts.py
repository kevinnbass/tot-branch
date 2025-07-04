import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Union
import argparse

# Default prompts directory relative to this file (package prompts)
_DEFAULT_PROMPTS_DIR = Path(__file__).parent / "prompts"

def concatenate_prompts(
    prompts_dir: Union[str, Path] = _DEFAULT_PROMPTS_DIR,
    output_file: str = "concatenated_prompts.txt",
    target_dir: Optional[Union[str, Path]] = None,
):
    """
    Concatenates all text files in the prompts directory into a single file.
    
    Args:
        prompts_dir (str | Path): Directory containing prompt files
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
                        
                        # Footer is added during live prompt construction; omit here for cleaner concatenation
                        
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
    parser = argparse.ArgumentParser(description="Concatenate prompt text files into a single file.")
    parser.add_argument("--prompts-dir", default=str(_DEFAULT_PROMPTS_DIR), help="Directory containing prompt .txt files")
    parser.add_argument("--out", dest="output_path", help="Output file path. If omitted, writes to ./concatenated_prompts/<timestamp>.txt inside current working directory.")
    parser.add_argument("--dest-dir", help="Destination folder for the concatenated file (ignored if --out is absolute)")

    args = parser.parse_args()

    # Determine output file and directory
    if args.output_path:
        out_path = Path(args.output_path)
        dest_dir = out_path.parent
        out_name = out_path.name
    else:
        dest_dir = Path(args.dest_dir) if args.dest_dir else None
        out_name = f"concatenated_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    result = concatenate_prompts(args.prompts_dir, out_name, dest_dir)
    if result:
        print(f"Concatenation successful: {result}")
    else:
        print("Concatenation failed")

if __name__ == "__main__":
    main() 