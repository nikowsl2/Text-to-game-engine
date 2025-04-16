from openai import OpenAI

def run_mode1():
    client = OpenAI(
        api_key="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",
        base_url="https://api.groq.com/openai/v1"
    )

    story_elements = {
        "genre": None,
        "protagonists": None,
        "goal": None,
        "storyline": None
    }

    for element in story_elements:
        user_input = input(f"Enter {element.replace('_', ' ')}: ")
        story_elements[element] = user_input

    system_prompt = """You are a creative writing assistant. Generate a short story using these elements:
    - Genre: {genre}
    - Protagonists: {protagonists}
    - Goal: {goal}
    - Storyline: {storyline}

    Make it compelling and follow the genre conventions. Length: 3-5 paragraphs."""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an award-winning fiction writer"},
                {"role": "user", "content": system_prompt.format(**story_elements)}
            ],
            temperature=0.9,
            max_tokens=1000
        )

        story = response.choices[0].message.content
        print("\nHere's your generated story:\n")
        print(story)

    except Exception as e:
        print(f"\nError: {str(e)}")

def main():
    print("✨ Story Generator Modes ✨")
    print("1. Custom Story Mode (Provide specific elements)")
    print("2. [Mode 2 Description Pending]")
    
    mode = input("\nSelect a mode (1/2): ").strip()
    
    if mode == "1":
        run_mode1()
    elif mode == "2":
        print("\nMode 2 is under development. Stay tuned!")
    else:
        print("\nInvalid selection. Please choose 1 or 2.")

if __name__ == "__main__":
    main()