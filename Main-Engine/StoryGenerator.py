from openai import OpenAI
import json
import os
import time
import re

HISTORY_FILE = "history.json"
PROTAGONISTS_FILE = "protagonists.json"
MODEL_NAME = "llama3-8b-8192"


def get_client():
    return OpenAI(
        api_key="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",
        base_url="https://api.groq.com/openai/v1"
    )


def save_to_history(story_text, user_input, uer_input_analysis = ""):
    """Save FULL generated story to history file"""
    entry = {
        "time": time.time(),
        "user_input": user_input,
        "story_segment": story_text,
        "uer_input_analysis": uer_input_analysis
    }

    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f:
            json.dump([], f)

    try:

        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)

        history.append(entry)

        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)

    except Exception as e:
        print(f"Warning: Could not save history - {str(e)}")


def load_characters():
    """Load and validate character JSON file"""
    filename = PROTAGONISTS_FILE

    try:
        with open(filename, 'r') as f:
            characters = json.load(f)

        required_fields = ['name', 'role', 'characteristics', 'backstory']
        for idx, char in enumerate(characters):
            for field in required_fields:
                if field not in char:
                    raise ValueError(
                        f"Character {idx+1} missing '{field}' field")
            if not isinstance(char['name'], str):
                raise ValueError("Character names must be strings")

        return characters

    except Exception as e:
        print(f"Error loading characters: {str(e)}")
        exit(1)


def format_characters(characters):
    """Format character data for prompt"""
    return "\n".join(
        f"- {char['name']} ({char['role']}): "
        f"Characteristics: {char['characteristics']}. "
        f"Backstory: {char['backstory']}"
        for char in characters
    )


def get_last_story_segment():
    """Retrieve the most recent story segment from history"""
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
            if not history:
                return None
            return history[-1]['story_segment']
    except Exception as e:
        print(f"Error loading history: {str(e)}")
        return None


def get_goal():
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
            if not history:
                return None
            user_input = history[0].get("user_input", "")
            for part in user_input.split(", "):
                if part.startswith("Goal:"):
                    goal = part.split("Goal:")[1].strip()
                    break
            return goal
    except Exception as e:
        print(f"Error loading goal from history: {str(e)}")
        return None


def update_protagonists(new_characters):
    """Add new characters to protagonists file"""
    if not new_characters:
        return

    existing = []
    if os.path.exists(PROTAGONISTS_FILE):
        with open(PROTAGONISTS_FILE, 'r') as f:
            existing = json.load(f)

    added = 0
    for char in new_characters:
        if not any(c['name'].lower() == char['name'].lower() for c in existing):
            existing.append(char)
            added += 1

    with open(PROTAGONISTS_FILE, 'w') as f:
        json.dump(existing, f, indent=2)
    if (added > 0):
        print(f"Added {added} new characters to {PROTAGONISTS_FILE}")


def parse_new_characters(story_text):
    """Extract new characters from story text using LLM"""
    client = get_client()

    prompt = f"""Analyze this story segment and extract any NEW important characters:
    
    {story_text}
    
    Format response as JSON array with objects containing:
    - name (string)
    - role (string)
    - characteristics (string)
    - backstory (string)
    Include ONLY newly introduced characters that should persist in the story."""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content).get('characters', [])
    except Exception as e:
        print(f"Character parsing failed: {str(e)}")
        return []


def run_mode2():
    client = get_client()

    last_segment = get_last_story_segment()
    if not last_segment:
        print("No existing story found in history!")
        return

    characters = load_characters()
    char_summary = format_characters(characters)
    goal = get_goal()
    turn = 0

    while True:
        turn += 1
        print(f"\n=== Turn {turn} ===")
        continuation_prompt = input(
            "Next story direction (or 'stop generation'): ")
        if continuation_prompt.lower() == 'stop generation':
            break

        system_prompt = f"""Continue the story from this segment:
        {last_segment}
        
        Existing Characters:
        {char_summary}
        
        New Input: {continuation_prompt}
        
        Requirements:
        - Generate 2-3 paragraphs of pure narrative continuation
        - NO suggestions, notes, or commentary
        - End with a scene break/cliffhanger in-universe
        - Strictly avoid phrases like "could be continued" or "next chapter"
        - Never include out-of-story text in parentheses/brackets
        - Maintain immersive storytelling only"""

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Expert serial fiction writer"},
                    {"role": "user", "content": system_prompt}
                ],
                temperature=0.8,
                max_tokens=1000
            )

            new_segment = response.choices[0].message.content
            new_segment = new_segment.split(
                "(Could be continued")[0]  # Remove trailing suggestions
            new_segment = re.sub(r"\(.*?\)", "", new_segment)
            print(new_segment)

            # Check if action aligns with goal
            goal_checking_prompt = f"""Analyze the player's action in relation to the goal.

            Current Story Segment:
            {last_segment}

            Player's Action:
            {continuation_prompt}

            Goal of the Story:
            {goal}

            Determine:
            - If the action progresses towards the goal
            - If the action leads to failure (game over)
            - If the action achieves the goal (win)
            
            Respond in JSON format:
            {{
                "status": "progress" | "game_over" | "win",
                "reason": "Brief explanation"
            }}"""

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": goal_checking_prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            status = result.get("status", "progress")
            reason = result.get("reason", "")

            save_to_history(new_segment, continuation_prompt, reason)
            new_chars = parse_new_characters(new_segment)
            update_protagonists(new_chars)

            last_segment = new_segment
            if new_chars:
                characters.extend(new_chars)
                char_summary = format_characters(characters)

            if status == "game_over":
                print(f"\n❌ Game Over: {reason}")
                break
            elif status == "win":
                print(f"\n🎉 You Win! {reason}")
                break
            else:
                print(f"\n✅ Progress: {reason}")

        except Exception as e:
            print(f"\nGeneration error: {str(e)}")


def run_mode1():
    client = get_client()

    # Get story elements
    genre = input("Enter genre: ").strip()
    storyline = input("Enter story setup: ").strip()
    goal = input("Enter story goal (what the protagonist must achieve): ").strip()

    # Load characters from JSON
    characters = load_characters()
    char_summary = format_characters(characters)

    system_prompt = f"""You are a creative writing professionals. Generate a 3-5 paragraph story that:
Genre: {genre}
Main Characters:
{char_summary}

Story Setup: {storyline}

Create an engaging narrative that:
- Builds tension but doesn't resolve completely
- Ends with a cliffhanger or unresolved situation
- Develops character relationships
- Maintains genre conventions
- Uses characters' backstories appropriately"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system",
                    "content": "Award-winning writer specializing in episodic fiction"},
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.95,
            max_tokens=1200
        )

        full_story = response.choices[0].message.content
        print("\nHere's your ongoing story:\n")
        print(full_story)

        user_input = f"Genre: {genre}, Storyline: {storyline}, Goal: {goal}"
        save_to_history(full_story, user_input)
        run_mode2()

    except Exception as e:
        print(f"\nError: {str(e)}")


def main():
    print("✨ Story Generator ✨")
    print("1. Start New Story")
    print("2. Exiting")

    mode = input("\nSelect (1/2): ").strip()

    if mode == "1":
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        run_mode1()
    """ elif mode == "2":
        if not os.path.exists(HISTORY_FILE) or not os.path.exists(PROTAGONISTS_FILE):
            print("Required files missing! Start with Mode 1 first.")
            return
        run_mode2() """


if __name__ == "__main__":
    main()
