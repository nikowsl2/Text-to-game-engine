import chromadb
import datetime
import re       #For converting the character names. Not really necessary.
import textwrap #For breaking up the story text into chunks.

from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

B_DEBUG_MODE = True

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

#Story_Collection Example
# def add_story_passage():
#     story_collection = client.get_or_create_collection(name="story_collection")

#     storyPassageId = 1
#     storyIdFormatted = "{:04d}".format(storyPassageId)

#     #Break down the story passages if they are too long
#     chunk_size = 300
#     story_chunks = textwrap.wrap(story_text, chunk_size)

#     # Add each chunk separately to enable partial retrieval
#     for i, chunk in enumerate(story_chunks):
#         chunk_id = f"{storyIdFormatted}_chunk{i}"
#         embedding = embedding_model.encode(chunk).tolist()

#         story_collection.add(
#             ids=[chunk_id],
#             embeddings=[embedding],
#             metadatas=[{
#                 "story_id": storyIdFormatted,
#                 "chunk_index": i,
#                 # "characters": characters,
#                 # "location": location,
#                 # "tags": tags
#             }],
#             documents=[chunk]  # Store text for reference
#         )

#     query_text = "A high-risk job involving a rogue android"
#     query_embedding = embedding_model.encode(query_text).tolist()

#     #Query is similar to running a SQL select operation. See https://docs.trychroma.com/docs/querying-collections/full-text-search
#     results = story_collection.query(
#         query_embeddings=[query_embedding],
#         n_results=2  # Retrieve the top 2 most similar story sections
#     )

#     print("Search Results:", results)    

#Implementation of add_story_passage as it might be implemented in the story generator agent.
def add_story_passage(story_passage, story_collection):
    # story_collection = client.get_or_create_collection(name="story_collection")
    timeStamp = utility_generateDatetimeStr()
    storyPassageId = timeStamp
    chunk_size = 300
    story_chunks = textwrap.wrap(story_passage, chunk_size)

    # Add each chunk separately to enable partial retrieval
    for i, chunk in enumerate(story_chunks):
        chunk_id = f"{storyPassageId}_chunk{i}"
        embedding = embedding_model.encode(chunk).tolist()

        story_collection.add_memory(
            chunk_id, 
            chunk,
            embedding,
            {"story_id": storyPassageId, "chunk_index" : i}
        )

# NPC_Collection Example
def add_npc():
    # Create or get a collection
    npc_collection = client.get_or_create_collection(name="npc_collection")

    for entity in npc_entries:
        embedding_text = f"{entity['role']}. {entity['characteristics']}. {entity['backstory']}"
        embedding = embedding_model.encode(embedding_text)

        #Remove any symbols from the name and format it to be used as the id for the npc.
        idTxt = re.sub(r"[^a-zA-Z0-9\s]", '', entity['name']).replace(' ', '').lower()

        npc_collection.add(
            ids=idTxt,
            embeddings=embedding,
            metadatas=[{"name": entity['name'], "role": entity['role']}], #The metadata tags can be modified into other things as needed. This is only to show a proof of concept.
            documents=embedding_text
        )

def utility_generateDatetimeStr():
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

    def add_memory(self, item_id: str, content: str, embeddings: list, metadata: dict = None):
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

if __name__ == "__main__":
   transfomer_model = "all-MiniLM-L6-v2" #Comes default with SentenceTransformer. However, other models can be used.
   db_path = "./chroma_db"

   # Initialize ChromaDB Client (Persistent Storage)
   client = chromadb.PersistentClient(path=db_path)  # Stores data on disk. There is a HttpsClient available to allow for client/server operations.
   embedding_model = SentenceTransformer(transfomer_model)  # Loaded from Hugging Face.
   
   story_collection = MemoryAgent(collection_name="story_collection", embedding_model=embedding_model)
   npc_collection = MemoryAgent(collection_name="npc_collection", embedding_model=embedding_model)

   add_story_passage(story_text, story_collection)

   query_text = "A high-risk job involving a rogue android"
   memory = story_collection.retrieve_memory(query_text, 2)

   print("Hello World")