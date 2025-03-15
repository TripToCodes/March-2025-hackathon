import speech_recognition as sr
import pyttsx3
import json
from os import environ
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI

load_dotenv()
OPENAI_API_KEY = environ["OPENAI_API_KEY"]

# Initialize Text-to-Speech Engine
engine = pyttsx3.init()

# Create an OpenAI LLM object
llm = OpenAI(model="gpt-4")

def speak(text):
    """Convert text to speech."""
    engine.say(text)
    engine.runAndWait()

def listen():
    """Capture audio and convert it to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening for your task...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        speak(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        speak("Sorry, I couldn't understand that.")
        return None
    except sr.RequestError:
        speak("Error connecting to speech recognition service.")
        return None

def generate_task_breakdown(task):
    """Use OpenAI to suggest a breakdown of a large task."""
    prompt = f"Break down the following task into smaller, manageable subtasks:\n\nTask: {task}\n\nSubtasks:"
    response = llm.complete(prompt)
    return response.text.strip().split("\n")

def save_tasks(task, subtasks):
    """Save tasks in a JSON file."""
    try:
        with open("todo_list.json", "r") as file:
            todo_list = json.load(file)
    except FileNotFoundError:
        todo_list = {}

    todo_list[task] = subtasks

    with open("todo_list.json", "w") as file:
        json.dump(todo_list, file, indent=4)

    speak("Task added successfully.")

def main():
    """Main function to handle voice input and task management."""
    while True:
        task = listen()
        if task:
            subtasks = generate_task_breakdown(task)
            save_tasks(task, subtasks)
            speak(f"Task '{task}' added with {len(subtasks)} subtasks.")
            print(f"Task: {task}\nSubtasks: {subtasks}")

if __name__ == "__main__":
    speak("Voice assistant started. Say your task.")
    main()
