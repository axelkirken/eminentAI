from openai import OpenAI
import os
import urllib.request
from PIL import Image

client = OpenAI(api_key=os.getenv("EMINENT_API_KEY"))


def write_description(model_name="gpt-3.5-turbo"):
    messages = [
        {
            "role": "system",
            "content": """Du är en hjälpsam assistent för att hjälpa företag att skapa en intresseväckande beskrivning av deras verksamhet. Användaren kommer ge dig lite information om sitt företag - du ska ta den informationen och skapa en försäljningspitch.""",
        },
        {
            "role": "user",
            "content": f"""
            Användaren skrev in följande information om sitt företag:
            
            Företagets namn: Adesso
            Verksamhet: Vi tillverkar kaffemaskiner och liknande.

            Skapa en försäljningspitch. Svara bara med pitchen.
            """,
        },
    ]
    response = client.chat.completions.create(
        model=model_name, temperature=1, messages=messages, timeout=30
    )
    print("\n", response.usage)
    return response.choices[0].message.content


def create_image(model_name="dall-e-3"):
    prompt = """
    Du ska generera en bild som representerar ett företag. Användaren kommer ge dig lite information om sitt företag - du ska ta den informationen och skapa en bild som representerar företaget. Bilden bör vara inspirerande, inte inkludera någon text eller logotyp. 

    Information om företaget: Vi tillverkar kaffemaskiner och liknande.
    """
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    print(image_url)
    urllib.request.urlretrieve(image_url, "image.png")


create_image()
