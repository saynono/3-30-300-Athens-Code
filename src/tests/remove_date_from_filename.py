import os
import re

# Specify the folder containing the files
folder_path = "../../../3-30-300-Athens-Data/GSV-Data/panoramas-final-new"

# Regular expression pattern to match the date part (_YYYY-MM)
pattern = r"_\d{4}-\d{2}"

# Iterate through all files in the folder
for filename in os.listdir(folder_path):
    # Check if the filename matches the date pattern
    new_filename = re.sub(pattern, "", filename)

    # Only rename if the new filename is different
    if new_filename != filename:
        # Build full file paths
        old_file_path = os.path.join(folder_path, filename)
        new_file_path = os.path.join(folder_path, new_filename)

        # Rename the file
        os.rename(old_file_path, new_file_path)
        print(f"Renamed: {filename} -> {new_filename}")
