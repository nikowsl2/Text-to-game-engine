from openai import OpenAI
import json
import tkinter as tk
from tkinter import simpledialog, messagebox

temp_file = "data.txt"

GPT_api_key = "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"
Deepseek_api_key = "sk-edbde6ec754a48dba8bf6d3531985d70"


def create_char(num):
    char_prompt = {}

    # Create the main window
    root = tk.Tk()
    root.title(f"Character creation: CHaracter number {num}")
    root.geometry("1280x720")


    name_label = tk.Label(root, text="What is the name of your character?")
    name_label.pack(pady=2)
    name_box = tk.Entry(root, width=50)
    name_box.pack(pady=8)

    bg_label = tk.Label(root, text="please provide a brief description of the background of your character:")
    bg_label.pack(pady=2)
    bg_box = tk.Text(root, width=100, height=2)
    bg_box.pack(pady=8)

    act_label = tk.Label(root, text="please describe how you would like your character acts (mannerisms and traits):")
    act_label.pack(pady=2)
    act_box = tk.Text(root, width=100, height=2)
    act_box.pack(pady=8)

    info_label = tk.Label(root, text="What information does your character know?")
    info_label.pack(pady=2)
    info_box = tk.Text(root, width=100, height=2)
    info_box.pack(pady=8)

    init_label = tk.Label(root,
                          text="Where is this character and what are they doing at the beginning of the story?")
    init_label.pack(pady=2)
    init_box = tk.Entry(root, width=100)
    init_box.pack(pady=8)

    hello_label = tk.Label(root, text="how would your character respond to the following: \"Hello, how did you spend your day?\" ")
    hello_label.pack(pady=2)
    hello_box = tk.Text(root, width=100, height=2)
    hello_box.pack(pady=8)

    imp_label = tk.Label(root, text="how would your character respond to the following: \"What is the most important thing in the world to you?\" ")
    imp_label.pack(pady=2)
    imp_box = tk.Text(root, width=100, height=2)
    imp_box.pack(pady=8)

    help_label = tk.Label(root, text="how would your character respond to the following: \"Can you help me with something?\" ")
    help_label.pack(pady=2)
    help_box = tk.Text(root, width=100, height=2)
    help_box.pack(pady=8)

    note_label = tk.Label(root, text="What else you would like to add about your character that has not yet been covered?")
    note_label.pack(pady=2)
    note_box = tk.Text(root, width=100, height=2)
    note_box.pack(pady=8)

    # Function to handle button click
    def on_submit():
        char_prompt['name'] = name_box.get()

        char_prompt["background"] = bg_box.get("1.0", "end-1c")
        char_prompt["act"] = act_box.get("1.0", "end-1c")
        char_prompt["info"] = info_box.get("1.0", "end-1c")
        char_prompt["init"] = init_box.get()

        char_prompt["q_hello"] = hello_box.get("1.0", "end-1c")
        char_prompt["q_important"] = imp_box.get("1.0", "end-1c")
        char_prompt["q_help"] = help_box.get("1.0", "end-1c")

        char_prompt["notes"] = note_box.get("1.0", "end-1c")

        root.destroy()
    # Submit button
    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=8)

    root.mainloop()
    return char_prompt


def get_initial_prompt(data, char_name):
    return (f"Please continue this conversation acting as a character with the following details: \n"
            f"Your name is: {char_name}\n"
            f"Your have the following background: {data['chars'][char_name]['background']} \n"
            f"You behave in this way: {data['chars'][char_name]['act']}\n"
            f"The only information you know is: {data['chars'][char_name]['info']}. You do not know anything beyond the mentioned scope \n"
            f"Here are some examples of inputs and how you should respond:\n"
            f"Input: \"Hello, how did you spend your day?\"\n"
            f"Response: {data['chars'][char_name]['q_hello']}\n"
            "Input: \"What is the most important thing in the world to you?\"\n"
            f"Response: {data['chars'][char_name]['q_important']}\n"
            "Input: \"Can you help me with something?\"\n"
            f"Response: {data['chars'][char_name]['q_help']}\n"
            f"And here is some more information about you: {data['chars'][char_name]['notes']}\n"
            )

def get_dev_message(initial, hist):
    message = initial

    message += "here is the conversation so far: \n"
    for i in hist:
        message += f"{i[0]}: {i[1]}"

    return message

def get_response(client, model_name, message, input):
    if model_name == "claude-3-opus-20240229":
        return client.messages.create(
            model=model_name,
            temperature=0.6,
            max_tokens=1000,
            system=message,
            messages=[
                {"role": "user", "content": input}
            ]
        )
    elif model_name == "mistral-large-latest":
        return client.chat.complete(
            model=model_name,  # or "mistral-small"
            messages=[
                {"role": "system",
                 "content": message},
                {"role": "user", "content": input}
            ]
        )
    else:
        return client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": message},
                {"role": "user", "content": input},
            ],
            stream=False
        )

def run_convo(char_prompt):
    prompt = get_initial_prompt(char_prompt)
    conversion_history = []

    client = OpenAI(
        api_key="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",
        base_url="https://api.groq.com/openai/v1"
    )

    # Create the main window
    root = tk.Tk()
    root.title("NPC conversation generation")
    root.geometry("800x500")

    # Create a Text widget (editable multi-line text)
    text = tk.Text(
        root,
        height=20,  # Number of lines
        width=50,  # Width in characters
        font=("Arial", 12),
        wrap=tk.WORD,  # Wrap text at word boundaries
    )
    text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    text.insert("1.0", "your conversation will be displayed below!\n")
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
        dv = get_dev_message(prompt, conversion_history)
        response = get_response(client, dv, user_text)
        if user_text:
            text.config(state="normal")
            text.insert("end", f"You: {user_text}\n")
            text.insert("end", f"{char_prompt['name']}: {response.choices[0].message.content}\n")
            text.config(state="disabled")
            text.see(tk.END)
            conversion_history.append(["User", user_text])
            conversion_history.append([char_prompt['name'], response.choices[0].message.content])
            textbox.delete(0, tk.END)
        else:
            messagebox.showwarning("Empty Input", "Please enter some text!")

    # Submit button
    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.pack(pady=10)

    # Run the application
    root.mainloop()


if __name__ == "__main__":
    create_char(1)
