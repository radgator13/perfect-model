import os
import sys
import platform
import subprocess

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = '    ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '    ' * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

def get_git_info():
    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"]).decode().strip()
        latest_commit = subprocess.check_output(["git", "log", "-1", "--oneline"]).decode().strip()
        return f"Git branch: {branch}\nLast commit: {latest_commit}"
    except:
        return "Not a Git repo or Git not installed."

def main():
    print("📦 Project Environment Summary\n")

    # Python version
    print(f"🐍 Python version: {platform.python_version()}")

    # OS info
    print(f"🖥️ OS: {platform.system()} {platform.release()}")

    # Virtual environment?
    print(f"🔒 Virtualenv: {os.getenv('VIRTUAL_ENV', 'Not active')}")

    # Requirements
    print("\n📋 Dependencies:")
    if os.path.exists("requirements.txt"):
        with open("requirements.txt") as f:
            for line in f:
                print(f"  - {line.strip()}")
    else:
        print("  (requirements.txt not found)")

    # .env or secrets
    if os.path.exists(".env"):
        print("\n🔑 .env file detected (not shown for security)")

    # Project structure
    print("\n📁 Project Structure:")
    list_files(".")

    # Git
    print("\n🔧 Git Info:")
    print(get_git_info())

if __name__ == "__main__":
    main()
