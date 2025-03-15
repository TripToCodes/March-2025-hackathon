from livekit.agents.llm import FunctionContext
from livekit.plugins import openai
import json
import asyncio
import subprocess


class AssistantFnc(FunctionContext):
    def __init__(self):
        # Initialize any required attributes, like the current task list or context.
        self.task_list = []
        super().__init__()

    async def handle_task_breakdown(self, task: str):
        """
        Breaks down a large task into smaller manageable subtasks using OpenAI's LLM.
        """
        prompt = f"Break down the following task into smaller, manageable subtasks:\n\nTask: {task}\n\nSubtasks:"
        response = await openai.LLM().complete(prompt)
        subtasks = response.text.strip().split("\n")
        return subtasks

    def save_tasks(self, task: str, subtasks: list):
        """
        Save tasks and their subtasks to a JSON file and to MacOS Reminders.
        """
        try:
            with open("todo_list.json", "r") as file:
                todo_list = json.load(file)
        except FileNotFoundError:
            todo_list = {}

        # Save task and subtasks to the JSON file
        todo_list[task] = subtasks

        with open("todo_list.json", "w") as file:
            json.dump(todo_list, file, indent=4)

        # Add the task and subtasks to MacOS Reminders
        self.add_to_reminders(task, subtasks)

    def add_to_reminders(self, task: str, subtasks: list):
        """
        Add tasks and subtasks to MacOS Reminders using AppleScript.
        """
        for subtask in subtasks:
            script = f'''
            tell application "Reminders"
                tell list "Tasks"
                    make new reminder with properties {{name:"{subtask}", body:"Part of task: {task}"}}
                end tell
            end tell
            '''
            subprocess.run(["osascript", "-e", script])

    async def execute(self, command: str):
        """
        The main method to handle user commands. This will break down tasks and save them.
        """
        subtasks = await self.handle_task_breakdown(command)
        self.save_tasks(command, subtasks)
        return f"Task '{command}' has been broken down into {len(subtasks)} subtasks and saved."


# Example of how the AssistantFnc class can be used
if __name__ == "__main__":
    # Assuming you have a way to get a task from the voice assistant
    task = "Organize a team meeting"

    fnc = AssistantFnc()
    result = asyncio.run(fnc.execute(task))
    print(result)
