import json
import boto3
from openai import OpenAI
import os
import urllib.request
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

client = OpenAI(api_key=os.getenv("EMINENT_API_KEY"))


def send_email(headline, text, message):
    email = message.get("email", "")
    if not email or "@" not in email:
        print("No email provided")
        return

    ses = boto3.client("ses", region_name="eu-north-1")
    msg = MIMEMultipart("mixed")
    headline = headline.replace("'", "").replace('"', "")
    text = text.replace("'", "").replace('"', "")
    # Add subject, from and to lines
    msg["Subject"] = "AI-resultat från Eminent"
    msg["From"] = "axel@eminentfilm.se"
    msg["To"] = email

    msg_body = MIMEMultipart("alternative")

    textpart = MIMEText(
        f"""
    <html>
        <head></head>
        <body>
            <p>Hej!</p>
            <p>Här kommer AI-genererad text och bild för ditt företag. Kom ihåg att resultaten inte är perfekta och att problem med t.ex. fördomar och så kallade hallucinationer (AI:n hittar på) kan förekomma. Om du har några frågor är det bara att svara på detta mail.</p> 
            <h4 style="font-weight: bold; font-size: 14">{headline}</h4>
            <p>{text}</p>
            <p>Med vänlig hälsning,<br>Axel & Teodor<br>Eminent Film Sverige AB</p>
        </body>
    </html>
    """,
        "html",
    )
    msg_body.attach(textpart)

    msg.attach(msg_body)

    with open("/tmp/image.png", "rb") as file:
        imgpart = MIMEImage(file.read(), name=f"ai_image.png")
    msg.attach(imgpart)

    try:
        response = ses.send_raw_email(
            Source=msg["From"],
            Destinations=[msg["To"]],
            RawMessage={"Data": msg.as_string()},
        )
        return response
    except Exception as e:
        print(e)


def lambda_handler(event, context):
    messages = []
    records = event.get("Records", [])
    for record in records:
        message = json.loads(record.get("body"))
        messages.append(message)

    print(messages)
    for message in messages:
        create_content(message)

    return {"statusCode": 200, "body": json.dumps("Lambda finished")}


def list_files(s3, folder):
    file_names = []
    response = s3.list_objects_v2(Bucket="eminent-cdn", Prefix=folder)
    if response.get("Contents"):
        for obj in response["Contents"]:
            file_names.append(obj["Key"])
    while response.get("IsTruncated"):
        continuation_key = response.get("NextContinuationToken")
        response = s3.list_objects_v2(
            Bucket="eminent-cdn",
            Prefix=folder,
            ContinuationToken=continuation_key,
        )
        for obj in response["Contents"]:
            file_names.append(obj["Key"])
    return file_names


def find_highest_number(filenames):
    pattern = re.compile(r"\d+")
    numbers = []
    for filename in filenames:
        result = pattern.findall(filename)
        numbers.extend([int(num) for num in result])
    return max(numbers) if numbers else 0


def create_content(message):
    s3 = boto3.client("s3")
    bucket_name = "eminent-cdn"

    print(f"Creating image content for {message['company_name']}")
    create_image(message)

    print(f"Creating text content for {message['company_name']}")
    text = write_description(message)
    headline = write_headline(message)
    content = text + "<><>" + headline + "<><>" + message["company_name"]

    print(f"Finished creating content")

    text_files = list_files(s3, "ai/texts/")
    print(text_files)
    highest_number = find_highest_number(text_files)
    appendix = str(highest_number + 1)

    s3.put_object(
        Bucket=bucket_name,
        Key=f"ai/texts/description{appendix}.txt",
        Body=content,
        ACL="public-read",
    )
    s3.upload_file(
        "/tmp/image.png",
        "eminent-cdn",
        f"ai/images/cover{appendix}.png",
        ExtraArgs={"ACL": "public-read"},
    )
    print(f"Finished uploading content with index {appendix}")
    res = send_email(headline, text, message)
    print(res)


def write_description(message, model_name="gpt-3.5-turbo"):
    messages = [
        {
            "role": "system",
            "content": """Du är en hjälpsam assistent för att hjälpa företag att skapa en intresseväckande beskrivning av deras verksamhet. Användaren kommer ge dig lite information om sitt företag - du ska ta den informationen och skapa en försäljningspitch.""",
        },
        {
            "role": "user",
            "content": f"""
            Användaren skrev in följande information om sitt företag:
            
            Företagets namn: {message['company_name']}
            Verksamhet: {message['description']}

            Skapa en försäljningspitch. Svara bara med pitchen. Skriv den på svenska.
            """,
        },
    ]
    response = client.chat.completions.create(
        model=model_name, temperature=1, messages=messages, timeout=40
    )
    print("\n", response.usage)
    return response.choices[0].message.content.strip()


def write_headline(message, model_name="gpt-3.5-turbo"):
    messages = [
        {
            "role": "system",
            "content": """Du är en hjälpsam assistent för att hjälpa företag att skapa en intresseväckande rubrik till deras verksamhet. Användaren kommer ge dig lite information om sitt företag - du ska ta den informationen och skapa en kort men slagkraftig rubrik som sammanfattar företaget. Du är kreativ, fyndig och kortfattad..""",
        },
        {
            "role": "user",
            "content": f"""
            Användaren skrev in följande information om sitt företag:
            
            Företagets namn: {message['company_name']}
            Verksamhet: {message['description']}

            Skapa en intressant och spännande rubrik till företaget. Svara bara med rubriken. Skriv den på svenska.
            """,
        },
    ]
    response = client.chat.completions.create(
        model=model_name, temperature=1, messages=messages, timeout=40
    )
    print("\n", response.usage)
    return response.choices[0].message.content.strip()


def create_image(message, model_name="dall-e-3"):
    prompt = f"""
    Du ska generera en bild som representerar ett företag. Användaren kommer ge dig lite information om sitt företag - du ska ta den informationen och skapa en bild som representerar företaget. Bilden bör vara inspirerande, inte inkludera någon text eller logotyp. Det är viktigt att ingen text är med i bilden.

    Information om företaget: {message['description']}
    """
    response = client.images.generate(
        model=model_name,
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    print(image_url)
    urllib.request.urlretrieve(image_url, "/tmp/image.png")
    return image_url
