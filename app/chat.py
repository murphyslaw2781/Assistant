from halo import Halo
import os
import openai
import textwrap
from dotenv import load_dotenv
from app.file_operations import (run_command, open_file, save_file, clear_log,
                             save_to_scratchpad, log_conversation, list_files,
                             append_file, create_system_message_file)
from app.api.chatGPT import chatbot
from dotenv import load_dotenv

load_dotenv()

base_dir = os.getcwd()
openai.api_key = os.getenv('OPENAI_API_KEY')
ALL_MESSAGES = []

def select_directory():
    new_path = input('Enter new directory path: ')
    if os.path.isdir(new_path):
        return new_path
    else:
        print("Invalid path. Please try again.")
        return select_directory()
    
def prepare_conversation(choice, base_dir, options, scratchpad, text):
    ALL_MESSAGES.append({'role': 'user', 'content': text})
    log_conversation('user', text, base_dir)
    system_message_file_path = os.path.join(base_dir, f'app/prompts/{options[choice]}/system_message.txt')
    create_system_message_file(system_message_file_path)
    system_message_content = open_file(system_message_file_path)
    system_message = system_message_content.replace('<<CODE>>', open_file(scratchpad)).replace('<<TREE>>', open_file(os.path.join(base_dir,'app/prompts/tree.md'))) 
    conversation = ALL_MESSAGES.copy()
    conversation.append({'role': 'system', 'content': system_message})
    return conversation

def print_response(response):
    print('\n\n\n\nCHATBOT:\n')
    formatted_lines = [textwrap.fill(line, width=120) for line in response.split('\n')]
    formatted_text = '\n'.join(formatted_lines)
    print(formatted_text)

def process_choice(choice, options, files):
    state = True
    scratchpad = os.path.join(base_dir, f'app/prompts/{options[choice]}/scratchpad.txt')
    save_file(scratchpad,'')

    while state:
        if choice == 1:
            save_file(scratchpad, '')
            print("\nPlease select the files to review:")
            for key, value in files.items():
                abs_path, rel_path = value
                print(f"{key}. {rel_path}")

            print("Enter the numbers of the files you want to review, separated by commas (or type 'BACK' to start over):")
            text = input()
            if text.upper() == 'BACK':
                state = False
            elif text.upper() == 'EXIT':
                print("Ending the session.")
                break
            else:
                file_numbers = text.split(',')
                try:
                    file_paths = [files[int(num.strip())][0] for num in file_numbers]
                except KeyError:
                    print("\nInvalid choice. Please try again.")
                else:
                    for file in file_paths:
                        read_file = open_file(file)
                        append_file(scratchpad, read_file)
                    print("\nPlease turn on scratchpad (enter '1'), or type your question")
                    text = input('(or type "BACK" to start over):\n ')
                    if text.upper() == 'BACK':
                        state = False
                    elif text == '1':
                        text = save_to_scratchpad()
                        append_file(scratchpad, text.strip('END').strip())
                        print('\n\n##### Scratchpad updated!')
        else:
            print("\nPlease turn on scratchpad (enter '1'), or type your question")
            text = input('(or type "BACK" to start over):\n ')
            if text.upper() == 'BACK':
                state = False
            elif text == '1':
                text = save_to_scratchpad()
                save_file(scratchpad, text.strip('END').strip())
                print('\n\n##### Scratchpad updated!')

        if text and state:
            conversation = prepare_conversation(choice, base_dir, options, scratchpad, text)
            spinner = Halo(text='Coding...', spinner='dots')
            spinner.start()
            response, tokens = chatbot(conversation)
            spinner.stop()
            if tokens > 7500:
                ALL_MESSAGES.pop(0)
            ALL_MESSAGES.append({'role': 'assistant', 'content': response})
            log_conversation('assistant', response,base_dir)
            print_response(response)

def main():
    print('\n\n\n\nWelcome to the Coding Assistant!\n')
    clear_log()
    selected_path = select_directory() 
    
    files = list_files(selected_path)
    
    options = {1: 'peer_review', 2: 'code_inquiry', 3: 'general_qa'}

    while True:
        print("\nPlease choose an option:")
        for key, value in options.items():
            print(f"{key}. {value}")
        choice = input("\nYour choice (or type 'BACK' to start over): ")
        if choice.upper() == 'BACK':
            continue
        elif choice.upper() == 'EXIT':
            print("Ending the session.")
            break
        try:
            choice = int(choice)
        except ValueError:
            print("\nInvalid input. Please enter a number.")
            continue
        if choice not in options:
            print("\nInvalid choice. Please try again.")
            continue

        process_choice(choice, options, files)

if __name__ == '__main__':
    main()