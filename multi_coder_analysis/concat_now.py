#!/usr/bin/env python3
"""
Quick helper script to concatenate all prompt files on demand.
Usage: python concat_now.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def main():
    print("🔄 Concatenating prompt files...")
    
    # Check if prompts directory exists
    prompts_dir = Path("prompts")
    if not prompts_dir.exists():
        print("❌ Error: 'prompts' directory not found!")
        print(f"   Current directory: {Path.cwd()}")
        print("   Make sure you're running this from the multi_coder_analysis directory.")
        sys.exit(1)
    
    # Get all .txt files, sorted
    prompt_files = sorted(prompts_dir.glob("*.txt"))
    
    if not prompt_files:
        print("⚠️  No .txt files found in prompts directory!")
        sys.exit(1)
    
    # Create dedicated output directory
    output_dir = Path("concatenated_prompts")
    output_dir.mkdir(exist_ok=True)
    
    # Load global footer for appending to hop files
    global_footer_path = prompts_dir / "GLOBAL_FOOTER.txt"
    global_footer = ""
    if global_footer_path.exists():
        global_footer = global_footer_path.read_text(encoding='utf-8')
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"concatenated_prompts_{timestamp}.txt"
    
    print(f"📁 Found {len(prompt_files)} prompt files:")
    for f in prompt_files:
        print(f"   • {f.name}")
    
    print(f"📝 Writing to: {output_file}")
    
    # Create concatenated file
    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Header
            outfile.write(f"# Concatenated Prompts - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            outfile.write("=" * 80 + "\n\n")
            
            # Process each file
            for i, prompt_file in enumerate(prompt_files):
                print(f"   Adding: {prompt_file.name}")
                
                # File separator
                outfile.write(f"## File {i+1}: {prompt_file.name}\n")
                outfile.write("-" * 60 + "\n")
                
                # File content
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
                    print(f"   ⚠️  Warning: Could not read {prompt_file.name}: {e}")
                    outfile.write(f"[ERROR: Could not read {prompt_file.name}]\n\n")
            
            # Footer
            outfile.write("=" * 80 + "\n")
            outfile.write(f"# End of concatenated prompts ({len(prompt_files)} files)\n")
        
        # Success message
        file_size = Path(output_file).stat().st_size
        print(f"✅ Success! Concatenated {len(prompt_files)} files")
        print(f"📄 Output: {output_file} ({file_size:,} bytes)")
        
    except Exception as e:
        print(f"❌ Error creating concatenated file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 