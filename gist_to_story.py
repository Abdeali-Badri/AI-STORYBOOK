from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

def generate_story_with_moral(gist, max_chars=1000):
    """Generate a children's story from a gist using OpenAI"""
    
    prompt = f"""
Write a children's picture book story for ages 3-7 about: {gist}

Rules:
- Total length about {max_chars} characters
- One main character
- Include a title
- Include a STORY_OVERVIEW describing the entire story visually
- Split story into short pages (3-4 sentences)
- Each page must have TEXT and SCENE
- End with a clear moral

Format EXACTLY like this:

TITLE: ...

STORY_OVERVIEW: ...

CHARACTER:
NAME: ...
DESCRIPTION: ...

PAGE:
TEXT: ...
SCENE: ...

MORAL: ...
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9
    )

    raw = response.choices[0].message.content.strip()
    lines = [l.strip() for l in raw.split("\n") if l.strip()]

    title = ""
    story_overview = ""
    character = {}
    pages = []
    moral = ""

    text = ""
    scene = ""

    for line in lines:
        low = line.lower()

        if low.startswith("title:"):
            title = line[6:].strip()

        elif low.startswith("story_overview:"):
            story_overview = line[15:].strip()

        elif low.startswith("name:"):
            character["name"] = line[5:].strip()

        elif low.startswith("description:"):
            character["description"] = line[12:].strip()

        elif low.startswith("page"):
            if text and scene:
                pages.append({"text": text, "scene": scene})
            text = ""
            scene = ""

        elif low.startswith("text:"):
            text = line[5:].strip()

        elif low.startswith("scene:"):
            scene = line[6:].strip()

        elif low.startswith("moral:"):
            if text and scene:
                pages.append({"text": text, "scene": scene})
            moral = line[6:].strip()
            break

    return {
        "title": title,
        "story_overview": story_overview,
        "pages": pages,
        "character": character,
        "moral": moral
    }