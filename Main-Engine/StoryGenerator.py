from openai import OpenAI
# import mistralai
import json


def format_characters(data):
    """Format character data for prompt"""
    return "\n".join(
        f"""Character name: {data["chars"][i]['name']}
        Character background: {data["chars"][i]['background']}
        Character Behaviour: {data["chars"][i]['act']}
        The only information the character knows is: {data["chars"][i]['info']}. The character does not know anything beyond the mentioned scope.
        The character begins the story in the following state: {data["chars"][i]['init']} \n
        """
        for i in data["chars"]
    )


def get_last_story_segment(data):
    """Retrieve the most recent story segment from history"""
    return "\n".join(
        f"""{i[0]}: {i[1]}"""
        for i in data["history"]
    )



def update_chars(new_characters, data):
    """Add new characters to the chars dictionary in the data structure"""
    if not new_characters:
        return data

    added = 0
    for char in new_characters:
        char_name = char['name'].lower()
        if char_name not in data["chars"]:
            data["chars"][char_name] = {
                "name": char['name'].lower(),
                "background": char.get('role', ''),
                "act": char.get('characteristics', ''),
                "info": char.get('backstory', ''),
                "init": "",
                "q_hello": "",
                "q_important": "",
                "q_help": "",
                "notes": ""
            }
            added += 1

    if added > 0:
        print(f"Added {added} new characters to the story")
    return data


