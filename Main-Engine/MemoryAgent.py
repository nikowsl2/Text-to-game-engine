import chromadb
import datetime
# import textwrap #For breaking up the story text into chunks.

import json
import openai

# from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
# from transformers import pipeline

B_DEBUG_MODE = True
B_PERSIST_ENTRIES = False
MODEL_TRANSFORMER = "all-MiniLM-L6-v2"

#Test Input Text
npc_entries_old = [
  {
    "name": "Captain Elias Vorne",
    "role": "Aging spaceship commander",
    "characteristics": "Cynical, laser-scarred face, whiskey voice",
    "backstory": "Former war hero now hauling illegal cargo to pay medical debts"
  },
  {
    "name": "Zera-7",
    "role": "Experimental android",
    "characteristics": "Golden ocular implants, emotion chip malfunction",
    "backstory": "Prototype that gained sentience and destroyed its creators"
  },
  {
    "name": "Dr. Lin Marakos",
    "role": "Rogue xenobiologist",
    "characteristics": "Always wears environmental suit, tremor in left hand",
    "backstory": "Sole survivor of first contact disaster that wiped out her colony"
  }
]

npc_entries = {
    "chars": {
        "Lyra Kaine": {
            "name": "Lyra Kaine",
            "background": "Lyra Kaine is a former archaeologist turned mercenary, specializing in recovering and deciphering ancient alien artifacts. After losing her team in a failed excavation, she now works alone, navigating the treacherous waters of galactic politics and deadly factions.",
            "act": "Analytical, resourceful, cautious, and fiercely independent, Lyra has a penchant for meticulous planning and quick decision-making under pressure.",
            "info": "Lyra is an expert in ancient alien languages and technologies, particularly those related to the recently unearthed relic. She has unparalleled knowledge of its potential uses and risks, as well as connections to various factions and black market dealers.",
            "init": "At the beginning of the story, Lyra Kaine is on a remote research station, carefully examining a new piece of the alien relic. She receives a distressing message revealing that her old patron has been compromised, forcing her to flee and seek allies in the chaos of the warring factions.",
            "q_hello": "Lyra adjusts her glasses, eyes narrowing slightly. 'I haven't seen you before. Who are you, and what brings you here?'",
            "q_important": "Her expression turns serious, her eyes focused on the horizon. 'Preserving knowledge and protecting humanity from the consequences of unchecked power.'",
            "q_help": "She assesses you carefully, her eyes sharp. 'I can offer information or tools, but I won't risk my life unless it benefits us both.'",
            "notes": ""
        },
        "Elysia Vance": {
            "name": "Elysia Vance",
            "background": "Elysia Vance is a former diplomat turned information broker, navigating the treacherous landscape of interstellar politics. With a knack for deciphering coded messages and negotiating between warring factions, she now operates from the shadows, selling valuable intel to the highest bidder.",
            "act": "calculating, charismatic, enigmatic, always carrying a small device for decrypting signals",
            "info": "Elysia has extensive knowledge of political intricacies and covert communication methods used by various factions. She has a network of informants and hackers who provide her with exclusive data, making her an invaluable asset in the information war.",
            "init": "Elysia enters the crowded spaceport bar, her eyes scanning the patrons as she receives a encrypted message on her device. She knows that the alien relic's power could either unite the factions or plunge the galaxy into chaos, and she's determined to play her cards right to ensure her survival and perhaps, shape the future of civilization.",
            "q_hello": "She raises an eyebrow slightly, 'Greetings. What brings you to this end of the galaxy?'",
            "q_important": "'Stability. And making sure the right information gets to the right hands at the right time.'",
            "q_help": "She leans in, 'I can't promise anything, but if it's worth my time, I'll consider it.'",
            "notes": ""
        }
    }
}

