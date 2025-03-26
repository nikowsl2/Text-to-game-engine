import json


class StoryInput:
    def __init__(self, description_file, characters_file, goals_file):
        self.description_file = description_file
        self.characters_file = characters_file
        self.goals_file = goals_file

    def load_json_file(self, file_path):
        """Load data from a JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)

    def print_contents(self):
        """Print the contents of the description, characters, and goals files."""
        description_data = self.load_json_file(self.description_file)
        characters_data = self.load_json_file(self.characters_file)
        goals_data = self.load_json_file(self.goals_file)

        print("Description Data:")
        print(json.dumps(description_data, indent=2))

        print("\nCharacters Data:")
        print(json.dumps(characters_data, indent=2))

        print("\nGoals Data:")
        print(json.dumps(goals_data, indent=2))


def main():

    description_file = 'description.json'
    characters_file = 'characters.json'
    goals_file = 'goals.json'

    story_input = StoryInput(description_file, characters_file, goals_file)
    story_input.print_contents()


if __name__ == "__main__":
    main()
