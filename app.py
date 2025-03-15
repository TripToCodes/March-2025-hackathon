import asyncio
import json
import subprocess
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero
from api import AssistantFnc

load_dotenv()

async def entrypoint(ctx: JobContext):
    # Define the system message for the assistant's context
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoid usage of unpronounceable punctuation."
        ),
    )

    # Connect to the LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Initialize the assistant function context
    fnc_ctx = AssistantFnc()

    # Create the VoiceAssistant with proper plugins
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),  # Voice activity detection plugin
        stt=openai.STT(),       # Speech-to-text plugin from OpenAI
        llm=openai.LLM(),       # Language model from OpenAI
        tts=openai.TTS(),       # Text-to-speech plugin from OpenAI
        chat_ctx=initial_ctx,   # Initial chat context for the assistant
        fnc_ctx=fnc_ctx,        # Function context to handle custom logic
    )

    # Start the assistant in the room
    assistant.start(ctx.room)

    # Give a welcome message
    await asyncio.sleep(1)
    await assistant.say("Hey, how can I help you today?", allow_interruptions=True)

    # Loop to continuously listen for voice commands
    while True:
        # Listen for a voice command from the user
        command = await assistant.listen()

        if command:
            print(f"User Command: {command}")

            # Process the user's command, e.g., by breaking it down into tasks using OpenAI
            subtasks = await generate_task_breakdown(command)

            # Save tasks and add them to MacOS Reminders
            await save_tasks(command, subtasks)

            # Respond to the user with the breakdown
            response = f"Task: {command}\nSubtasks: {', '.join(subtasks)}"
            await assistant.say(response)

async def generate_task_breakdown(task: str):
    """Generate a breakdown of a task into smaller subtasks using OpenAI's LLM."""
    prompt = f"Break down the following task into smaller, manageable subtasks:\n\nTask: {task}\n\nSubtasks:"
    response = await openai.LLM().complete(prompt)
    return response.text.strip().split("\n")

def add_to_reminders(task: str, subtasks: list):
    """Add tasks and their subtasks to MacOS Reminders app via AppleScript."""
    for subtask in subtasks:
        script = f'''
        tell application "Reminders"
            tell list "Tasks"
                make new reminder with properties {{name:"{subtask}", body:"Part of task: {task}"}}
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])

async def save_tasks(task: str, subtasks: list):
    """Save tasks and their subtasks to a JSON file and add them to MacOS Reminders."""
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
    add_to_reminders(task, subtasks)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
