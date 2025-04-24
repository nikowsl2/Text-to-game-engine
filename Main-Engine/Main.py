from openai import OpenAI
import json
import os
import time
import re
import tkinter as tk
from tkinter import messagebox
from NPC import create_char, get_initial_prompt, get_dev_message, get_response
from StoryGenerator import get_starting_prompt, format_characters, get_last_story_segment, story_generation, parse_new_characters, check_goal


HISTORY_FILE = "history.json"
PROTAGONISTS_FILE = "protagonists.json"
MODEL_NAME = "llama3-8b-8192"
DATA = {
    "chars": {},
    "history": []
}
client = OpenAI(
    api_key="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",
    base_url="https://api.groq.com/openai/v1"
)


def classifier(client, user_input):
    return client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": f"""You are a classifier. Your job is to determine the user's intent with his input."""},
            {"role": "user", "content": f"""
                    Given the user's input, determine if they would like to switch from the story generator to conversing with one of the characters or vice-versa.
            If the user input is directed at the story generator, respond with \"story\".
            If the user input is directed at a character, respond with the Character's name. Make sure that the character name you respond with is \
            part of the following: {list(DATA["chars"].keys())}
            
            Here are a few examples:
            Current conversation agent: story
            User input: I walk down the hallway
            Your response: story
            You respond with story because the user is currently using the story agent and by issuing directions to progress the story they \
            clearly wish to continue using the story agent
            
            Current conversation agent: John
            User input: How was your day?
            Your response: John
            You respond with John as the user is currently conversing with John and the input is clearly directed at a character, meaning they desire to continue conversing with John
            
            
            Context: the bartender's name is Chuck
            Current conversation agent: story
            User input: I approach the bartender
            Your response: Chuck
            You respond with Chuck as the user is currently using the story agent but clearly wishes to begin a conversation with the Bartender.\
             You respond with Chuck because the bartender's name is Chuck, but if the bartender's name was John, you would respond with John.
             
            Current conversation agent: Chuck
            User input: I get up from the bar and leave the room
            Your response: story
            You respond with story as while the user was previously conversing with Chuck, the direction clearly \
            indicates that the user wishes leave the conversation and progress with the story agent.
            
            
            Here is the current context that you are provided with:
            Characters:
            {format_characters(DATA)}
            
            Conversation History:
            {get_last_story_segment(DATA)}
            
            Remember to respond ONLY with "story" or a character's name. Do not include any other information in the response.
            Also remember that if you respond with a character's name, it MUST be included in the following list {list(DATA["chars"].keys())}.
            DO NOT respond with a name not on the provided list. Your only valid responses are names from that list or "story".
            
            
            The current conversation agent: {DATA["target"]}
            User Input: {user_input}
            """},
        ],
        stream=False
    )


def run_generation(beginning_line):
    # Create the main window
    root = tk.Tk()
    root.title("story generation")
    root.geometry("1280x720")

    # Create a Text widget (editable multi-line text)
    text = tk.Text(
        root,
        height=20,  # Number of lines
        width=50,  # Width in characters
        font=("Arial", 12),
        wrap=tk.WORD,  # Wrap text at word boundaries
    )
    text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    text.insert("1.0", f"{beginning_line}\n")
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
        global DATA
        user_text = textbox.get()
        input_type = classifier(client, user_text).choices[0].message.content
        print(input_type)
        response = None
        if input_type == "story":
            response = story_generation(client, MODEL_NAME, DATA, user_text)
            DATA["history"].append(["User", user_text])
            DATA["history"].append([input_type, response])
            DATA = parse_new_characters(response, DATA, MODEL_NAME)
        elif input_type in DATA["chars"].keys():
            dv = get_dev_message(get_initial_prompt(
                DATA, input_type), DATA["history"])
            response = get_response(
                client, dv, user_text).choices[0].message.content
            DATA["history"].append(["User", user_text])
            DATA["history"].append([input_type, response])
        else:
            messagebox.showerror(
                "An issue occured!", "Uh Oh, the AI is stupid and can't process your input")
        if response is not None:
            text.config(state="normal")
            text.insert("end", f"\n")
            text.insert("end", f"You: {user_text}\n\n", "user_text")
            text.insert("end", f"{response}\n")
            text.tag_configure("user_text", foreground="grey")
            text.config(state="disabled")
            text.see(tk.END)
            textbox.delete(0, tk.END)
        else:
            messagebox.showwarning("Empty Input", "Please enter some text!")

        # Analyze the player's action in relation to the goal.
        status, reason, ending_line = check_goal(client, MODEL_NAME, DATA)
        if status == "progress":
            print(f"✅ Progress: {reason}")
            return

        if status == "game_over":
            ending_line = "Game Over: " + ending_line
            print(f"❌ Game Over: {reason}")
        elif status == "win":
            ending_line = "You Win: " + ending_line
            print(f"🎉 You Win! {reason}")

        text.config(state="normal")
        text.insert("end", f"\n{ending_line}\n")
        text.config(state="disabled")
        text.see(tk.END)
        textbox.delete(0, tk.END)

    # Submit button
    submit_button = tk.Button(root, text="Generate", command=on_submit)
    submit_button.pack(pady=10)

    def save():
        filename = DATA["story"]["title"] + ".json"
        file = open(filename, 'w')
        json.dump(DATA, file)
        file.close()

    # save button
    button = tk.Button(root, text="Save", command=save, width=10)
    button.place(relx=1.0, rely=1.0, anchor="se")

    # Run the application
    root.mainloop()