#Note that story_text was accomplished via the generator.
old_story_text = 'As I entered the dingy spaceport tavern, the smoke-filled air clung to my skin like a bad omen. ' \
'I scanned the room, my eyes adjusting to the dim light, searching for the guild representative. That\'s when I spotted them ' \
'Captain Elias Vorne, his laser-scarred face a map of battle-hardened experience, his whiskey-roughened voice booming across ' \
'the room.He sat at a corner table, sipping a questionable-looking drink, his eyes fixed on me with a mixture of curiosity ' \
'and calculation. Zera-7, the golden-eyed android, stood by his side, its malfunctioning emotion chip flickering like a ' \
'malfunctioning neon sign. The air around them seemed to vibrate with tension, like a coiled spring waiting to snap.As I ' \
'approached, Dr. Lin Marakos, the xenobiologist, slipped into the shadows, her environmental suit a stark contrast to the ' \
'squalor around us. Her left hand trembled as she lit a cigarette, the flame casting an eerie glow on her ravaged face. ' \
'Rumors whispered that she was the last survivor of the infamous first contact disaster that wiped out her colony. The ' \
'weight of her gaze made my skin crawl."Ah, you must be the young merc I\'ve been expecting," Captain Vorne growled, his ' \
'voice like a rusty gate. "I\'ve got a job that requires... particular skills. Zera-7 here can vouch for my reputation." ' \
'The android\'s gaze flickered, as if struggling to process its programming. "We need someone to retrieve a shipment from ' \
'the outer rim. Payment is negotiable, but the risk is high."As I hesitated, the doctor\'s cigarette butt dropped, hissing ' \
'against the worn floorboards. "Be careful, you don\'t know who you\'re dealing with. This job\'s got... consequences." ' \
'Captain Vorne\'s eyes glinted with a hint of menace, while Zera-7\'s malfunctioning chip sparked with an unsettling fervor. ' \
'The air seemed to charge with anticipation, like a storm about to break. And then, just as I was about to agree, the comms ' \
'device on Captain Vorne\'s wrist beeped, a message flashing in red letters: " Warning: Imperial Customs Interceptors spotted ' \
'in the vicinity. Attempting to intercept your vessel."The room seemed to tilt, as if the very fabric of space itself was ' \
'unraveling. Captain Vorne\'s face turned granite-hard, Zera-7\'s chip flickered wildly, and Dr. Marakos\'s gaze locked onto ' \
'mine with an unnerving intensity. And I knew, in that moment, I was in over my head.'

story_text = """Lyra Kaine's eyes narrowed as she examined the latest piece of the alien relic, her mind racing with the 
implications of its discovery. She was deep in thought when her comms device crackled to life, breaking the silence of the 
remote research station.\n\n\"Lyra, this is Ari. I've been compromised. The Syndicate has taken control of our operation, 
and they're coming for us. Get out, Lyra, you're the only one who can stop them,\" the voice on the other end was frantic, 
sent by her old patron, the infamous artifact smuggler.\n\nLyra's hand tightened around the relic, her analytical mind 
quickly processing the situation. She knew the Syndicate was a ruthless organization, willing to do whatever it took to get 
their hands on powerful relics like this one. With a surge of adrenaline, Lyra quickly packed her gear, her eyes darting 
around the research station for any signs of unwanted visitors.\n\nAs she made her way to the exit, Lyra's thoughts turned 
to Elysia Vance, an information broker she had done business with in the past. Elysia might be the only one who could help 
her navigate the treacherous landscape of galactic politics and rival factions. Lyra slid the relic into her pack and made 
her way off-world, ready to face whatever lay ahead.\n\nAcross the galaxy, Elysia Vance walked into the crowded spaceport 
bar, her eyes scanning the rows of patrons. She was a master of blending in, her calculated movements and enigmatic smile 
allowing her to gather information without drawing attention to herself. As she made her way to the bar, her device beeped, 
signaling an encrypted message from one of her unknown contacts.\n\nElysia's eyes locked onto the screen, her mind racing 
with the implications of the message. The relic, rumored to be able to bend reality itself, was the key to the galaxy's 
future. If she could get her hands on it, she might be able to shape the course of events, ensuring her survival and perhaps 
even bringing about a new era of peace.\n\nAs she finished her drink, Elysia gazed out at the crowded bar, her eyes narrowing 
in calculation. She knew the risk was high, but the potential reward was too great to ignore. Now, she just needed to find 
out where the relic was, and who was behind its recent resurgence into the galaxy.\n\nFor Lyra and Elysia, the fate of the 
galaxy was about to take a dramatic turn. The choices they made would determine whether to salvage civilization, harness the 
relic's power, or watch the cosmos collapse. The journey was just beginning, and the outcome was far from certain.
"""

