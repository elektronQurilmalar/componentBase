import os


def print_tree(directory, prefix="", ignore_dirs=None):
    if ignore_dirs is None:
        ignore_dirs = {'__pycache__', 'venv', 'zoneinfo', 'PyQt5', 'dist', 'objects', '.git', 'build', '.idea'}

    try:
        contents = sorted([item for item in os.listdir(directory) if item not in ignore_dirs])
    except PermissionError:
        return  # Пропускаем директории, к которым нет доступа

    for i, item in enumerate(contents):
        path = os.path.join(directory, item)
        is_last = i == len(contents) - 1
        print(f"{prefix}{'└── ' if is_last else '├── '}{item}")
        if os.path.isdir(path):
            print_tree(path, prefix + ("    " if is_last else "│   "), ignore_dirs)


if __name__ == "__main__":
    project_root = os.getcwd()  # Текущая директория проекта
    print(os.path.basename(project_root))
    print_tree(project_root)