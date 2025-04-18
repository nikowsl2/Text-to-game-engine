from openai import OpenAI
import json
import os
import time
import re
import tkinter as tk
import chromadb

import NPC
import MemoryAgent

from tkinter import messagebox
from NPC import create_char, get_initial_prompt, get_dev_message, get_response
from StoryGenerator import get_starting_prompt, format_characters, get_last_story_segment, story_generation, check_goal
from sentence_transformers import SentenceTransformer

#Debugging Variables
B_DEBUG_MODE = True
B_PERSIST_ENTRIES = False

HISTORY_FILE = "history.json"
PROTAGONISTS_FILE = "protagonists.json"
MODEL_NAME = "llama3-8b-8192"

#Variables for Vector DB
DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

DATA = {
    "chars": {},
    "history": []
}

CLIENT = OpenAI(
        api_key="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",
        base_url="https://api.groq.com/openai/v1"
    )

def get_client():
    return OpenAI(
        api_key="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",
        base_url="https://api.groq.com/openai/v1"
    )

#New Story Creation
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

    num_char_label = tk.Label(root, text="How many Non-Player Characters would you like to add to the story (max 10)?")
    num_char_label.pack(pady=2)
    num_char_box = tk.Entry(root, width=50)
    num_char_box.pack(pady=10)

    story_label = tk.Label(root, text="Can you give us an overview of the story setup?")
    story_label.pack(pady=2)
    story_box = tk.Text(root, width=50, height=5)
    story_box.pack(pady=10)

    goal_label = tk.Label(root, text="What is the goal of the player character?")
    goal_label.pack(pady=2)
    goal_box = tk.Entry(root, width=50)
    goal_box.pack(pady=10)

    def on_submit():
        title = title_box.get()
        genre = genre_box.get()
        num_char = num_char_box.get()
        story = story_box.get("1.0", "end-1c")
        goal = goal_box.get()
        try:
            num_char = int(num_char)
        except ValueError:
            messagebox.showerror("Invalid Number", "Please enter a valid number!")

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
                messagebox.showerror("Error", f"Character creation failed: {str(e)}")

        prompt = get_starting_prompt(DATA)
        beginning_line = get_response(CLIENT, MODEL_NAME, prompt).choices[0].message.content
        DATA["target"] = "story"
        DATA["history"].append(["story", beginning_line])
        run_generation(beginning_line)

    next_button = tk.Button(root, text="Next", font=("Arial", 16), command=on_submit, width=20)
    next_button.pack(pady=10)

#Load Story Creation - based on code from StoryGenerator.
def run_mode2():
    root = tk.Tk()
    root.title("Story Creation")
    root.geometry("960x540")

    title_label = tk.Label(root, text="What is the title of the story that you want to load?")
    title_label.pack(pady=2)
    title_box = tk.Entry(root, width=50)
    title_box.pack(pady=10)

    def on_submit():
        title = title_box.get()
        try:
            filename = title.replace(" ", "_") + ".json"
            with open(filename, 'r') as file:
                DATA = json.load(file)
            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Unable to open file: {str(e)}")

        beginning_line = get_last_story_segment(DATA)
        run_generation(beginning_line)

    next_button = tk.Button(root, text="Next", font=("Arial", 16), command=on_submit, width=20)
    next_button.pack(pady=10)