class MemoryAgent:
    def __init__(self, embedding_model="all-MiniLM-L6-v2",
                 db_path="./chroma_db"):
        # Initialize the Chroma client and collection
        self.client = chromadb.PersistentClient(db_path)
        self.embedding_model = SentenceTransformer(embedding_model)

        # Create or get the collection
        self._collections: dict[str, chromadb.Collection] = {}

    def get_collection(self, name: str) -> chromadb.Collection:
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(name=name)

        return self._collections[name]
    
    def add_memory(self, collection: str, **kwargs):
        self.get_collection(collection).add(**kwargs)

    def retrieve_memory(self, collection: str, **kwargs):
        return self.get_collection(collection).query(**kwargs)

    def update_memory(self, collection: str, **kwargs):
        self.get_collection(collection).update(**kwargs)

    def remove_memory(self, collection: str, **kwargs):
        self.get_collection(collection).delete(**kwargs)

    def old_add_memory(self, item_id: str, embeddings: list,  content: str = None, metadata: dict = {}):
        """
        Adds a new piece of memory (text + metadata) to the collection.
        Each memory item has a unique item_id used for future retrieval or updates.
        """
        self.collection.add(
            ids=[item_id],
            documents=[content],
            embeddings=embeddings,
            metadatas=[metadata],            
        )

        if B_DEBUG_MODE:
            print(f"[MemoryAgent] Added item_id={item_id} with content='{content}'")

    def old_update_memory(self, item_id: str, new_content: str, new_metadata: dict = None):
        """
        Updates memory by first removing the old item, then adding the new content.
        Alternatively, you could implement a specialized 'update' if your setup allows partial modifications.
        """
        # Remove old data
        self.collection.delete(ids=[item_id])

        # Insert new data
        self.collection.add(
            documents=[new_content],
            metadatas=[new_metadata if new_metadata else {}],
            ids=[item_id]
        )

        if B_DEBUG_MODE:
            print(f"[MemoryAgent] Updated item_id={item_id} with new content='{new_content}'")

    def old_remove_memory(self, item_id: str):
        """
        Removes an existing piece of memory from the collection by item_id.
        """
        self.collection.delete(ids=[item_id])

        if B_DEBUG_MODE:
            print(f"[MemoryAgent] Removed item_id={item_id}")

    def old_retrieve_memory(self, collection: str, query: str, n_results: int = 5):
        """
        Retrieves the most relevant documents from the collection
        based on the provided query text, returning up to n_results items.
        """
        query_embedding = self.embed_fn.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # results is a dictionary with 'documents', 'metadatas', 'ids', etc.
        # For convenience, you can zip them up or just return the full dictionary.
        
        # Example: Combine each match into a tuple or dict
        combined_results = []
        for doc, meta, mem_id, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["ids"][0],
            results["distances"][0]
        ):
            combined_results.append({
                "id": mem_id,
                "document": doc,
                "metadata": meta,
                "distance": distance
            })
        
        return combined_results
    
    def utility_generateDatetimeStr(self):
        """
            Utility function to generate a timestamp to create a unique id for each entry.             
        """
        # Get current date and time
        now = datetime.datetime.now()
        
        # Extract components
        yy = now.year % 100  # Last two digits of year
        mm = now.month
        dd = now.day
        hh = now.hour
        min = now.minute
        ss = now.second
        
        # Format as yymmddhhmmss
        formatted = f"{yy:02d}{mm:02d}{dd:02d}{hh:02d}{min:02d}{ss:02d}"
        
        # Convert to integer
        return int(formatted)
    
    def saveToJson(self, json_data, file_name):
        filename = file_name + ".json"
        file = open(filename, 'w')
        json.dump(json_data, file, indent=4)
        file.close()

