import os
import re

def convert_header(file_path):
    print(f"Processing file: {file_path}")

    with open(file_path, 'r') as f:
        lines = f.readlines()

    in_header = False
    new_lines = []
    for line in lines:
        stripped_line = line.strip()

        # Check for the header start or end
        if stripped_line == '+++':
            in_header = not in_header
            print(f"Header toggled: {'Started' if in_header else 'Ended'}")
            new_lines.append(line)
            continue

        if in_header:
            print(f"Original header line: {stripped_line}")
            
            # Replace the old format "parameter: value" with "parameter = value"
            updated_line = re.sub(r'^(.*?):\s*(.*)$', r'\1 = \2', line)
            
            print(f"Updated header line: {updated_line.strip()}")
            new_lines.append(updated_line)
        else:
            new_lines.append(line)

    with open(file_path, 'w') as f:
        f.writelines(new_lines)

    print(f"File {file_path} converted.")

def main():
    # Scan the given directory for Markdown files
    directory_path = "./content/posts"  # Replace with your posts directory
    print(f"Scanning directory: {directory_path}")

    for filename in os.listdir(directory_path):
        print(filename)
        if filename.endswith('.md'):
            file_path = os.path.join(directory_path, filename)
            convert_header(file_path)
            print(f"Converted {filename}")

if __name__ == '__main__':
    main()
