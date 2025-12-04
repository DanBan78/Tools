import re
from pathlib import Path
import sys
import os
from datetime import datetime
import subprocess
from colorama import Fore, Style, init

# Initialize colorama
init()

# Get script directory for relative paths
SCRIPT_DIR = Path(__file__).parent.absolute()

# ===== KONFIGURACJA - ZMIEŃ ŚCIEŻKI WEDŁUG POTRZEB =====
BEYOND_COMPARE_PATH = r"C:\Users\dban\AppData\Local\Programs\Beyond Compare 5\BCompare.exe"
FOLDER_WZORCOWY_PATH = r"C:\.temp\results\2025-12-04--17-22-44_results_ORYGINALNY_LUKASZ"
REPORT_OUTPUT_PATH = SCRIPT_DIR / "__report.txt"
# ========================================================

# Extract counts from report headings (Beyond Compare):
SECTION_PATTERNS = {
    "Right Orphan Files": re.compile(r"^\s*Right\s+Orphan\s+Files\s*\((\d+)\).*", re.IGNORECASE | re.MULTILINE),
    "Left Orphan Files": re.compile(r"^\s*Left\s+Orphan\s+Files\s*\((\d+)\).*", re.IGNORECASE | re.MULTILINE),
    "Difference Files": re.compile(r"^\s*Difference\s+Files\s*\((\d+)\).*", re.IGNORECASE | re.MULTILINE),
}


def parse_counts(text: str):
    counts = {}
    for name, pattern in SECTION_PATTERNS.items():
        m = pattern.search(text)
        counts[name] = int(m.group(1)) if m else 0
    return counts


def extract_file_details(section_name, content):
    # Extract file details for a given section
    section_start = re.search(rf"^\s*{section_name}\s*\(\d+\).*", content, re.IGNORECASE | re.MULTILINE)
    if not section_start:
        # print(f"Section '{section_name}' not found in the report.")  # Debugging
        return []

    section_lines = content[section_start.end():].splitlines()
    # print(f"Debug: Lines after section '{section_name}':")  # Debugging
    # print(section_lines)  # Debugging

    files = []
    for line in section_lines:
        line = line.strip()
        if not line or line.startswith("----------------------------------------------"):
            break
        if re.match(r"^\S", line):  # Match non-empty lines starting with a non-whitespace character
            files.append(line)
    # print(f"Debug: Extracted files for section '{section_name}': {files}")  # Debugging
    return files


def log_test_result(left_folder, right_folder, result):
    log_path = SCRIPT_DIR / "log.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Debug: Log the folder paths being used
    # print(f"Debug: Logging result - Left: {left_folder}, Right: {right_folder}, Result: {result}")

    log_entry = f"{timestamp} | Left: {left_folder} | Right: {right_folder} | Result: {result}\n"
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(log_entry)