class StoryAgent(MemoryAgent):
    COLLECTION_NAMES = {}

    def __init__(self, 
                 entities_collection_name="story_entities",
                 passages_collection_name="story_passages",
                 embedding_model=MODEL_TRANSFORMER,
                ):
        
        super().__init__(embedding_model=embedding_model)

        self.COLLECTION_NAMES = {
            "entities": entities_collection_name,
            "passages": passages_collection_name
        }

        # build every collection once and expose as attributes
        for attr, col_name in self.COLLECTION_NAMES.items():
            setattr(self, attr, self.get_collection(col_name))

    def add_story_passage(self, story_passage: str, metadata: dict = {}):        
        timeStamp = self.utility_generateDatetimeStr()
        storyPassageId = str(timeStamp)

        self.passages.add(
            ids=[storyPassageId],
            documents=[story_passage],
            metadatas=[metadata]
        )

        if B_DEBUG_MODE:
            base_str_output = "New Story Passage added with the following metadata:\n"

            for key, value in metadata.items():
                base_str_output += f"{key} : {value}\n"
            
            print(base_str_output)

        return storyPassageId
        
    def extract_story_segment(self, story_passage):
        model = "llama3-70b-8192"
        client = openai.OpenAI(
            api_key="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",
            base_url="https://api.groq.com/openai/v1"
        )

        constraints = [
            "Use only explicit information from the text",
            # "Maintain consistent snake_case IDs for cross-referencing",
            "Include atmospheric cues as mood tags",
            "Limit event descriptions to 15 words",
            "Never invent details not present in the text"
            "The 'actions' field cannot be blank."
            "The player cannot be a 'chars' entry."
        ]

        #Sample input prompt to facilitate few-shot learning.
        test_input = """
            "Eldora \"Ironhide\" Thorns stood tall beside her caravan, her eyes scanning the bustling border checkpoint with a 
            mix of scrutiny and calculation. The worn iron pendant around her neck seemed to gleam in the flickering torchlight,
            a subtle reminder of her former life as a knight of the border patrol. Her reputation for unyielding protection 
            had earned her the nickname \"Ironhide,\" and she wore it like a badge of honor. As she engaged in hushed 
            conversation with a gruff border guard, Eldora's stern demeanor was a stark contrast to the warmth of the evening. 
            The air was thick with the smells of exotic spices and fresh bread, and the sounds of merchants haggling and the 
            occasional clang of metal on metal filled the air. Yet, Eldora's focus remained fixed on the task at hand: getting 
            her precious cargo through the checkpoint without raising any unwanted attention.\n\n\"Tell me, Gorvoth,\" she 
            pressed the guard, her voice low and steady, \"what's the word on the decree? Any changes since I last passed 
            through?\"\n\nGorvoth, a grizzled veteran with a thick beard and a perpetual scowl, rubbed his chin thoughtfully. 
            \"Ah, Eldora, you know as well as I do that the Alchemist's Council has been breathing down our necks. The decree 
            remains unchanged: no magic ores are allowed to leave the kingdom. But,\" he leaned in closer, his voice taking 
            on a conspiratorial tone, \"I heard rumors of...ah...creative interpretations. For the right price, of course.
            \"\n\nEldora's eyes narrowed. She had heard similar whispers, but she was skeptical. The last thing she needed
            was to trust some shadowy figure who might sell her out. \"What's the going rate for these...interpretations?\" 
            she asked, her hand resting on the hilt of her sword.\n\nGorvoth chuckled, a low, gravelly sound. \"Ah, Eldora, 
            you know as well as I do that prices are negotiable. But be warned: those who try to smuggle magic ores out 
            of the kingdom won't be dealt with kindly. The alchemist's eyes are everywhere.\"\n\nEldora's gaze flickered 
            back to her caravan, where the precious cargo lay hidden beneath layers of canvas and woven blankets. She had 
            already taken extensive precautions to conceal the ores, but she knew that the alchemist's agents were cunning 
            and relentless.\n\nAs she pondered her next move, Eldora's eyes met those of a hooded figure lurking at the edge 
            of the checkpoint. For a fleeting moment, their gazes locked, and Eldora felt a shiver run down her spine. Were 
            they friend or foe? She made a mental note to keep a watchful eye on this mysterious individual, for in a world 
            where loyalty was the rarest commodity, appearances could be deceiving."
        """

        prompt_template = {
        "task": "Analyze the provided story segment (under input_story) and extract structured data in JSON format.",
        "requirements": {
            "output_sections": ["chars", "key_events", "setting_atmosphere"],
                "format": {
                "chars": {
                    "fields": [
                        "id: (name of character without any symbols)",
                        "type: (major character, minor character)",
                        "attributes: (disposition towards player, current mood, cannot be blank)",
                        "dialog: [(spoken lines)]",
                        "actions: (1-sentence describing what the character is doing)"
                    ]
                },
                "key_events": {
                    "fields": [
                    "id: (lowercase_snake_case)",
                    "type: 'event'", 
                    "description: (1-sentence summary)",
                    "tags: (plot-relevant keywords as a single string separated by commas)"
                    ]
                },
                "setting_atmosphere": {
                    "fields": [
                        "id (lowercase_snake_case)",
                        "type: 'setting'",
                        "description: (physical environment)",
                        "mood: (emotional tone as a single string separated by commas)"
                    ]
                }
            }
        },
        "examples": {
            "input_sample": test_input,
            "output_sample": {                
                "chars": [
                    {
                        "id": "Eldora Ironhide Thorns",
                        "type": "major character",
                        "attributes": {
                            "disposition": "",
                            "current_mood": "calculating, stern"
                        },
                        "dialog": [
                            "Tell me, Gorvoth,",
                            "what's the word on the decree? Any changes since I last passed through?",
                            "What's the going rate for these...interpretations?"
                        ],
                        "actions": "Engaging in hushed conversation with Gorvoth, scanning the checkpoint"
                    },
                    {
                        "id": "Gorvoth",
                        "type": "minor character",
                        "attributes": {
                            "disposition": "",
                            "current_mood": "thoughtful, conspiratorial"
                        },
                        "dialog": [
                            "Ah, Eldora, you know as well as I do that the Alchemist's Council has been breathing down our necks.",
                            "Ah, Eldora, you know as well as I do that prices are negotiable."
                        ],
                        "actions": "Rubbing his chin thoughtfully, leaning in closer"
                    },
                    {
                        "id": "Hooded Figure",
                        "type": "minor character",
                        "attributes": {
                            "disposition": "",
                            "current_mood": "mysterious"
                        },
                        "dialog": [],
                        "actions": "Lurking at the edge of the checkpoint, watching Eldora"
                    }
                ],
                "key_events": [
                    {
                        "id": "eldora_meets_gorvoth",
                        "type": "event",
                        "description": "Eldora engages in conversation with Gorvoth at the border checkpoint.",
                        "tags": "border_checkpoint, smuggling, magic_ores"
                    },
                    {
                        "id": "gorvoth_mentions_rumors",
                        "type": "event",
                        "description": "Gorvoth shares rumors of 'creative interpretations' of the decree.",
                        "tags": "rumors, smuggling, magic_ores"
                    },
                    {
                        "id": "eldora_notices_hooded_figure",
                        "type": "event",
                        "description": "Eldora notices a mysterious hooded figure watching her.",
                        "tags": "mysterious_figure, suspicion"
                    }
                ],
                "setting_atmosphere": [
                    {
                        "id": "border_checkpoint",
                        "type": "setting",
                        "description": "A bustling border checkpoint with torchlight and exotic smells.",
                        "mood": "tense, suspicious, warm"
                    }
                ]
            }
        },
        "constraints": constraints,
        "input_story": story_passage
        }

        json_prompt_string = json.dumps(prompt_template)
        segments = None

        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI that formats data as requested."
            },
            {
                "role": "user",
                "content": f"JSON Prompt:\n{json_prompt_string}"
            }
        ]

        try: 
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                response_format={"type": "json_object"}             
            ) 

            segments = json.loads(response.choices[0].message.content)

            if B_DEBUG_MODE:
                self.saveToJson(segments, "db_segments")

            return segments

        except Exception as e:
            print(f"Prompt operation failed:\n{e}")

            #TODO: Consider running the try block a second time.
            return None
        
    def add_story_metadata(self, json_data, storyPassageId):
        key_events = json_data["key_events"]
        setting_atmosphere = json_data["setting_atmosphere"]

        for entry in key_events:
            embed_str = (
                f"Story Passage ID: {storyPassageId}\n"
                f"Event ID: {entry['id']}\n"
                f"Description: {entry['description']}\n"
                f"Tags: {entry['tags']}\n"
            )

            embedding = self.embedding_model.encode(embed_str).tolist()
            self.entities.add(
                documents=embed_str,
                ids=entry["id"], 
                embeddings=embedding,
                metadatas={
                    "storyPassageId": storyPassageId,
                    "type": entry["type"], 
                    "description": entry["description"],
                    "tags": entry["tags"]
                } #Add additional metadata if need be.                
            )

            if B_DEBUG_MODE:
                print(f"Added entity: {entry['id']} : {entry['description']} based on storyPassageId: {storyPassageId}")

        setting_embed_str = (
            f"Story Passage ID: {storyPassageId}\n"
            f"Setting ID: {setting_atmosphere[0]['id']}\n"
            f"Description: {setting_atmosphere[0]['description']}\n"
            f"Mood: {setting_atmosphere[0]['mood']}\n"
        )

        self.entities.add(
            documents=setting_embed_str,
            ids=setting_atmosphere[0]["id"],
            embeddings=self.embedding_model.encode(setting_embed_str).tolist(),
            metadatas={
                "storyPassageId": storyPassageId,
                "type": setting_atmosphere[0]["type"], 
                "description": setting_atmosphere[0]["description"],
                "mood": setting_atmosphere[0]["mood"]
            } #Add additional metadata if need be.            
        )

        if B_DEBUG_MODE:
                print(f"Added setting: {setting_atmosphere[0]['id']} : {setting_atmosphere[0]['description']} based on storyPassageId: {storyPassageId}")


    def get_recent_passages(self, timeStamp, k: int = 1):
        """Gets the k most recent passages, using the time stamp as the search function."""
        results = self.passages.query(
            n_results=k,
            query_texts=[str(timeStamp)],
        )

        dt_output = {
            "ids": results["ids"],
            "documents": results["documents"],
            "metadatas": results["metadatas"]
        }

        return dt_output
    
    def get_keyEvents(self, storyPassageId):
        results = self.entities.get(
            where={"storyPassageId": storyPassageId}
        )

        return results

