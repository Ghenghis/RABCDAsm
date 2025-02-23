import os

# Directory to process
TARGET_DIR = r"J:\evony_1921\AS3 Scripts (EvonyClient1921.swf)"

def remove_backups(dir_path):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.bak') or file.endswith('.bak.bak'):
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                    print(f"Removed: {filepath}")
                except Exception as e:
                    print(f"Error removing {filepath}: {e}")

if __name__ == '__main__':
    if os.path.exists(TARGET_DIR):
        print("Removing backup files...")
        remove_backups(TARGET_DIR)
        print("Cleanup complete!")
    else:
        print(f"Target directory does not exist: {TARGET_DIR}")
