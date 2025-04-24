from openai import OpenAI
import anthropic
import mistralai
import json
import tkinter as tk
from tkinter import messagebox
from NPC import create_char, get_initial_prompt, get_dev_message, get_response
from StoryGenerator import get_starting_prompt,get_initial_gen, format_characters, get_last_story_segment, story_generation, parse_new_characters, check_goal


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
deepseek = OpenAI(
    api_key= "sk-3d29f5f4fee64e2390f2525640f57ba7",
    base_url= "https://api.deepseek.com/"
)
DEEPSEEK_MODEL_NAME = "deepseek-chat"

gpt = OpenAI(api_key="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")
GPT_MODEL_NAME = "gpt-4.1-2025-04-14"

claude = anthropic.Anthropic(api_key="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")
CLAUDE_MODEL_NAME = "claude-3-opus-20240229"

mistral = mistralai.Mistral(api_key="e7DlAIjT1Nen1Bje2Mb9uDarABQ4iOmD")
MISTRAL_MODEL_NAME = "mistral-large-latest"

def get_client():
    return client

def get_response_content(response):
    global MODEL_NAME
    if MODEL_NAME == "claude-3-opus-20240229":
        return response.content[0].text
    else:
        return response.choices[0].message.content

def classifier(client, user_input):
    if MODEL_NAME == "claude-3-opus-20240229":
        return client.messages.create(
            model=MODEL_NAME,
            temperature=0.6,
            max_tokens=1000,
            system=f"""You are a classifier. Your job is to determine the user's intent with his input.""",
            messages=[
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
                """}
            ]
        )
    elif MODEL_NAME == "mistral-large-latest":
        return client.chat.complete(
            model=MODEL_NAME,  # or "mistral-small"
            messages=[
                {"role": "system",
                 "content": f"""You are a classifier. Your job is to determine the user's intent with his input."""},
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
                """}
            ]
        )
    else:
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
        input_type = get_response_content(classifier(client, user_text))
        print(input_type)
        response = None
        if user_text:
            if input_type == "story":
                response = get_response_content(story_generation(client, MODEL_NAME, DATA, user_text))
                DATA["history"].append(["User", user_text])
                DATA["history"].append([input_type, response])
                DATA = parse_new_characters(response,client, DATA, MODEL_NAME)
            elif input_type in DATA["chars"].keys():
                dv = get_dev_message(get_initial_prompt(
                    DATA, input_type), DATA["history"])
                response = get_response_content(get_response(
                    client, MODEL_NAME, dv, user_text))
                DATA["history"].append(["User", user_text])
                DATA["history"].append([input_type, response])
            else:
                messagebox.showerror(
                    "An issue occured!", "Uh Oh, the AI is stupid and can't process your input")
        else:
            messagebox.showwarning("Empty Input", "Please enter some text!")
        text.config(state="normal")
        text.insert("end", f"\n")
        text.insert("end", f"You: {user_text}\n\n", "user_text")
        text.insert("end", f"{response}\n")
        text.tag_configure("user_text", foreground="grey")
        text.config(state="disabled")
        text.see(tk.END)
        textbox.delete(0, tk.END)


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

def select_model(mode):
    model_selection = tk.Tk()
    model_selection.title("Model Selection")
    model_selection.geometry("960x540")

    big_label = tk.Label(model_selection, text="Please Select an LLM to run your story on", font=("Arial", 24))
    big_label.pack(pady=10)

    def choose_Llama():
        model_selection.destroy()
        if mode == "mode2":
            run_mode2()
        else:
            run_mode1()

    llama_button = tk.Button(model_selection, text="Llama", command=choose_Llama)
    llama_button.pack(pady=10)

    def choose_deepseek():
        global client
        client = deepseek
        global MODEL_NAME
        MODEL_NAME = DEEPSEEK_MODEL_NAME
        model_selection.destroy()
        if mode == "mode2":
            run_mode2()
        else:
            run_mode1()

    llama_button = tk.Button(model_selection, text="DeepSeek", command=choose_deepseek)
    llama_button.pack(pady=10)

    def choose_gpt():
        global client
        client = gpt
        global MODEL_NAME
        MODEL_NAME = GPT_MODEL_NAME
        model_selection.destroy()
        if mode == "mode2":
            run_mode2()
        else:
            run_mode1()

    llama_button = tk.Button(model_selection, text="ChatGPT", command=choose_gpt)
    llama_button.pack(pady=10)

    def choose_claude():
        global client
        client = claude
        global MODEL_NAME
        MODEL_NAME = CLAUDE_MODEL_NAME
        model_selection.destroy()
        if mode == "mode2":
            run_mode2()
        else:
            run_mode1()

    llama_button = tk.Button(model_selection, text="Claude", command=choose_claude)
    llama_button.pack(pady=10)

    def choose_mistral():
        global client
        client = mistral
        global MODEL_NAME
        MODEL_NAME = MISTRAL_MODEL_NAME
        model_selection.destroy()
        if mode == "mode2":
            run_mode2()
        else:
            run_mode1()

    llama_button = tk.Button(model_selection, text="Mistral", command=choose_mistral)
    llama_button.pack(pady=10)

def run_mode1():

    global MODEL_NAME
    print(MODEL_NAME)

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
        beginning_line = get_response_content(get_initial_gen(
            client, MODEL_NAME, prompt))
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
        select_model("mode1")
        root.destroy()

    def run_2():
        select_model("mode2")
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