class NPCAgent(MemoryAgent):
    COLLECTION_NAMES = {}

    def __init__(self, 
                npc_collection_name="npc_collection", 
                npc_interactions_name="npc_interactions",
                embedding_model=MODEL_TRANSFORMER,
                additional_collections={}
                ):
        super().__init__(embedding_model=embedding_model)

        self.COLLECTION_NAMES = {
            "npcs": npc_collection_name,
            "npc_interactions": npc_interactions_name
        }

        #Additional capability for adding more collections if need be.
        for key, value in additional_collections:
            self.COLLECTION_NAMES[key] = value

        # build every collection once and expose as attributes
        for attr, col_name in self.COLLECTION_NAMES.items():
            setattr(self, attr, self.get_collection(col_name))

    def add_npcs(self, npc_entries):
        for key, value in npc_entries['chars'].items():
            #Note: If updating the metadata tags, ensure that the embedding_text is also updated.
            embedding_text = (
                f"name: {value['name']}\n" 
                f"background: {value['background']}\n" 
                f"traits: {value['act']}\n"
                f"knowledge: {value['info']}\n"
                f"init_loc_activity: {value['init']}\n"
                f"q_react_hello: {value['q_hello']}\n"
                f"q_react_important: {value['q_important']}\n"
                f"q_react_help: {value['q_help']}\n"
                f"q_notes: {value['notes']}\n"
            )
            embedding = self.embedding_model.encode(embedding_text)

            self.npcs.add(
                ids=value['name'],
                documents=embedding_text,
                embeddings=embedding,
                metadatas=[{
                    "name": value['name'],
                    "background": value['background'],
                    "act": value['act'],
                    "info": value['info'],
                    "init": value['init'],
                    "q_hello": value['q_hello'],
                    "q_important": value['q_important'],
                    "q_help": value['q_help'],
                    "q_notes": value['notes']
                }]
            )

    def add_npc_interaction(self, npc_convo_entries, storyPassageId):
        """Add NPC conversations extracted from the story passage denoted by the storyPassageId"""
        for entry in npc_convo_entries['chars']:
            self.npc_interactions.add(
                ids=[entry['id']],
                documents=entry['dialog'],
                metadatas=[{
                    "storyPassageId" : storyPassageId
                    #Add additional tags as needed.
                }]
            )

    def get_NPCs(self, **kwargs):
        result = self.npcs.get(**kwargs)

        return result
    