class AppEngine(tk.Tk):
    """
        Main App Engine. Holds the variables accessed by every page frame within the App.
    """
    def __init__(self, dlgResWidth=1280, dlgResHeight=960):
        super().__init__()
        self.title("CSCI 566 Text To Game Engine")
        self.dlgResWidth = dlgResWidth
        self.dlgResHeight = dlgResHeight
        self.geometry(f"{self.dlgResWidth}x{self.dlgResHeight}")
        self.debug_mode = B_DEBUG_MODE                

        #Note: All created frames have access to set/get values from DATA.
        self.DATA = {
            "chars": {},
            "history": []
        }
        self.beginning_line = None #The initial prompt displayed.
        self.story_memory = None
        self.npc_memory = None
        self.json_story_summary = None

        self.timestamp_lastPassage = None
        
        # Create a container frame to hold all the pages
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        
        # Configure grid layout to make sure the frame expands
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Dictionary to hold the pages
        self.frames = {}
        
        # Initialize and stack pages in the same location
        for F in (MainInterface, PageNewStory, PageLoadStory):
            page_name = F.__name__
            frame = F(master=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        # Show the master page first
        self.show_frame("MainInterface")
        
    def show_frame(self, page_name):
        """Bring the specified frame (page) to the front."""
        frame = self.frames[page_name]
        frame.tkraise()

    def generateStartingPrompts(self):
        prompt = get_starting_prompt(self.DATA)
        beginning_line = get_response(CLIENT, MODEL_NAME, prompt).choices[0].message.content

        self.DATA["target"] = "story"
        self.DATA["history"].append(["story", beginning_line])
        self.beginning_line = beginning_line

    def initializePageNpc(self, num_npcs):
        page_name = NPC.PageCreateNPC.__name__
        frame = NPC.PageCreateNPC(master=self.container, controller=self, num_npcs=num_npcs)
        self.frames[page_name] = frame
        frame.grid(row=0, column=0, sticky="nsew")

    def initializePageGameInterface(self, beginning_line):
        page_name = PageGameInterface.__name__
        frame = PageGameInterface(master=self.container, controller=self, beginning_line=beginning_line)
        self.frames[page_name] = frame
        frame.grid(row=0, column=0, sticky="nsew")
    
    def initializeStoryMemory(self, beginning_line):    
        story_title = self.DATA["story"]["title"]                   
        story_passages_name = f"story_passages_{story_title}"
        story_entities_name = f"story_entities_{story_title}"
        self.story_memory = MemoryAgent.StoryAgent(entities_collection_name=story_entities_name, 
                                                   passages_collection_name=story_passages_name, 
                                                   embedding_model=EMBEDDING_MODEL)

        self.AddNewStoryPassage(beginning_line)
        #Add initial story passage. 

    def AddNewStoryPassage(self, response, user_text=""):
        self.json_story_summary = self.story_memory.extract_story_segment(response)

        if B_DEBUG_MODE:
            self.saveToJson()

        story_passage_metadata = {            
            "setting_id": self.json_story_summary ["setting_atmosphere"][0]["id"],
            "setting_description": self.json_story_summary ["setting_atmosphere"][0]["description"],
            "setting_mood": self.json_story_summary ["setting_atmosphere"][0]["mood"], 
            "key_events": ", ".join([event["id"] for event in self.json_story_summary ["key_events"]]),            
        } 

        #Add additional metadata depending on scenario.
        if user_text != "":
            story_passage_metadata["user_prompt"] = user_text

        passageId = self.story_memory.add_story_passage(response, story_passage_metadata)
        self.story_memory.add_story_metadata(self.json_story_summary, passageId)
        self.timestamp_lastPassage = passageId        

    def initializeNPCMemory(self):
        story_title = self.DATA["story"]["title"]   
        npc_collection_name = f"npc_collection_{story_title}"
        npc_interactions_name = f"npc_interactions_{story_title}"

        self.npc_memory = MemoryAgent.NPCAgent(npc_collection_name=npc_collection_name,
                                               npc_interactions_name=npc_interactions_name,
                                               embedding_model=EMBEDDING_MODEL)
        
        #Add initial npcs. 
        #TODO: Consider storing in separate function
        self.npc_memory.add_npcs(self.DATA)

    def AddNPCs(self):
        self.npc_memory.add_npcs(self.DATA)

    def displayPageGameInterface(self):
        self.initializeStoryMemory(self.beginning_line)
        self.initializeNPCMemory()
        self.initializePageGameInterface(self.beginning_line)
        self.show_frame("PageGameInterface")

    def classifier(self, client, user_input):
        return client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": f"""You are a classifier. Your job is to determine the user's intent with his input."""},
                {"role": "user", "content": f"""
                        Given the user's input, determine if they would like to switch from the story generator to conversing with one of the characters or vice-versa.
                If the user input is directed at the story generator, respond with \"story\".
                If the user input is directed at a character, respond with the Character's name. Make sure that the character name you respond with is \
                part of the following: {list(self.DATA["chars"].keys())}
                
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
                {format_characters(self.DATA)}
                
                Conversation History:
                {get_last_story_segment(self.DATA)}
                
                Remember to respond ONLY with "story" or a character's name. Do not include any other information in the response.
                Also remember that if you respond with a character's name, it MUST be included in the following list {list(self.DATA["chars"].keys())}.
                DO NOT respond with a name not on the provided list. Your only valid responses are names from that list or "story".
                
                
                The current conversation agent: {self.DATA["target"]}
                User Input: {user_input}
                """},
            ],
            stream=False
        )
    
    def saveToJson(self):
        filename = self.DATA["story"]["title"] + ".json"
        file = open(filename, 'w')
        json.dump(self.DATA, file, indent=4)
        file.close()

