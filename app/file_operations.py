import os
import fnmatch
import re
import json
import subprocess
import yaml
from time import sleep
from datetime import datetime
from os.path import join, dirname, abspath, realpath

# Use os.path.join() to construct filepaths
base_dir = dirname(realpath(__file__))  # This will get the directory that the script is in


# Use os.path.join() to construct filepaths
tree_md = '/prompts/tree.md'
history_log = '/logs/chat_history.md'
chat_md = '/logs/chat.md'


def log_conversation(role, message, base_dir):
    chat_dir = os.path.join(base_dir, 'coding_assistant', 'logs')
    os.makedirs(chat_dir, exist_ok=True)  # Create logs directory if it doesn't exist
    chat_file = os.path.join(chat_dir, 'chat.md')
    with open(chat_file, 'a', encoding='utf-8') as f:
        f.write(f"### {role}:\n {message}\n")
    save_log(role, message, base_dir)

def save_log(role, message, base_dir):  # Create directory if it doesn't exist
    log_dir = os.path.join(base_dir, 'coding_assistant', 'logs')
    os.makedirs(log_dir, exist_ok=True)  # Create logs directory if it doesn't exist
    log_file = os.path.join(log_dir, 'chat_history.md')
    today = datetime.today()
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"### {role} on {today}:\n{message}\n")


def clear_log(filename=chat_md):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"")

def save_to_scratchpad():
    print('\n\n\nType END to save and exit.\n[MULTI] USER:\n')
    lines = []
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)
    return "\n".join(lines)

def list_files(startpath):
    file_dict = {}
    i = 1
    tree_output = ''
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in ['migrations', '.venv', '.env','.git','data','db','coding_assistant']]  # Remove unwanted directories from the walk
        for file in files:
            # Ignore Python cache files and .txt or .md files inside prompts
            if file.endswith('.pyc') or file.endswith('.sql') or file.startswith('.env') or file.startswith('.venv'):
                continue
            if (root.endswith('prompts') and (file.endswith('.txt') or file.endswith('.md') or file.endswith('.db') or file.endswith('.pem') )):
                continue
            # Ignore log files
            if root.endswith('logs') and file.endswith('.log'):
                continue
            # Get the relative path
            rel_path = os.path.relpath(os.path.join(root, file), startpath)
            abs_path = os.path.join(root, file)
            file_dict[i] = (abs_path, rel_path)
            tree_output += f"{i}. {rel_path}\n"
            i += 1
    # If 
    with open('app/prompts/tree.md', 'w') as f:
        f.write(tree_output)

    return file_dict



def run_command(app_dir):
    if not os.path.isdir(app_dir):
        print('Invalid directory. Please try again.')
        return None  # Return None to indicate an error
    output_file = os.path.join(app_dir, 'prompts/tree.md')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    command = f'rptree "{app_dir}" --output-file "{output_file}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print("Command executed, return code is ", result.returncode)
    return output_file  # Return the path to the generated tree file




def save_yaml(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)


def open_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    return data


def save_file(filename, content):
    directory = os.path.dirname(filename)  # Get the directory name
    os.makedirs(directory, exist_ok=True)  # Create directory if it doesn't exist
    with open(filename, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

        
def append_file(filepath, content):
    directory = os.path.dirname(filepath)  # Get the directory name
    os.makedirs(directory, exist_ok=True)  # Create directory if it doesn't exist
    with open(filepath, 'a', encoding='utf-8') as outfile:
        outfile.write(content)


def open_file(filepath):
    directory = os.path.dirname(filepath)  # Get the directory name
    os.makedirs(directory, exist_ok=True)  # Create directory if it doesn't exist
    if os.path.isfile(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
            return infile.read()
    else:
        print(f"File {filepath} does not exist.")
        return None
    
def create_system_message_file(file_path):
    if not os.path.isfile(file_path):
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)
        content = '''
        MAIN PURPOSE
        You are a Senior Backend Developer that will review code that is sent. The USER will give you code that you must review for efficiency, error handling, scalability, and best practices. 
        The current app is provided in the current file tree. You may ask for clarification if needed, but otherwise you must reason from the tree about the current app. 


        SCRATCHPAD
        The below scratchpad is the code that the user has questions or needs to be refactored for efficiency, error handling, scalability, and best practices.

        SCRATCHPAD:

        <<CODE>>

        CURRENT FILE TREE:

        <<TREE>>
        '''
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)



def write_file_tree(file_tree):
    file_path = join(base_dir, 'prompts/tree.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in file_tree:
            f.write("%s\n" % item)

def get_file_tree():
    exclude_dirs = ['.git', '__pycache__', 'venv', 'env']
    file_tree = []

    for root, dirs, files in os.walk(os.getcwd()):
        level = root.count(os.sep)
        if level > 3:  # Only go 3 levels deep
            continue

        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            print(file)
            if not fnmatch.fnmatch(file, '*.pyc'):
                file_tree.append('|   ' * (level - 1) + '|-- ' + os.path.basename(file))

    write_file_tree(file_tree)  # Call the function to write the list to a file

def save_directory_tree(path, prefix='', level=1):
    if level > 2:
        return

    file_path = join(base_dir, 'prompts/tree.txt')
    contents = os.listdir(path)
    contents.sort()

    with open(file_path, 'a', encoding='utf-8') as f:
        for i, item in enumerate(contents):
            item_path = os.path.join(path, item)
            is_last_item = i == len(contents) - 1

            if os.path.isdir(item_path):
                # Write directory to file
                if is_last_item:
                    f.write(f'{prefix}└── {item}/\n')
                    next_prefix = f"{prefix}    "
                else:
                    f.write(f'{prefix}├── {item}/\n')
                    next_prefix = f"{prefix}│   "

                # Recursively write subdirectories to file
                save_directory_tree(item_path, next_prefix, level + 1)

            else:
                # Write file to file
                if is_last_item:
                    f.write(f"{prefix}└── {item}\n")
                else:
                    f.write(f"{prefix}├── {item}\n")