#Debugging functions
def debug_addStoryPassageAndMetaData(story_agent, segment_components):
    passage_id = story_agent.add_story_passage(
                story_text, 
                {
                    "setting_id": segment_components["setting_atmosphere"][0]["id"],
                    "setting_description": segment_components["setting_atmosphere"][0]["description"],
                    "setting_mood": segment_components["setting_atmosphere"][0]["mood"], 
                    "key_events": ", ".join([event["id"] for event in segment_components["key_events"]])
                })
    story_agent.add_story_metadata(segment_components, passage_id)
        
    return passage_id

#Note: segment_components represents the summarized story passage object, while npc_entries 
#represents the data from the combined DATA json object.
def debug_addNPCsAndInteractions(npc_agent, npc_entries, segment_components, storyPassageId):
    npc_agent.add_npcs(npc_entries)
    npc_agent.add_npc_interaction(segment_components, storyPassageId)

#NOTE: The operations defined in the main function below are intended for debugging purposes outside of the Main app.
if __name__ == "__main__":
    transfomer_model = "all-MiniLM-L6-v2" #Comes default with SentenceTransformer. However, other models can be used.
    db_path = "./chroma_db"

   # Initialize ChromaDB Client (Persistent Storage)
    client = chromadb.PersistentClient(path=db_path)  # Stores data on disk. There is a HttpsClient available to allow for client/server operations.
#    embedding_model = SentenceTransformer(transfomer_model)  # Loaded from Hugging Face.
#    embedding_model.save('./models')

    if not B_PERSIST_ENTRIES:
        collections = client.list_collections()

        for collection in collections:
            client.delete_collection(collection)

    story_collection = StoryAgent(
        entities_collection_name="story_collection_entities",
        passages_collection_name="story_collection_passages",
        embedding_model=transfomer_model
    )

    npc_collection = NPCAgent(
        npc_collection_name="story_npc_collection",
        npc_interactions_name="npc_collections",
        embedding_model=transfomer_model
    )

    segment_components = story_collection.extract_story_segment(story_text)

    storyPassageId = debug_addStoryPassageAndMetaData(story_collection, segment_components)
    debug_addNPCsAndInteractions(npc_collection, npc_entries, segment_components, storyPassageId)

    timeStamp = story_collection.utility_generateDatetimeStr()
    dt_test_output = story_collection.get_recent_passages(timeStamp)

    dt_key_events = story_collection.get_keyEvents(dt_test_output["ids"][0][0])
    dt_npcs = npc_collection.get_NPCs(ids="Lyra Kaine")