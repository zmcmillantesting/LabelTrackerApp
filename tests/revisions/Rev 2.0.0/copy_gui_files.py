import os
import shutil
import sys

def copy_files(source_root, dest_root):
    """
    Copy necessary GUI files from source project to the new application directory.
    
    Args:
        source_root: Path to the source project root
        dest_root: Path to the destination application directory
    """
    # Create necessary directories
    os.makedirs(os.path.join(dest_root, "application", "gui"), exist_ok=True)
    os.makedirs(os.path.join(dest_root, "application", "gui", "images"), exist_ok=True)
    
    # Files to copy
    files_to_copy = [
        ("gui/main_window.py", "application/gui/main_window.py"),
        ("gui/widgets.py", "application/gui/widgets.py"),
    ]
    
    # Copy image files
    for image_file in os.listdir(os.path.join(source_root, "gui", "images")):
        source_path = os.path.join(source_root, "gui", "images", image_file)
        dest_path = os.path.join(dest_root, "application", "gui", "images", image_file)
        if os.path.isfile(source_path):
            print(f"Copying image: {image_file}")
            shutil.copy2(source_path, dest_path)
    
    # Copy each file
    for source_file, dest_file in files_to_copy:
        source_path = os.path.join(source_root, source_file)
        dest_path = os.path.join(dest_root, dest_file)
        
        if os.path.exists(source_path):
            print(f"Copying: {source_file} -> {dest_file}")
            shutil.copy2(source_path, dest_path)
        else:
            print(f"Source file not found: {source_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python copy_gui_files.py <source_project_path> <destination_data_path>")
        sys.exit(1)
    
    source_root = sys.argv[1]
    dest_root = sys.argv[2]
    
    print(f"Copying files from {source_root} to {dest_root}")
    copy_files(source_root, dest_root)
    print("Done!") 