from openai import OpenAI
import json
import tkinter as tk
from tkinter import simpledialog, messagebox

temp_file = "data.txt"

GPT_api_key = "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"
Deepseek_api_key = "sk-edbde6ec754a48dba8bf6d3531985d70"

class PageCreateNPC(tk.Frame):
    def __init__(self, master, controller, num_npcs):
        super().__init__(master)
        self.controller = controller
        self.char_prompt = {}        
        self.num_npcs_created = 1
        self.num_npcs = num_npcs

        self.text_npcs_created = tk.StringVar()
        self.text_npcs_created.set(f"NPC Creation: 1 of {self.num_npcs}")

        self.npc_created_label = tk.Label(self, text=self.text_npcs_created.get(),
                              font=("Helvetica", 16))
        self.npc_created_label.pack(pady=2)        

        name_label = tk.Label(self, text="What is the name of your character?")
        name_label.pack(pady=2)
        self.name_box = tk.Entry(self, width=50)
        self.name_box.pack(pady=8)

        bg_label = tk.Label(self, text="please provide a brief description of the background of your character:")
        bg_label.pack(pady=2)
        self.bg_box = tk.Text(self, width=100, height=2)
        self.bg_box.pack(pady=8)

        act_label = tk.Label(self, text="please describe how you would like your character acts (mannerisms and traits):")
        act_label.pack(pady=2)
        self.act_box = tk.Text(self, width=100, height=2)
        self.act_box.pack(pady=8)

        info_label = tk.Label(self, text="What information does your character know?")
        info_label.pack(pady=2)
        self.info_box = tk.Text(self, width=100, height=2)
        self.info_box.pack(pady=8)

        init_label = tk.Label(self,
                            text="Where is this character and what are they doing at the beginning of the story?")
        init_label.pack(pady=2)
        self.init_box = tk.Entry(self, width=100)
        self.init_box.pack(pady=8)

        hello_label = tk.Label(self, text="how would your character respond to the following: \"Hello, how did you spend your day?\" ")
        hello_label.pack(pady=2)
        self.hello_box = tk.Text(self, width=100, height=2)
        self.hello_box.pack(pady=8)

        imp_label = tk.Label(self, text="how would your character respond to the following: \"What is the most important thing in the world to you?\" ")
        imp_label.pack(pady=2)
        self.imp_box = tk.Text(self, width=100, height=2)
        self.imp_box.pack(pady=8)

        help_label = tk.Label(self, text="how would your character respond to the following: \"Can you help me with something?\" ")
        help_label.pack(pady=2)
        self.help_box = tk.Text(self, width=100, height=2)
        self.help_box.pack(pady=8)

        note_label = tk.Label(self, text="What else you would like to add about your character that has not yet been covered?")
        note_label.pack(pady=2)
        self.note_box = tk.Text(self, width=100, height=2)
        self.note_box.pack(pady=8)

        auto_gen_button = tk.Button(self, text="Autogen NPC", command=self.debug_autogen_NPC)
        auto_gen_button.pack(pady=8)

        submit_button = tk.Button(self, text="Submit", command=self.on_submit)
        submit_button.pack(pady=8)

    def on_submit(self):
        self.char_prompt = {}
        self.char_prompt['name'] = self.name_box.get()
        self.char_prompt["background"] = self.bg_box.get("1.0", "end-1c")
        self.char_prompt["act"] = self.act_box.get("1.0", "end-1c")
        self.char_prompt["info"] = self.info_box.get("1.0", "end-1c")
        self.char_prompt["init"] = self.init_box.get()
        self.char_prompt["q_hello"] = self.hello_box.get("1.0", "end-1c")
        self.char_prompt["q_important"] = self.imp_box.get("1.0", "end-1c")
        self.char_prompt["q_help"] = self.help_box.get("1.0", "end-1c")
        self.char_prompt["notes"] = self.note_box.get("1.0", "end-1c")
        
        self.controller.DATA["chars"][self.char_prompt["name"]] = self.char_prompt

        if self.num_npcs_created < self.num_npcs:
            self.num_npcs_created += 1
            self.text_npcs_created.set(f"NPC Creation: {self.num_npcs_created} of {self.num_npcs}")
            self.npc_created_label.config(text=self.text_npcs_created.get())
            
            self.reset_form()
            # self.npc_created_label.config(text=f"NPC Creation: {self.num_npcs_created} of {self.num_npcs}")
        else:
            #TODO: Initialize game frame
            self.controller.generateStartingPrompts() #First line in run_convo
            self.controller.displayPageGameInterface()

    def reset_form(self):
        self.name_box.delete(0, tk.END)
        self.bg_box.delete("1.0", tk.END)
        self.act_box.delete("1.0", tk.END)
        self.info_box.delete("1.0", tk.END)
        self.init_box.delete(0, tk.END)
        self.hello_box.delete("1.0", tk.END)
        self.imp_box.delete("1.0", tk.END)
        self.help_box.delete("1.0", tk.END)
        self.note_box.delete("1.0", tk.END)

    def debug_autogen_NPC(self):
        prompt_template = {
            "task": "Create an NPC character within the scope of the world defined in 'input_story'. Output the response in the described JSON format.",
            "requirements": {
                "name": "Can be either a first name, first name and last name, nickname, or a description",
                "background": "2 - 3 sentences",
                "act": "Concise descriptions of personality and mannerisms (example: observant, pragmatic, dry sense of humor)",
                "info": "2 - 3 sentences",
                "init": "2 - 3 sentences, describing what the chraacter knows in relation to the story world",
                "responses": {
                    "q_hello": "2 sentences describing their typical response when someone says 'hello' to them.",
                    "q_important": "2 sentences describing their ideas, relationships, or goals most important to them",
                    "q_help": "2 sentences describing their typical response when someone asks them for help."
                }
            },
            "examples": {
                "input_sample": {
                    "genre": "Science Fiction",
                    "storyline": "In a fractured galaxy where humanity teeters on extinction after unearthing a volatile alien relic, you play a rogue mercenary thrust into a war between rival factions and ancient AI. Your choices determine whether to salvage civilization, harness the relic’s reality-bending power, or watch the cosmos collapse.",
                    "goal": "The player must decide whether to secure the alien relic to unite the warring factions, exploit its power for personal dominance, or let chaos consume the galaxy, shaping the fate of civilization and the cosmos"
                },
                "output_sample": {
                    "name": "Ronan Kade",
                    "background": "Ronan Kade is a former Imperial pilot who defected to the outer rim after witnessing atrocities committed by the Empire. Skilled in evasive maneuvers and covert operations, he now works as a freelance pilot and informant, navigating the shady alliances and shifting loyalties of spaceports and smugglers' dens.",
                    "act": "quiet intensity, observant, pragmatic, guarded in conversation, dry sense of humor",
                    "info": "Ronan knows Imperial procedures, flight paths, and secret communication frequencies. He has intelligence on hidden supply caches and safe houses scattered along the outer rim and maintains contacts within both rebel factions and black market networks.",
                    "init": "At the beginning of the story, Ronan Kade is at the same spaceport tavern, quietly seated at the bar observing the interactions between Captain Vorne, Zera-7, and Dr. Marakos. He is waiting for a contact to deliver critical information concerning Imperial patrols.",
                    "responses": {
                        "q_hello": "Kade glances briefly, still flipping the token. 'Avoiding Imperial entanglements, same as any day.'",
                        "q_important": "His eyes darken slightly, the token pausing momentarily. 'Freedom. And keeping a step ahead of the Empire.'",
                        "q_help" : "He evaluates cautiously, token resuming its dance. 'Depends. Is it likely to get me killed or just nearly?'"
                    }
                }
            },
            "input_story": self.controller.DATA["story"]
        }

        json_prompt_string = json.dumps(prompt_template)
        messages = [
            {
                "role": "system",
                "content": "You are a famous storywriter."
            },
            {
                "role": "user",
                "content": f"JSON Prompt:\n{json_prompt_string}"
            }   
        ]

        segments = None
        model = "mistral-saba-24b"
        client = OpenAI(
            api_key="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",
            base_url="https://api.groq.com/openai/v1"            
        )
        
        try: 
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.8,
                response_format={"type": "json_object"}             
            ) 

            segments = json.loads(response.choices[0].message.content)

        except Exception as e:
            print("Prompt operation failed")
            messagebox.showerror("Error", f"Character creation failed. Please run auto-gen again: {str(e)}")
            return 

        self.reset_form() #Clear previous fields in case a user wants to randomly generate a different character.
        self.name_box.insert(0, segments["name"])
        self.bg_box.insert("1.0", segments["background"])
        self.act_box.insert("1.0", segments["act"])
        self.info_box.insert("1.0", segments["info"])
        self.init_box.insert(0, segments["init"])
        self.hello_box.insert("1.0", segments["responses"]["q_hello"])
        self.imp_box.insert("1.0", segments["responses"]["q_important"])
        self.help_box.insert("1.0", segments["responses"]["q_help"])

#NOTE: Consider deleting function as its functionality has been moved over to the PageCreateNPC class. 
def create_char(num):
    char_prompt = {}

    # Create the main window
    root = tk.Tk()
    root.title(f"Character creation: Character number {num}")
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
    prompt_text = (
        f"Please continue this conversation acting as a character with the following details: \n"
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

    return prompt_text

def get_dev_message(initial, hist):
    message = initial

    message += "here is the conversation so far: \n"
    for i in hist:
        message += f"{i[0]}: {i[1]}"

    return message

def get_response(client, message, input):
    return client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": message},
            {"role": "user", "content": input},
        ],
        stream=False
    )

#NOTE: This function has been copied over to Main.py -> PageGameInterface.__init__()
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
    create_char()
