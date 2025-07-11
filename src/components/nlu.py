from langchain_google_genai import ChatGoogleGenerativeAI
import os
from pydantic import Field, BaseModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
import json
import time
from src.components.config import get_secret

model = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-lite',
    temperature=0,
    api_key = get_secret("GEMINI_API_KEY")
)

class ResponseSchema(BaseModel):
    actual_input: str = Field(description="The actual user input")
    user_intent: str = Field(description="What the user have asked for that can be processed by LLM in next chain")
parser = PydanticOutputParser(pydantic_object=ResponseSchema)

prompt = PromptTemplate(
    template='''
You are an expert in Natural Language Understanding for Inventory Management Domain.

Right now you are assigned to understand what the user have asked and paraphrase it to send it to the next LLM agent.
So you understand what the user have asked in prompt and return the same information, but in the format where agent can understand better.

The user input: {text}

The output should be in the following format:
{response_schema}
''',
input_variables=['text'],
partial_variables={'response_schema': parser.get_format_instructions()}
)

chain = prompt | model | parser


def understand_the_user(user_text: str)-> json:
    retries, max_retries = 0, 5
    while(retries < max_retries):
        try:
            response = chain.invoke(input={"text": user_text})
            return response

        except Exception as e:
            print(e)
            retries +=1
            time.sleep(5 * retries)

    return None
        

if __name__ == '__main__':
#     from stt import convert_speech_to_text
#     audio_file_path = './data/audios/harvard.wav'
#     transcription , elapsed_time = convert_speech_to_text(audio_file_path=audio_file_path)

    transcription = "Do we have any adhesives available for rubber tyres? If yes, where is it kept in the inventory?"
    actual_input, user_intent = understand_the_user(user_text=transcription)

    print(f"actual_input: {actual_input}\n\nuser_intent: {user_intent}")