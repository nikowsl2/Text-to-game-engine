from openai import OpenAI
import json
import os
import time
import re
import tkinter as tk
from tkinter import messagebox
from NPC import create_char, get_initial_prompt, get_dev_message, get_response
from StoryGenerator import get_starting_prompt


HISTORY_FILE = "history.json"
PROTAGONISTS_FILE = "protagonists.json"
MODEL_NAME = "llama3-8b-8192"
DATA = {
    "chars": {},
    "history": []
}

def get_client():
    return OpenAI(
        api_key="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",
        base_url="https://api.groq.com/openai/v1"
    )

def run_generation():
    prompt = get_starting_prompt(DATA)
    client = get_client()

    beginning_line = get_response(client, MODEL_NAME, prompt)

    # Create the main window
    root = tk.Tk()
    root.title("story generation")
    root.geometry("960x540")

    # Create a Text widget (editable multi-line text)
    text = tk.Text(
        root,
        height=20,  # Number of lines
        width=50,  # Width in characters
        font=("Arial", 12),
        wrap=tk.WORD,  # Wrap text at word boundaries
    )
    text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    text.insert("1.0", f"{beginning_line.choices[0].message.content}")
    text.config(state="disabled")

    # Scrollbar
    scrollbar = tk.Scrollbar(text, command=text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text.config(yscrollcommand=scrollbar.set)

    # Label
    label = tk.Label(root, text="Enter your text below:")
    label.pack(pady=10)

    # Textbox (Entry widget)
    textbox = tk.Entry(root, width=100)
    textbox.pack(pady=10)

    # Function to handle button click
    def on_submit():
        user_text = textbox.get()
        dv = get_dev_message(prompt, DATA["history"])
        response = get_response(client, dv, user_text)
        if user_text:
            text.config(state="normal")
            text.insert("end", f"You: {user_text}\n")
            text.insert("end", "hello, fucker")
            text.config(state="disabled")
            text.see(tk.END)
            DATA["history"].append(["User", user_text])
            #DATA["history"].append([char_prompt['name'], response.choices[0].message.content])
            textbox.delete(0, tk.END)
        else:
            messagebox.showwarning("Empty Input", "Please enter some text!")

    # Submit button
    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=10)

    # Run the application
    root.mainloop()

def run_mode1():


    root = tk.Tk()
    root.title("Story Creation")
    root.geometry("960x540")

    genre_label = tk.Label(root, text="What is the genre of the story?")
    genre_label.pack(pady=2)
    genre_box = tk.Entry(root, width=50)
    genre_box.pack(pady=10)

    num_char_label = tk.Label(root, text="How many Non-Player Characters would you like to add to the story (max 10)?")
    num_char_label.pack(pady=2)
    num_char_box = tk.Entry(root, width=50)
    num_char_box.pack(pady=10)

    story_label = tk.Label(root, text="Can you give us an overview of the story setup?")
    story_label.pack(pady=2)
    story_box = tk.Entry(root, width=50)
    story_box.pack(pady=10)

    goal_label = tk.Label(root, text="What is the goal of the player character?")
    goal_label.pack(pady=2)
    goal_box = tk.Entry(root, width=50)
    goal_box.pack(pady=10)


    def on_submit():
        genre = genre_box.get()
        num_char = num_char_box.get()
        story = story_box.get()
        goal = goal_box.get()
        try:
            num_char = int(num_char)
        except ValueError:
            messagebox.showerror("Invalid Number", "Please enter a valid number!")

        DATA["story"] = {
            "genre": genre,
            "storyline": story,
            "goal": goal
        }
        root.destroy()
        for i in range(num_char):
            try:
                npc = create_char()
                DATA["chars"][npc["name"]] = npc
            except Exception as e:
                messagebox.showerror("Error", f"Character creation failed: {str(e)}")
        run_generation()



    next_button = tk.Button(root, text="Next", font=("Arial", 16), command=on_submit, width=20)
    next_button.pack(pady=10)

def main():
    #print("✨ Story Generator ✨")
    #print("1. Start New Story")
    #print("2. Exiting")

    root = tk.Tk()
    root.title("Main Menu")
    root.geometry("960x540")

    title_label = tk.Label(root, text="CSCI 544 Text To Game Engine", font=("Arial", 24))
    title_label.pack(pady=80)

    def run_1():
        run_mode1()
        root.destroy()

    def run_2():
        run_mode2()
        root.destroy()

    new_button = tk.Button(root, text="New Game", font=("Arial", 16), command=run_1, width=30, height=3)
    new_button.pack(pady=10)

    new_button = tk.Button(root, text="Load Game", font=("Arial", 16), command=run_2, width=30, height=3)
    new_button.pack(pady=10)

    root.mainloop()

    """mode = input("\nSelect (1/2): ").strip()

    if mode == "1":
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        run_mode1()
    elif mode == "2":
        if not os.path.exists(HISTORY_FILE) or not os.path.exists(PROTAGONISTS_FILE):
            print("Required files missing! Start with Mode 1 first.")
            return
        run_mode2() """


if __name__ == "__main__":
    main()