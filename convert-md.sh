#!/bin/bash

# Directory to scan
directory="$1"

# Check if directory exists
if [[ ! -d "$directory" ]]; then
  echo "Directory does not exist."
  exit 1
fi

# Iterate through each file in the directory
for filepath in "$directory"/*; do
  # Check if it is a regular file
  if [[ -f "$filepath" ]]; then
    # Replace first two instances of '---' with '+++'
    sed -i '0,/\---/{s/\---/\+++/}' "$filepath"
    sed -i '0,/\---/{s/\---/\+++/}' "$filepath"
  fi
done

echo "Replacement done in all files."