def parse_new_characters(story_text, client, data, model_name):
    """Extract new characters from story text using LLM and update the data structure"""

    prompt = f"""Analyze this story segment and extract any NEW important characters:
    
    {story_text}
    
    Format response as JSON array with objects containing:
    - name (string): The character's full name
    - role (string): The character's role/background (e.g., "military commander", "scientist", "reporter")
    - characteristics (string): Key personality traits and behaviors (e.g., "brave and strategic", "curious and analytical")
    - backstory (string): Important background information and knowledge the character possesses
        
    Guidelines:
    1. Include ONLY newly introduced characters that should persist in the story
    2. Make role/background specific and descriptive
    3. Focus on defining characteristics that would affect how they interact
    4. Include relevant knowledge in backstory that would be useful for conversations
    5. Keep descriptions concise but informative
    6. Ensure the character would be interesting to interact with
    
    Example format:
    {{
        "characters": [
            {{
                "name": "General Lisa Chen",
                "role": "Chief Strategist of Earth Defense Force",
                "characteristics": "Analytical, decisive, and deeply committed to Earth's defense",
                "backstory": "Expert in alien technology analysis and military strategy, has studied previous alien encounters extensively"                
            }}
        ]
    }}"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        new_characters = json.loads(
            response.choices[0].message.content).get('characters', [])
        
        return update_chars(new_characters, data)
    
    except Exception as e:
        print(f"Character parsing failed: {str(e)}")
        return data


def story_generation(client, model_name, data, user_text, latest_text):
    char_summary = format_characters(data)
    latest_text_passage = latest_text['documents']

    system_prompt = f"""You are a creative writing professional specializing in {data["story"]["genre"]} stories. \
    The user will give you an in progress story and you will continue it in a manner that makes sense given the provided \
    information and does not break continuity or violate any facts already established in the universe of the story.
     
    Your response:
    1. Must respond directly to the action provided by the user
    
    2. NOT generate any dialogue for the main character.
    """

    user_prompt = f"""Given the following story that is currently in progress, a cast of characters, and the most \
    recent action by the main character, write a continuation to the story that happens as a response to the most recent \
    action by the main character.
    
    Your response should:
    1. Response length has no limit(can be as short as one sentences or as long as several paragraphs)
    2. Maintain genre conventions
    3. Use character backstory appropriately
    4. NOT need to include all characters. ONLY include characters that would make sense given the most recent action.
    5. NOT include suggestions, notes, or commentary
    6. NOT generate dialogue for the main Character. That will be left up to the user.
    7. Strictly avoid phrases like "could be continued" or "next chapter"
    8. Never include out-of-story text in parentheses/brackets
    
    Here is the story so far:
    {latest_text_passage}
    
    With this set of Non Player Characters:
    {char_summary}

    Here is the most recent action by the main character that you are responding to:
    {user_text}

    """

    try:
        if model_name == "claude-3-opus-20240229":
            response = client.messages.create(
                model=model_name,
                temperature=0.6,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
        elif model_name == "mistral-large-latest":
            response = client.chat.complete(
                model=model_name,  # or "mistral-small"
                messages=[
                    {"role": "system",
                     "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
        else:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system",
                     "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=1200
            )

        return response

    except Exception as e:
        print(f"\nError: {str(e)}")


def get_starting_prompt(data):
    characters_string = format_characters(data)
    return f"""##Please generate the beginning of a story using the following parameters:
                The genre is: {data["story"]["genre"]}
                The goal of the main character is: {data["story"]["goal"]}
                Here is an overview of the storyline: {data["story"]["storyline"]}

                ##Enforce the following constaints:
                The main character is separate from the characters mentioned in the following section.
                
                ##Please include the following characters with the provided details and starting conditions in a way that feels natural to the story:
                {characters_string}
                """


def get_initial_gen(client, model_name, prompt):
    system_prompt = """You are a expert serial fiction writer helping the user write the start of \
                a first person story that the user can then continue. The user will provide a genre, \
                a rough overview of the storyline, and a set of characters that are present in the story. Please use the \
                information provided by the user to write the BEGINNING of a story with the following requirements.
                
                Requirements:
                - Generate 1 to 2 paragraphs that sets the stage for main characters to embark on a path to achieve the provided goal
                - Builds tension but doesn't resolve completely
                - Ends with an open-ended situation that provides the user various options for their next action
                - Maintains genre conventions
                - Uses characters' backstories appropriately
                - NO suggestions, notes, or commentary
                - DO NOT generate dialogue for the main Character. That will be left up to the user.
                - Strictly avoid phrases like "could be continued" or "next chapter"
                - Never include out-of-story text in parentheses/brackets
                - Maintain immersive storytelling only"""
    
    if model_name == "claude-3-opus-20240229":
        print("claude")
        return client.messages.create(
                model=model_name,
                temperature=0.6,
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
    elif model_name == "mistral-large-latest":
        print("mistral")
        return client.chat.complete(
            model=model_name,
            messages=[
                {"role": "system",
                 "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
)
    else:
        print("not claude or mistral")
        return client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )


def check_goal(client, model_name, data):
    history = data["history"]
    last_user_index = None
    last_user_prompt = None
    for i in range(len(history) - 1, -1, -1):
        if history[i][0] == "User":
            last_user_index = i
            last_user_prompt = history[i][1]
            break

    latest_story_before_user = None

    if last_user_index is not None:
        for i in range(last_user_index - 1, -1, -1):
            if history[i][0] == "story":
                latest_story_before_user = history[i][1]
                break

    storyline = data["story"]["storyline"]
    goal = data["story"]["goal"]
    chars = data.get("chars", {})
    character_summaries = "\n".join([
        f"{c['name']}: {c['background']}" for c in chars.values()
    ])

    system_prompt = f"""
        Analyze the player's action in relation to the goal.
        Storyline: {storyline}
        Current Story Segment: {latest_story_before_user}
        Player's Action: {last_user_prompt}
        Goal of the Story: {goal}
        Characters:
        {character_summaries}

        Determine:
        - If the action progresses towards the goal
        - If the action leads to failure (game over)
        - If the action achieves the goal (win)

        Respond in JSON format:
        {{
            "status": "progress" | "game_over" | "win",
            "reason": "Brief explanation"
            "ending_line": A dramatic narrative sentence for win or game_over status, otherwise leave empty.
        }}
    """

    if model_name == "claude-3-opus-20240229":
        response = client.messages.create(
            model=model_name,
            temperature=0.6,
            max_tokens=1000,
            system="""You are an evaluation metric whose job is to analyze the actions of the main character in 
            the provided story to determine whether or not they have achieved their goal. 
            Always respond with a valid JSON object. Do NOT respond with anything that is not a JSON object""",
            messages=[
                {"role": "user", "content": system_prompt}
            ]
        )
    elif model_name == "mistral-large-latest":
        response = client.chat.complete(
            model=model_name,  # or "mistral-small"
            messages=[
                {"role": "system",
                 "content": """You are an evaluation metric whose job is to analyze the actions of the main character 
                 in the provided story to determine whether or not they have achieved their goal"""},
                {"role": "user", "content": system_prompt}
            ],
            response_format={"type": "json_object"}
        )
    else:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role":"system", "content": """You are an evaluation metric whose job is to analyze the actions of the main character 
                 in the provided story to determine whether or not they have achieved their goal"""},
                      {"role": "user", "content": system_prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
    if model_name == "claude-3-opus-20240229":
        response = response.content[0].text
    else:
        response = response.choices[0].message.content
    result = json.loads(response)
    status = result.get("status", "progress")
    reason = result.get("reason", "")
    ending_line = result.get("ending_line", "")
    return status, reason, ending_line

# not used
