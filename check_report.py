import re
from pathlib import Path
import sys
import os
from datetime import datetime
import subprocess


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
        print(f"Section '{section_name}' not found in the report.")  # Debugging
        return []

    section_lines = content[section_start.end():].splitlines()
    print(f"Debug: Lines after section '{section_name}':")  # Debugging
    print(section_lines)  # Debugging

    files = []
    for line in section_lines:
        line = line.strip()
        if not line or line.startswith("----------------------------------------------"):
            break
        if re.match(r"^\S", line):  # Match non-empty lines starting with a non-whitespace character
            files.append(line)
    print(f"Debug: Extracted files for section '{section_name}': {files}")  # Debugging
    return files


def log_test_result(left_folder, right_folder, result):
    log_path = Path("log.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | Left: {left_folder} | Right: {right_folder} | Result: {result}\n"
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(log_entry)


def run_beyond_compare():
    bc_command = [
        r"C:\\Users\\danie\\AppData\\Local\\Programs\\Beyond Compare 5\\BCompare.exe",
        "@script.txt"
    ]
    try:
        subprocess.run(bc_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Beyond Compare: {e}")
        sys.exit(1)


def update_report(report_path, counts):
    content = report_path.read_text(encoding="utf-8")

    print("Original report content:")
    print(content)  # Debugging output to verify the original content

    # Update section headers with translated labels
    content = re.sub(r"Left Orphan Files", "Braki w folderze (Left Orphan Files)", content)
    content = re.sub(r"Right Orphan Files", "Nowe w folderze (Right Orphan Files)", content)
    content = re.sub(r"Difference Files", "Pliki zmienione (Difference Files)", content)

    # Remove the "Left Newer Files" and "Right Newer Files" sections
    content = re.sub(r"Left Newer Files \(0\).*?----------------------------------------------\n\n", "", content, flags=re.DOTALL)
    content = re.sub(r"Right Newer Files \(0\).*?----------------------------------------------\n\n", "", content, flags=re.DOTALL)

    # Replace the "Summary of Analysis" section
    summary = (
        "Summary of Analysis:\n"
        f"Braki w folderze (Left Orphan Files): {counts.get('Left Orphan Files', 0)}\n"
        f"Nowe w folderze (Right Orphan Files): {counts.get('Right Orphan Files', 0)}\n"
        f"Pliki zmienione (Difference Files): {counts.get('Difference Files', 0)}\n"
    )
    content = re.sub(r"Summary of Analysis:.*", summary, content, flags=re.DOTALL)

    print("Modified report content:")
    print(content)  # Debugging output to verify the modified content

    # Write the updated content back to the report
    report_path.write_text(content, encoding="utf-8")

    # Automatically verify the updated report
    print("Updated report content saved to file:")
    print(report_path.read_text(encoding="utf-8"))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Process Beyond Compare reports.")
    parser.add_argument("-c", "--compare", type=str, help="Path to the right folder for comparison.")
    args = parser.parse_args()

    if args.compare:
        # Update the script.txt file with the new right folder path
        script_path = Path("script.txt")
        if script_path.exists():
            updated_lines = []
            with script_path.open("r", encoding="utf-8") as file:
                for line in file:
                    if line.strip().startswith("load right"):
                        updated_lines.append(f"load right {args.compare}\n")
                    else:
                        updated_lines.append(line)
            with script_path.open("w", encoding="utf-8") as file:
                file.writelines(updated_lines)
            print(f"Updated right folder path in script.txt to: {args.compare}")
        else:
            print("script.txt not found. Cannot update the right folder path.")
            sys.exit(1)

    # Run Beyond Compare before analyzing the report
    run_beyond_compare()

    report_path = Path("Wyniki_porownan") / "report.txt"
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

    order = ["Right Orphan Files", "Left Orphan Files", "Difference Files"]
    non_zero = [(k, counts[k]) for k in order if counts.get(k, 0) != 0]
    if non_zero:
        for k, v in non_zero:
            # Print with standardized labels as requested
            if k == "Right Orphan Files":
                print(f"Brakujace pliki: {v}")
            elif k == "Left Orphan Files":
                print(f"Nowe pliki: {v}")
            elif k == "Difference Files":
                print(f"Pliki rozne: {v}")
        log_test_result(left_folder, right_folder, "Niezgodne")
        os.startfile(report_path)  # Open the report file if differences are found
        sys.exit(2)
    else:
        print("Brak roznic!")
        log_test_result(left_folder, right_folder, "Zgodne")
        sys.exit(0)


if __name__ == "__main__":
    main()

