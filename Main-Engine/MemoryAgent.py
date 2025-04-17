import chromadb
import datetime
import re       #For converting the character names. Not really necessary.
# import textwrap #For breaking up the story text into chunks.

# import nltk 
import json
import openai

# from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
# from transformers import pipeline

B_DEBUG_MODE = True
B_PERSIST_ENTRIES = False
MODEL_TRANSFORMER = "all-MiniLM-L6-v2"

#Test Input Text
npc_entries = [
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

#Note that story_text was accomplished via the generator.
story_text = 'As I entered the dingy spaceport tavern, the smoke-filled air clung to my skin like a bad omen. ' \
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
        # embedding = self.embedding_model.encode(story_passage).tolist()

        # story_chunks = textwrap.wrap(story_passage, self.chunk_size)

        # Add each chunk separately to enable partial retrieval
        # for i, chunk in enumerate(story_chunks):
        #     chunk_id = f"{storyPassageId}_chunk{i}"
        #     embedding = self.embedding_model.encode(chunk).tolist()
            
        #     self.add_memory(
        #         item_id=chunk_id, 
        #         content=chunk,
        #         embeddings=embedding,
        #         metadata={
        #             "story_id": storyPassageId, 
        #             "chunk_index" : i
        #         } #Add additional metadata if need be.
        #     )

        self.passages.add(
            ids=[storyPassageId],
            documents=[story_passage],
            metadatas=[metadata]
        )

        return storyPassageId

    def summarize_passage(self, story_passage):
        """
            Proof of concept function. Attempts to summarize a story passage.
        """
        # Generate a summary    
        summary_output = self.summarizer(
            story_passage,
            max_length=self.summarizer_max_length,
            min_length=self.summarizer_min_length,
            do_sample=False
        )

        # Extract the summarized text from the pipeline output
        summary = summary_output[0]["summary_text"]
        return summary
    
    def dev_extract_story_segment(self, story_passage):
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
        ]

        test_input = """
            As the twin suns of the remote outpost set over the dusty horizon, casting a reddish-orange glow over the makeshift 
            research facility, Elysia 'Starlight' Vaal's eyes remained fixed on the holographic display projected before her. 
            Her advanced navigation software, affectionately dubbed "Nebula", hummed softly as it crunched massive amounts of 
            data on the mysterious anomalies that had been plaguing the galaxy.

            Elysia's fingers danced across the console, her mind whirling with theories and hypotheses. A former star 
            cartographer, she had lost her ship and crew to one of these very anomalies, leaving her with a burning desire to 
            understand their mechanisms and prevent further disasters. The silence of the outpost was a balm to her soul, 
            allowing her to focus on her work without distraction.

            The sudden shrill beep of her comms system shattered the peaceful atmosphere. Elysia's instincts kicked in, her 
            heart rate steady as she reached for the console. A data-packet flickered into existence on the screen, the 
            transmitted signal weak and garbled.

            "Unidentified vessel...dis...es...tress...," the fractured message read.

            Elysia's eyes narrowed. A distress signal was rare in these isolated regions, and the anomaly-ridden galaxies 
            made any transmission a gamble. Yet, something about this one resonated with her. Perhaps it was the desperation 
            that clung to the words like a lifeline, or the faint hint of fear that underscored the fragile signal.

            Her mind racing with possibilities, Elysia called up the nearest constellation charts and began to triangulate 
            the location of the distressed vessel. The outpost's distant sensors were already picking up anomalies, echoes 
            of the cosmic phenomena that had ravaged the galaxy. Her advanced navigation software would take some time to 
            compensate for the interference, but Elysia was convinced that this was no ordinary distress call.

            With a deep breath, she sent a confirmation signal, promising aid to the struggling vessel. The crimson horizon 
            outside seemed to darken in response, as if the very fabric of the universe was drawing her closer to the heart 
            of the mystery.

            Elysia smiled wistfully, knowing that her curiosity had gotten the better of her once more. It was time to leave 
            the comforts of the outpost behind and venture into the great unknown, where the fates of civilizations and the 
            cosmos hung in delicate balance.

            Little did she know, the next jump would propel her into the midst of a desperate struggle, and the choices she 
            made would decide the course of human destiny...
        """

        prompt_template = {
        "task": "Analyze the provided story segment (under input_story) and extract structured data in JSON format.",
        "requirements": {
            "output_sections": ["characters", "key_events", "setting_atmosphere"],
                "format": {
                "characters": {
                    "fields": [
                    "id (lowercase_snake_case)",
                    "type: (major character, minor character)",
                    "attributes: (disposition, current mood)"
                    ]
                },
                "key_events": {
                    "fields": [
                    "id (lowercase_snake_case)",
                    "type: 'event'", 
                    "description (1-sentence summary)",
                    "tags (plot-relevant keywords as a single string separated by commas)"
                    ]
                },
                "setting_atmosphere": {
                    "fields": [
                        "id (lowercase_snake_case)",
                        "type: 'setting'",
                        "description (physical environment)",
                        "mood (emotional tone as a single string separated by commas)"
                    ]
                }
            }
        },
        "examples": {
            "input_sample": test_input,
            "output_sample": {                
                "characters": [
                    {
                        "id": "elysia_starlight_vaal",
                        "type": "character",
                        "attributes": {
                            "disposition": "determined, curious",
                            "current_mood": "focused, intrigued"
                        }
                    }                    
                ],
                "key_events": [
                    {
                        "id": "elysia_receives_distress_signal",
                        "type": "event",
                        "description": "Elysia intercepts a rare and fragmented distress signal from an unidentified vessel.",
                        "tags": "distress_signal, mystery, anomalies"
                    },
                    {
                        "id": "elysia_confirms_aid",
                        "type": "event",
                        "description": "Elysia decides to respond to the distress signal, preparing for immediate departure.",
                        "tags": "decision, departure, danger"
                    }
                ],
                "setting_atmosphere": [
                    {
                        "id": "remote_outpost",
                        "type": "setting",
                        "description": "An isolated, makeshift research facility bathed in reddish-orange twilight from twin suns.",
                        "mood": "isolated, tense, foreboding"
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
            return segments

        except Exception as e:
            print("Prompt operation failed")

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

        for name, value in npc_entries.items():
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

    def add_npc_interaction(self):
        pass

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

    segment_components = story_collection.dev_extract_story_segment(story_text)
    passage_id = story_collection.add_story_passage(story_text, 
                                        {
                                            "setting_id": segment_components["setting_atmosphere"][0]["id"],
                                            "setting_description": segment_components["setting_atmosphere"][0]["description"],
                                            "setting_mood": segment_components["setting_atmosphere"][0]["mood"], 
                                            "key_events": ", ".join([event["id"] for event in segment_components["key_events"]])
                                        })
    story_collection.add_story_metadata(segment_components, passage_id)
#    story_collection.add_story_metadata(segment_components)

#    story_collection.add_story_passage(story_text)

#    story_collection.summarize_passage(story_text)
#    story_collection.dev_cluster_example(story_text)
   

#    npc_collection = MemoryAgent(collection_name="npc_collection", embedding_model=embedding_model)

#    query_text = "A high-risk job involving a rogue android"
#    memory = story_collection.retrieve_memory(query_text, 2)

#    print("Hello World")