class MainInterface(tk.Frame):
    """
        The initial page that is displayed when starting up the game.
    """
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.page_title_name = "CSCI 566 Text To Game Engine"
    
        title_label = tk.Label(self, text=self.page_title_name, font=("Arial", 24))
        title_label.pack(pady=80)

        new_button = tk.Button(self, text="New Game", font=("Arial", 16), 
                               command=lambda: controller.show_frame("PageNewStory"), width=30, height=3)
        new_button.pack(pady=10)

        new_button = tk.Button(self, text="Load Game", font=("Arial", 16), 
                               command=lambda: controller.show_frame("PageLoadStory"), width=30, height=3)
        new_button.pack(pady=10)
        
class PageNewStory(tk.Frame):
    """
        New Story Creation page
    """
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        
        # Label for the master page
        label = tk.Label(self, text="New Story Creation", font=("Helvetica", 24))
        label.pack(pady=10)

        title_label = tk.Label(self, text="What is the title of the story?")
        title_label.pack(pady=2)
        self.title_box = tk.Entry(self, width=50) 
        self.title_box.pack(pady=10)

        genre_label = tk.Label(self, text="What is the genre of the story?")
        genre_label.pack(pady=2)
        self.genre_box = tk.Entry(self, width=50)
        self.genre_box.pack(pady=10)

        num_char_label = tk.Label(self, text="How many Non-Player Characters would you like to add to the story (max 10)?")
        num_char_label.pack(pady=2)
        self.num_char_box = tk.Entry(self, width=50)
        self.num_char_box.pack(pady=10)

        story_label = tk.Label(self, text="Can you give us an overview of the story setup?")
        story_label.pack(pady=2)
        self.story_box = tk.Text(self, width=50, height=5)
        self.story_box.pack(pady=10)

        goal_label = tk.Label(self, text="What is the goal of the player character?")
        goal_label.pack(pady=2)
        self.goal_box = tk.Entry(self, width=50)
        self.goal_box.pack(pady=10)

        back_button = tk.Button(self, text="Back", font=("Arial", 16),
                                 command=lambda: controller.show_frame("MainInterface"), width=20)
        back_button.pack(pady=10)                     
        next_button = tk.Button(self, text="Next", font=("Arial", 16), 
                                command=self.event_btnOnClick, width=20)
        next_button.pack(pady=10)

        if B_DEBUG_MODE:
            self.debug_autoPopulateFields()
    
    def event_btnOnClick(self):
        self.controller.DATA["story"] = {
            "title": self.title_box.get().replace(" ", "_"),
            "genre": self.genre_box.get(),
            "storyline": self.story_box.get("1.0",'end-1c'),
            "goal": self.goal_box.get()
        } 
                
        numNPCs = int(self.num_char_box.get())
        if numNPCs > 0:
            self.controller.num_npcs = numNPCs

            #Initialize Create NPC Frame
            self.controller.initializePageNpc(numNPCs)            
            self.controller.show_frame("PageCreateNPC")
        else:
            self.generateStartingPrompts()
            self.controller.initializePageGameInterface()

    def debug_autoPopulateFields(self):
        #Auto-populate fields for debugging purposes
        story_description = """In a fractured galaxy where humanity teeters on extinction after unearthing a volatile alien relic, you play a rogue mercenary 
        thrust into a war between rival factions and ancient AI. Your choices determine whether to salvage civilization, harness the relic’s reality-bending 
        power, or watch the cosmos collapse."""        
        story_goal = """The player must decide whether to secure the alien relic to unite the warring factions, exploit its power for personal dominance, 
        or let chaos consume the galaxy, shaping the fate of civilization and the cosmos"""
        story_description = story_description.replace('\r', '').replace('\n', '')
        story_goal = story_goal.replace('\r', '').replace('\n', '')

        self.title_box.insert(0, "Test")
        self.genre_box.insert(0, "Science Fiction")
        self.num_char_box.insert(0, 1)
        self.story_box.insert("1.0", story_description)
        self.goal_box.insert(0, story_goal)
        #End debug fields        

