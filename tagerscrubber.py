import os
import re

BAD_TAGGER_PATTERN = re.compile(
    r"",
    re.MULTILINE
)

def clean_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # If no bad tagger block, skip
        if not BAD_TAGGER_PATTERN.search(content):
            return False

        # Remove the block
        cleaned = BAD_TAGGER_PATTERN.sub("", content)

        # Write back safely
        with open(path, "w", encoding="utf-8") as f:
            f.write(cleaned)

        print(f"Cleaned: {path}")
        return True

    except Exception as e:
        print(f"Error processing {path}: {e}")
        return False


def clean_folder(root_folder):
    for root, dirs, files in os.walk(root_folder):
        for name in files:
            file_path = os.path.join(root, name)
            clean_file(file_path)


if __name__ == "__main__":
    folder = input("Enter folder to clean: ").strip()
    clean_folder(folder)
    print("Done.")