import chromadb
import datetime
import re       #For converting the character names. Not really necessary.
import textwrap #For breaking up the story text into chunks.

import nltk 
import json
import openai

from nltk.tokenize import sent_tokenize

from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from sklearn.cluster import KMeans

B_DEBUG_MODE = True
B_PERSIST_ENTRIES = False

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
    def __init__(self, collection_name="my_collection", 
                 embedding_model=embedding_functions.DefaultEmbeddingFunction()):
        # Initialize the Chroma client and collection
        self.client = chromadb.Client()
        self.embed_fn = embedding_model
        
        # Create or get the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name            
        )

    def add_memory(self, item_id: str, embeddings: list,  content: str = None, metadata: dict = None):
        """
        Adds a new piece of memory (text + metadata) to the collection.
        Each memory item has a unique item_id used for future retrieval or updates.
        """
        self.collection.add(
            ids=[item_id],
            documents=[content],
            embeddings=embeddings,
            metadatas=[metadata if metadata else {}],            
        )

        if B_DEBUG_MODE:
            print(f"[MemoryAgent] Added item_id={item_id} with content='{content}'")

    def update_memory(self, item_id: str, new_content: str, new_metadata: dict = None):
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

    def remove_memory(self, item_id: str):
        """
        Removes an existing piece of memory from the collection by item_id.
        """
        self.collection.delete(ids=[item_id])

        if B_DEBUG_MODE:
            print(f"[MemoryAgent] Removed item_id={item_id}")

    def retrieve_memory(self, query: str, n_results: int = 5):
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
    def __init__(self, 
                 collection_name="story_collection", 
                 embedding_model=embedding_functions.DefaultEmbeddingFunction(), 
                 chunk_size=300,
                 summarization_model="facebook/bart-large-cnn"):
        super().__init__(collection_name=collection_name, embedding_model=embedding_model)

        self.chunk_size = chunk_size        
        self.summarizer = pipeline("summarization", model=summarization_model)
        self.summarizer_min_length = 100
        self.summarizer_max_length = 1000

    def add_story_passage(self, story_passage):        
        timeStamp = self.utility_generateDatetimeStr()
        storyPassageId = timeStamp        
        story_chunks = textwrap.wrap(story_passage, self.chunk_size)

        # Add each chunk separately to enable partial retrieval
        for i, chunk in enumerate(story_chunks):
            chunk_id = f"{storyPassageId}_chunk{i}"
            embedding = embedding_model.encode(chunk).tolist()
            
            self.add_memory(
                item_id=chunk_id, 
                content=chunk,
                embeddings=embedding,
                metadata={
                    "story_id": storyPassageId, 
                    "chunk_index" : i
                } #Add additional metadata if need be.
            )

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
    
    def dev_cluster_example(self, story_passage):
        """
            Proof of concept function. Attempts to cluster a story passage into relevant bits.
        """ 
        sentences = sent_tokenize(story_passage)
        sentences = [s.strip() for s in sentences if s.strip()]  # remove empty or whitespace-only
        
        sentence_embeddings = self.embed_fn.encode(sentences)

        num_clusters = 4
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        kmeans.fit(sentence_embeddings)
        cluster_labels = kmeans.labels_ 

        clustered_sentences = {}
        for label, sentence in zip(cluster_labels, sentences):
            if label not in clustered_sentences:
                clustered_sentences[label] = []

            clustered_sentences[label].append(sentence)

        print("CHUNKED BY TOPIC COHERENCE:\n")

        for cluster_id, cluster_sents in clustered_sentences.items():
            chunk_text = " ".join(cluster_sents)
            print(f"--- Cluster {cluster_id} ---\n{chunk_text}\n")

    def old_extract_story_segment(self, story_passage):
        """
        Uses an LLM (via the OpenAI API) to parse a story passage into major scene beats.
        
        :return: A list of scene beat descriptions from the LLM.
        # """
        model = "llama3-70b-8192"
        client = openai.OpenAI(
            api_key="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",
            base_url="https://api.groq.com/openai/v1"            
        )

        # Construct a system or user prompt instructing the model to identify major scene beats
        prompt = f"""
            You are an expert literary analyst. Given the following story segment,
            extract structured JSON data. Follow these rules:

            **Sections to Extract**:
            1. **Characters**: Include their appearance, traits, role, personality, and relationships.
            2. **Key Events**: Short summaries with plot-relevant tags.
            3. **Setting & Atmosphere**: Physical environment and mood.
            4. **Setting Facts**: What is true in the world.
            5. **Setting Constraints**: What actions are allowed or forbidden.

            **Format**:
            - Use `snake_case` for IDs (e.g., "captain_elias_vorne").
            - Maintain consistent snake_case IDs for cross-referencing           
            - Include atmospheric cues as mood tags
            - Never invent new information.
            - Limit event descriptions to 15 words

            **Example Output**:
            {{
                "characters": [
                    {{
                        "id": "example_character",
                        "type": "character",
                        "attributes": {{
                            "appearance": "laser-scarred face",
                            "personality": "serious, stoic",
                            "role": "guild representative",
                            "relationships": ["other_character_id"]
                        }}
                    }}
                ],
                "key_events": [
                    {{
                        "id": "event_id",
                        "type": "event",
                        "description": "Brief summary",
                        "tags": ["tension", "danger"]
                    }}
                ],
                "setting_atmosphere": {{
                    "id": "location_id",
                    "type": "setting",
                    "description": "Dingy spaceport tavern",
                    "mood": "tense, gritty"
                }}
                "setting_facts": [
                    {{
                        "id" : "fact_id",
                        "fact" : "Door is locked"
                    }}
                ],
                "setting_constraints": [
                    {{
                        "id" : "constraint_id",
                        "constaint" : "Cannot enter cave without torch"
                    }}
                ],                
            }}

            **Story Segment**:
            {story_passage}
        """
        segments = None

        try: 
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Expert story analyst"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}             
            ) 

            segments = json.loads(response.choices[0].message.content)

        except Exception as e:
            print("Prompt operation failed")

        return segments
    
    def dev_extract_story_segment(self, story_passage):
        model = "llama3-70b-8192"
        client = openai.OpenAI(
            api_key="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",
            base_url="https://api.groq.com/openai/v1"            
        )

        constraints = [
            "Use only explicit information from the text",
            "Maintain consistent snake_case IDs for cross-referencing",
            "Include atmospheric cues as mood tags",
            "Limit event descriptions to 15 words",
            "Never invent details not present in the text"
        ]

        prompt_template = {
        "task": "Analyze the provided story segment and extract structured data in JSON format.",
        "requirements": {
            "output_sections": ["characters", "key_events", "setting_atmosphere"],
                "format": {
                "characters": {
                    "fields": [
                    "id (lowercase_snake_case)",
                    "type: 'character'",
                    "attributes: {appearance, personality/traits, role, relationships, backstory (if mentioned)}"
                    ]
                },
                "key_events": {
                    "fields": [
                    "id (lowercase_snake_case)",
                    "type: 'event'", 
                    "description (1-sentence summary)",
                    "tags (plot-relevant keywords)"
                    ]
                },
                "setting_atmosphere": {
                    "fields": [
                    "id (lowercase_snake_case)",
                    "type: 'setting'",
                    "description (physical environment)",
                    "mood (emotional tone)"
                    ]
                }
            }
        },
        "examples": {
            "input_sample": "\"Captain Elias Vorne growled... risk is high.\"",
            "output_sample": {
            "characters": [{
                "id": "captain_elias_vorne",
                "type": "character",
                "attributes": {
                "appearance": "laser-scarred face, whiskey-roughened voice",
                "personality": "battle-hardened, calculating",
                "role": "offers risky transport job",
                "relationships": ["zera7"]
                }
            }]
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
                # We embed our JSON as a 'user' message,
                # or we could add it as a system message—depends on your use case.
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
            return None
        
    def add_story_metadata(self, json_data):
        # timeStamp = self.utility_generateDatetimeStr()
        # storyPassageId = timeStamp

        key_events = json_data["key_events"]
        setting_atmosphere = json_data["setting_atmosphere"]

        for entry in key_events:
            embed_str = entry["description"]
            embedding = embedding_model.encode(embed_str).tolist()

            self.add_memory(
                item_id=entry["id"], 
                embeddings=embedding,
                metadata={
                    "type": entry["type"], 
                    "description": entry["description"],
                    "tags": entry["tags"]
                } #Add additional metadata if need be.
            )

        self.add_memory(
            item_id=setting_atmosphere["id"],
            embedding = embedding_model.encode(setting_atmosphere["description"]).tolist(),
            metadata={
                "type": setting_atmosphere["type"], 
                "description": setting_atmosphere["description"],
                "mood": setting_atmosphere["tags"]
            } #Add additional metadata if need be.            
        )

class NPCAgent(MemoryAgent):
    def __init__(self, 
                collection_name="my_collection", 
                 embedding_model=embedding_functions.DefaultEmbeddingFunction()):
        super().__init__(collection_name=collection_name, embedding_model=embedding_model)

    
    def add_npc(self, npc_entries):
        for entity in npc_entries:
            embedding_text = f"{entity['role']}. {entity['characteristics']}. {entity['backstory']}"
            embedding = embedding_model.encode(embedding_text)

            #Remove any symbols from the name and format it to be used as the id for the npc.
            idTxt = re.sub(r"[^a-zA-Z0-9\s]", '', entity['name']).replace(' ', '').lower()

            self.add_memory(
                item_id=idTxt,
                content=embedding_text,
                embeddings=embedding,
                metadatas=[{
                    "name": entity['name'], 
                    "role": entity['role']
                }]
            )

if __name__ == "__main__":
   transfomer_model = "all-MiniLM-L6-v2" #Comes default with SentenceTransformer. However, other models can be used.
   db_path = "./chroma_db"

   # Initialize ChromaDB Client (Persistent Storage)
   client = chromadb.PersistentClient(path=db_path)  # Stores data on disk. There is a HttpsClient available to allow for client/server operations.
   embedding_model = SentenceTransformer(transfomer_model)  # Loaded from Hugging Face.

   if not B_PERSIST_ENTRIES:
    collections = client.list_collections()
    for collection in collections:
        client.delete_collection(collection)

   story_collection = StoryAgent(collection_name="story_collection", embedding_model=embedding_model)
   segment_components = story_collection.dev_extract_story_segment(story_text)
   story_collection.add_story_metadata(segment_components)

#    story_collection.add_story_passage(story_text)

#    story_collection.summarize_passage(story_text)
#    story_collection.dev_cluster_example(story_text)
   

   npc_collection = MemoryAgent(collection_name="npc_collection", embedding_model=embedding_model)

   query_text = "A high-risk job involving a rogue android"
   memory = story_collection.retrieve_memory(query_text, 2)

   print("Hello World")