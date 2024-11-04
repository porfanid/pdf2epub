#!/bin/bash

# Set the output file for the file tree and the directory for text files
OUTPUT_FILE="filetree.md"
TEXT_FILES_DIR="text_files"

# Create the directory for text files if it doesn't exist
mkdir -p "$TEXT_FILES_DIR"

# Define directories to exclude
EXCLUDE_DIRS=".venv venv .git $TEXT_FILES_DIR"

# Create a regular expression pattern for excluded directories
EXCLUDE_PATTERN=$(echo $EXCLUDE_DIRS | sed 's/ /|/g')

# Generate the file tree excluding specified directories and output to OUTPUT_FILE
tree -a -I "$EXCLUDE_PATTERN" --charset utf-8 | sed 's/^/    /' > "$OUTPUT_FILE"

# Find and copy all text-based files to the TEXT_FILES_DIR, using a flat file structure
find . -type f -not -path "./$TEXT_FILES_DIR/*" -print0 | grep -zEv "./($EXCLUDE_PATTERN)/" | while IFS= read -r -d '' file; do
    # Skip .db files and check if the file is a text file
    if [[ ! "$file" =~ \.db$ ]]; then
        if file "$file" | grep -qE 'ASCII|UTF-8|Python script|empty'; then
            # Remove the leading "./" and replace slashes with double underscores
            dest_file=$(echo "$file" | sed 's|^\./||; s|/|__|g')
            cp "$file" "$TEXT_FILES_DIR/$dest_file"
        fi
    fi
done

echo "File tree generated in $OUTPUT_FILE."
echo "Text-based files copied to $TEXT_FILES_DIR."
