# organizer.py
import os
import shutil
from pathlib import Path

FILE_TYPES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
    'Documents': ['.pdf', '.docx', '.doc', '.txt', '.pptx', '.xlsx'],
    'Videos': ['.mp4', '.mov', '.avi', '.mkv'],
    'Music': ['.mp3', '.wav', '.flac'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Scripts': ['.py', '.js', '.java', '.cpp', '.c']
}

def organize_folder(folder_path):
    folder = Path(folder_path)
    for file in folder.iterdir():
        if file.is_file():
            ext = file.suffix.lower()
            moved = False

            for category, extensions in FILE_TYPES.items():
                if ext in extensions:
                    target_dir = folder / category
                    target_dir.mkdir(exist_ok=True)
                    shutil.move(str(file), str(target_dir / file.name))
                    moved = True
                    break

            if not moved:
                other_dir = folder / "Others"
                other_dir.mkdir(exist_ok=True)
                shutil.move(str(file), str(other_dir / file.name))