def run_mode1():

    root = tk.Tk()
    root.title("Story Creation")
    root.geometry("960x540")

    title_label = tk.Label(root, text="What is the title of the story?")
    title_label.pack(pady=2)
    title_box = tk.Entry(root, width=50)
    title_box.pack(pady=10)

    genre_label = tk.Label(root, text="What is the genre of the story?")
    genre_label.pack(pady=2)
    genre_box = tk.Entry(root, width=50)
    genre_box.pack(pady=10)

    num_char_label = tk.Label(
        root, text="How many Non-Player Characters would you like to add to the story (max 10)?")
    num_char_label.pack(pady=2)
    num_char_box = tk.Entry(root, width=50)
    num_char_box.pack(pady=10)

    story_label = tk.Label(
        root, text="Can you give us an overview of the story setup?")
    story_label.pack(pady=2)
    story_box = tk.Text(root, width=50, height=5)
    story_box.pack(pady=10)

    goal_label = tk.Label(
        root, text="What is the goal of the player character?")
    goal_label.pack(pady=2)
    goal_box = tk.Entry(root, width=50)
    goal_box.pack(pady=10)

    def on_submit():
        global DATA
        title = title_box.get()
        genre = genre_box.get()
        num_char = num_char_box.get()
        story = story_box.get("1.0", "end-1c")
        goal = goal_box.get()
        try:
            num_char = int(num_char)
        except ValueError:
            messagebox.showerror(
                "Invalid Number", "Please enter a valid number!")

        DATA["story"] = {
            "title": title.replace(" ", "_"),
            "genre": genre,
            "storyline": story,
            "goal": goal
        }
        root.destroy()
        for i in range(num_char):
            try:
                npc = create_char(i)
                DATA["chars"][npc["name"]] = npc
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Character creation failed: {str(e)}")

        prompt = get_starting_prompt(DATA)
        beginning_line = get_response(
            client, MODEL_NAME, prompt).choices[0].message.content
        DATA["target"] = "story"
        DATA["history"].append(["story", beginning_line])
        run_generation(beginning_line)

    next_button = tk.Button(root, text="Next", font=(
        "Arial", 16), command=on_submit, width=20)
    next_button.pack(pady=10)


def run_mode2():
    root = tk.Tk()
    root.title("Story Creation")
    root.geometry("960x540")

    title_label = tk.Label(
        root, text="What is the title of the story that you want to load?")
    title_label.pack(pady=2)
    title_box = tk.Entry(root, width=50)
    title_box.pack(pady=10)

    def on_submit():
        global DATA
        title = title_box.get()
        try:
            filename = title.replace(" ", "_") + ".json"
            with open(filename, 'r') as file:
                DATA = json.load(file)
            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Unable to open file: {str(e)}")
            return

        beginning_line = get_last_story_segment(DATA)
        run_generation(beginning_line)

    next_button = tk.Button(root, text="Next", font=(
        "Arial", 16), command=on_submit, width=20)
    next_button.pack(pady=10)


def main():
    # print("✨ Story Generator ✨")
    # print("1. Start New Story")
    # print("2. Exiting")

    root = tk.Tk()
    root.title("Main Menu")
    root.geometry("960x540")

    title_label = tk.Label(
        root, text="CSCI 566 Text To Game Engine", font=("Arial", 24))
    title_label.pack(pady=80)

    def run_1():
        run_mode1()
        root.destroy()

    def run_2():
        run_mode2()
        root.destroy()

    new_button = tk.Button(root, text="New Game", font=(
        "Arial", 16), command=run_1, width=30, height=3)
    new_button.pack(pady=10)

    new_button = tk.Button(root, text="Load Game", font=(
        "Arial", 16), command=run_2, width=30, height=3)
    new_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
