from openai import OpenAI
import os
from typing_extensions import override 
from openai import AssistantEventHandler 
from termcolor import colored

OPENAI_API_KEY = ""

class AssistantsUnified:
  
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.assistant = None
        self.vector_store = None
        self.thread = None
      
    def setup_assistant(self, assistant_id=None):
        if assistant_id:
            print("Retrieving assistant...")
            self.assistant = self.client.beta.assistants.retrieve(assistant_id)
        else:
            print("Creating assistant...")
            name = input(colored("Enter the name of the assistant: ", "yellow"))
            instructions = input(colored("Enter the instructions for the assistant: ", "yellow"))
            self.assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions, 
                model="gpt-4o",
                tools=[{"type": "file_search"}, {"type": "code_interpreter"}],
            )
        
    def setup_vector_store(self):
        print("Creating vector store...")
        name = input(colored("Enter the name of the vector store: ", "yellow"))
        self.vector_store = self.client.beta.vector_stores.create(
            name=name,
            expires_after={"anchor": "last_active_at", "days": 7},
        )
      
    def upload_files_to_vector_store(self, file_paths):
        print("Uploading files to vector store...")
        file_streams = [open(path, "rb") for path in file_paths]
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=self.vector_store.id,
            files=file_streams,
        )
        print(file_batch.status)
        print(file_batch.file_counts)
      
    def update_assistant(self):
        print("Updating assistant...")
        self.assistant = self.client.beta.assistants.update(
            assistant_id=self.assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [self.vector_store.id]}},
        )
      
    def setup_thread(self, thread_id=None):
        if thread_id:
            print("Retrieving thread...")
            self.thread = self.client.beta.threads.retrieve(thread_id)
        else:
            print("Creating thread...")
            self.thread = self.client.beta.threads.create(messages=[])

    def create_message(self, content, file=None):
        message_data = {
            "role": "user",
            "content": content,
        }
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            **message_data,
        )
        
    def chat_loop(self):
        while True:
            message = input(colored("User: ", "magenta"))
            if message.lower() == 'quit':
                break
            self.create_message(message)
            with self.client.beta.threads.runs.stream(
                thread_id=self.thread.id, 
                assistant_id=self.assistant.id,
                instructions="You are an intelligent assistant", 
                event_handler=EventHandler(self.client), 
                truncation_strategy={"type": "auto"}
            ) as stream:
                stream.until_done()
              
class EventHandler(AssistantEventHandler):
  
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.code_interpreter = ""  # Initialize the code_interpreter attribute

    @override
    def on_text_created(self, text) -> None:
        print("\nassistant › ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(colored(delta.value, "cyan"), end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)
        if tool_call.type == "code_interpreter":
            self.code_interpreter = ""  # Optionally reset or initialize here as well
            print(colored(f"\nAssistant > {tool_call.type}\n", "magenta"), flush=True)

    @override
    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                self.code_interpreter += delta.code_interpreter.input 
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                # Save code_interpreter to file
                with open("code_interpreter/code_interpreter.py", "w") as f:
                    f.write(self.code_interpreter)
                    print(colored("\n\noutput ›", "yellow"), flush=True)
                    for output in delta.code_interpreter.outputs:
                        if output.type == "logs":
                            print(colored(f"\n{output.logs}", "red"), flush=True)
  
    @override
    def on_message_done(self, message) -> None:
        message_content = message.content[0].text
        annotations = message_content.annotations
        citations = []
        for index, annotation in enumerate(annotations):
            message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
            if file_citation := getattr(annotation, "file_citation", None):
                cited_file = self.client.files.retrieve(file_citation.file_id)
                citations.append(f"[{index}] {cited_file.filename}")
        print("\n")
        print(colored("\n".join(citations), "red"))

if __name__ == "__main__":
    assistant = AssistantsUnified()
    assistant_id = input(colored("Enter the assistant ID to use (press enter to create a new assistant): ", "yellow"))
    thread_id = input(colored("Enter the thread ID to use (press enter to create a new thread): ", "yellow"))
    assistant.setup_assistant(assistant_id=assistant_id)
    if not assistant_id and not thread_id:
        sow_folder = "sows"
        files = os.listdir(sow_folder)
        if files:
            file_paths = [os.path.join(sow_folder, file) for file in files]
            assistant.setup_vector_store()
            assistant.upload_files_to_vector_store(file_paths)
            assistant.update_assistant()
        else:
            print("No files found in the 'sow' folder.")
    assistant.setup_thread(thread_id=thread_id)
    assistant.chat_loop()