def run_beyond_compare():
    script_upd_path = SCRIPT_DIR / "script_upd.txt"
    bc_command = [
        BEYOND_COMPARE_PATH,
        f"@{script_upd_path}"
    ]
    
    # Show only the load command from script_upd.txt
    try:
        script_content = script_upd_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading script_upd.txt: {e}\n")
    
    try:
        subprocess.run(bc_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Beyond Compare: {e}")
        sys.exit(1)


def update_report(report_path, counts):
    content = report_path.read_text(encoding="utf-8")

    # print("Original report content:")
    # print(content)  # Debugging output to verify the original content

    # Update section headers with translated labels
    content = re.sub(r"Left Orphan Files", "Braki w folderze", content)
    content = re.sub(r"Right Orphan Files", "Nowe w folderze", content)
    content = re.sub(r"Difference Files", "Pliki zmienione", content)

    # Remove the "Left Newer Files" and "Right Newer Files" sections
    content = re.sub(r"Left Newer Files \(0\).*?----------------------------------------------\n\n", "", content, flags=re.DOTALL)
    content = re.sub(r"Right Newer Files \(0\).*?----------------------------------------------\n\n", "", content, flags=re.DOTALL)
    
    # Remove "Size" and "Modified" column headers
    content = re.sub(r"\s+Size\s+Modified", "", content)
    content = re.sub(r"\s+Size\s+Modified\s*\n", "\n", content)
    
    # Reformat folder paths
    content = re.sub(r"Left base folder:\s*(.*)", r"\nFolder wzorca:\n\1", content)
    content = re.sub(r"Right base folder:\s*(.*)", r"\nBiezace porownanie:\n\1", content)

    # Replace the "Summary of Analysis" section
    summary = (
        "Summary of Analysis:\n"
        f"Braki w folderze (Left Orphan Files): {counts.get('Left Orphan Files', 0)}\n"
        f"Nowe w folderze (Right Orphan Files): {counts.get('Right Orphan Files', 0)}\n"
        f"Pliki zmienione (Difference Files): {counts.get('Difference Files', 0)}\n"
    )
    content = re.sub(r"Summary of Analysis:.*", summary, content, flags=re.DOTALL)

    # print("Modified report content:")
    # print(content)  # Debugging output to verify the modified content

    # Write the updated content back to the report
    report_path.write_text(content, encoding="utf-8")

    # Automatically verify the updated report
    # print("Updated report content saved to file:")
    # print(report_path.read_text(encoding="utf-8"))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Process Beyond Compare reports.")
    parser.add_argument("-c", "--compare", type=str, help="Path to the right folder for comparison.")
    args = parser.parse_args()

    if args.compare:
        # Read script.txt
        script_path = SCRIPT_DIR / "script.txt"
        if script_path.exists():
            lines = script_path.read_text(encoding="utf-8").splitlines()
            # Find the load line and append the right folder path to it
            # Update paths in script template
            for i, line in enumerate(lines):
                if line.strip().startswith("load") and "temp" in line:
                    lines[i] = f'load "{FOLDER_WZORCOWY_PATH}" "{args.compare}"'
                    break
                elif "output-to:" in line:
                    lines[i] = re.sub(r'output-to:"[^"]*"', f'output-to:"{REPORT_OUTPUT_PATH}"', line)
            # Save as script_upd.txt
            upd_script_path = SCRIPT_DIR / "script_upd.txt"
            with upd_script_path.open("w", encoding="utf-8") as file:
                file.write("\n".join(lines))
        else:
            print("script.txt not found.")
            sys.exit(1)

    # Run Beyond Compare before analyzing the report
    run_beyond_compare()

    report_path = SCRIPT_DIR / "__report.txt"
    if not report_path.exists():
        print(f"report missing: {report_path}")
        sys.exit(1)

    # Try UTF-8 first; if empty, fall back to cp1250 which is common for PL Windows
    content = report_path.read_text(encoding="utf-8", errors="ignore")
    if not content.strip():
        try:
            content = report_path.read_text(encoding="cp1250", errors="ignore")
        except Exception:
            pass

    counts = parse_counts(content)

    # Update the report with analysis summary
    update_report(report_path, counts)

    # Extract left and right folder names from the report header
    left_folder = "Unknown"
    right_folder = "Unknown"
    header_match = re.search(r"Left base folder:\s*(.*)\nRight base folder:\s*(.*)\n", content, re.IGNORECASE)
    if header_match:
        left_folder, right_folder = header_match.groups()
    else:
        # Fallback: if not found, use base folder and args.compare
        base_match = re.search(r"Base folder:\s*(.*)", content, re.IGNORECASE)
        if base_match:
            left_folder = base_match.group(1).strip()
        right_folder = args.compare if args.compare else "Unknown"

    order = ["Right Orphan Files", "Left Orphan Files", "Difference Files"]
    non_zero = [(k, counts[k]) for k in order if counts.get(k, 0) != 0]
    if non_zero:
        for k, v in non_zero:
            # Print with standardized labels as requested
            if k == "Right Orphan Files":
                print(f"{Fore.RED}Brakujace pliki: {v}{Style.RESET_ALL}")
            elif k == "Left Orphan Files":
                print(f"{Fore.RED}Nowe pliki: {v}{Style.RESET_ALL}")
            elif k == "Difference Files":
                print(f"{Fore.RED}Pliki rozne: {v}{Style.RESET_ALL}")
        log_test_result(left_folder, right_folder, "Niezgodne")
        # print(f"script_upd.txt left in: {Path('script_upd.txt').absolute()}")
        input("\nNacisnij Enter aby zakonczyc...")
        sys.exit(2)
    else:
        print(f"{Fore.GREEN}Brak roznic!{Style.RESET_ALL}")
        log_test_result(left_folder, right_folder, "Zgodne")
        # print(f"script_upd.txt left in: {Path('script_upd.txt').absolute()}")
        input("\nNacisnij Enter aby zakonczyc...")
        sys.exit(0)


if __name__ == "__main__":
    main()