class PageLoadStory(tk.Frame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        
        label = tk.Label(self, text="Load Story", font=("Helvetica", 24))
        label.pack(pady=10)

        title_label = tk.Label(self, text="What is the title of the story that you want to load?")
        title_label.pack(pady=2)
        self.title_box = tk.Entry(self, width=50)
        self.title_box.pack(pady=10)        
                
        back_button = tk.Button(self, text="Back", font=("Arial", 16),
                                 command=lambda: controller.show_frame("MainInterface"), 
                                 width=20)
        back_button.pack(pady=10)

        next_button = tk.Button(self, text="Next", font=("Arial", 16), command=self.event_btnOnClick, 
                                width=20)
        next_button.pack(pady=10) 

    def event_btnOnClick(self):
        title = self.title_box.get()
        try:
            filename = title.replace(" ", "_") + ".json"
            with open(filename, 'r') as file:
                self.controller.DATA = json.load(file)

        except Exception as e:
            messagebox.showerror("Error", f"Unable to open file: {str(e)}")

        beginning_line = get_last_story_segment(self.controller.DATA)
        run_generation(beginning_line)

class PageGameInterface(tk.Frame):
    def __init__(self, master, controller, beginning_line):
        super().__init__(master)
        self.controller = controller
                        
        # Create a Text widget (editable multi-line text)
        self.text = tk.Text(
            self,
            height=20,  # Number of lines
            width=50,  # Width in characters
            font=("Arial", 12),
            wrap=tk.WORD,  # Wrap text at word boundaries
        )

        self.text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.text.insert("1.0", f"{beginning_line}\n")
        self.text.config(state="disabled")

        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.text, command=self.text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=self.scrollbar.set)

        # Label
        label = tk.Label(self, text="Enter your text below:")
        label.pack(pady=10)

        # Textbox (Entry widget)
        self.textbox = tk.Entry(self, width=100)
        self.textbox.pack(pady=10)

        #save button
        button = tk.Button(self, text="Save", command=self.save, width=10)
        button.place(relx=1.0, rely=1.0, anchor="se")    

        # Submit button
        submit_button = tk.Button(self, text="Submit", command=self.on_submit)
        submit_button.pack(pady=10)            

    # Function to handle button click
    def on_submit(self):
        user_text = self.textbox.get()
        input_type = self.controller.classifier(CLIENT, user_text).choices[0].message.content
        print(input_type)
        response = None

        if input_type == "story":
            response = story_generation(CLIENT, MODEL_NAME, self.controller.DATA, user_text)

            self.controller.DATA["history"].append(["User", user_text])
            self.controller.DATA["history"].append([input_type, response])

            self.controller.AddNewStoryPassage(response, user_text)

        elif input_type in self.controller.DATA["chars"].keys():
            dv = get_dev_message(get_initial_prompt(self.controller.DATA, input_type), self.controller.DATA["history"])
            response = get_response(CLIENT, dv, user_text).choices[0].message.content

            self.controller.DATA["history"].append(["User", user_text])
            self.controller.DATA["history"].append([input_type, response])

            self.controller.AddNewStoryPassage(response, user_text)

        else:
            messagebox.showerror("An issue occured!", "Uh Oh, the AI is stupid and can't process your input")

        if response is not None:
            self.text.config(state="normal")
            self.text.insert("end", f"You: {user_text}\n")
            self.text.insert("end", f"{response}\n")
            self.text.config(state="disabled")
            self.text.see(tk.END)
            self.textbox.delete(0, tk.END)

        else:
            messagebox.showwarning("Empty Input", "Please enter some text!")

        # Analyze the player's action in relation to the goal.
        status, reason, ending_line = check_goal(CLIENT, MODEL_NAME, self.controller.DATA)
        if status == "progress":
            print(f"✅ Progress: {reason}")
            return

        if status == "game_over":
            ending_line = "Game Over: " + ending_line
            print(f"❌ Game Over: {reason}")
        elif status == "win":
            ending_line = "You Win: " + ending_line
            print(f"🎉 You Win! {reason}")

        self.text.config(state="normal")
        self.text.insert("end", f"\n{ending_line}\n")
        self.text.config(state="disabled")
        self.text.see(tk.END)
        self.textbox.delete(0, tk.END)

    def save(self):
        filename = self.controller.DATA["story"]["title"] + ".json"
        file = open(filename, 'w')
        json.dump(self.controller.DATA, file)
        file.close()

if __name__ == "__main__":
   db_client = chromadb.PersistentClient(path=DB_PATH) 

   #Clear out database if persistent entries are not desired.
   if not B_PERSIST_ENTRIES:
    collections = db_client.list_collections()
    for collection in collections:
        db_client.delete_collection(collection)

    app = AppEngine(dlgResWidth=1280, dlgResHeight=900)
    app.mainloop()