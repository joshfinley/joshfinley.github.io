#!/bin/bash

# Check if a file is specified
if [ -z "$1" ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

# Check if the file exists
if [ ! -f "$1" ]; then
  echo "Error: File '$1' not found."
  exit 1
fi

# Run aspell
echo "Running aspell..."
aspell -c "$1"

# Check aspell exit status
if [ $? -ne 0 ]; then
  echo "aspell encountered an error."
  exit 1
fi

# Run proselint
echo "Running proselint..."
proselint "$1"

# Check proselint exit status
if [ $? -ne 0 ]; then
  echo "proselint encountered an error."
  exit 1
fi

echo "Done!"
