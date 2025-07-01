#!/bin/bash

# Configuration
FOLDER_PATH="/path/to/your/folder"  # Replace with the actual path to your folder
PERCENTAGE_TO_DELETE="20"        # Percentage of folder size to delete
DRY_RUN="true"                 # Set to "false" to actually delete files, "true" for testing

# Get the total folder size in bytes
TOTAL_SIZE=$(du -sb "$FOLDER_PATH" | awk '{print $1}')

# Calculate the size to delete in bytes
SIZE_TO_DELETE=$(( TOTAL_SIZE * PERCENTAGE_TO_DELETE / 100 ))

# Find the files to delete (oldest first)
FILES_TO_DELETE=$(find "$FOLDER_PATH" -type f -print0 | sort -z | head -z -n 1000000 | xargs -r -0 -n1 du -sb | sort -n | head -z -n 1000000 | cut -f1 | awk -v size="$SIZE_TO_DELETE" '
    {
        sum += $1;
        if (sum > size) {
            exit; # Stop when we've reached the target size
        }
        print;
    }' | tr '\n' '\0')


# Delete the files (or print them if DRY_RUN is true)
if [[ "$DRY_RUN" == "true" ]]; then
    echo "Files to delete (DRY RUN):"
    printf "%s\n" "${FILES_TO_DELETE[@]}" | sed 'z;s/\x00/\n/g'  # Print null-separated list with newlines for readability.
else
    if [[ -n "$FILES_TO_DELETE" ]]; then #Check if files_to_delete is not empty
        echo "Deleting files:"
        printf "%s\0" "${FILES_TO_DELETE[@]}" | xargs -r -0 rm -v # -v for verbose output
    else
        echo "No files found to delete."
    fi
fi

echo "Done."