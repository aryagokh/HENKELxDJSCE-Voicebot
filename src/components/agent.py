from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents.agent_types import AgentType
from langchain_core.tools import tool
from pydantic import Field, BaseModel
import pandas as pd
from config import get_secret, where_is_it_running
import time

llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash',
    temperature=0,
    api_key=get_secret("GEMINI_API_KEY")
)

model = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash',
    temperature=0,
    api_key=get_secret("GEMINI_API_KEY")
)

def get_df():
    """
    Loads Dataframe
    """
    where_is_prog_running = where_is_it_running()
    print(where_is_prog_running)
    if where_is_prog_running == 'local':
        print("Local Running...")
        df = pd.read_excel(io='./data/excel/henkel_inventory_dummy_data.xlsx')
        return df
    elif where_is_prog_running == 'streamlit':
        # Handle when deployable
        df = pd.read_excel(io='./data/excel/henkel_inventory_dummy_data.xlsx')
        return df
    else:
        raise ValueError(f"Unknown environment: {where_is_prog_running}")

@tool
def dataframe_scraper(query: str) -> str:
    """
    Uses a language model agent to answer a query about the data.
    This tool is intended to allow an LLM to interact with tabular data stored in an Excel file.

    Parameters:
        query (str): A natural language question or instruction about the data.

    Returns:
        str: The result of the query execution by the agent, as a string.
    """
    try:
        df = get_df()
        
        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=df,
            verbose=True,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            allow_dangerous_code=True,
            max_iterations=20,
            return_intermediate_steps=False
        )
        
        response = agent.invoke({"input": query})
        
        if isinstance(response, dict):
            output = response.get('output', str(response))
        else:
            output = str(response)

        return output
    
    except Exception as e:
        error_msg = f"Error in dataframe_scraper: {str(e)}"
        print(error_msg)
        return error_msg

tools = [dataframe_scraper]
model_with_tools = model.bind_tools(tools)

class OutputSchema(BaseModel):
    query: str = Field(description="The query sent to the tool to retrieve the information")
    response: str = Field(description="The complete output received from the tool for the received query (even if it is long)")
    paraphrased_output: str = Field(description="The paraphrased complete output from the received which includes the response but in the human-understandable format")

parser = PydanticOutputParser(pydantic_object=OutputSchema)

prompt = PromptTemplate(
    template="""
You are an expert Data Analyst for inventory management.
You will be given a query which you need to pass to the dataframe_scraper tool provided.

Query: {query}

Use the dataframe_scraper tool to get the answer. Make sure to call the tool with the exact query provided.
After getting the response from the tool, format it according to the output schema below.

The answer should be direct and there should not be any filler text from your side.
The answer should be in the following schema:
{output_schema}
""",
    input_variables=['query'],
    partial_variables={"output_schema": parser.get_format_instructions()}
)


def retriever(query: str) -> dict:
    retries, max_retries = 0, 5
    while retries < max_retries:
        try:
            formatted_prompt = prompt.format(query=query, output_schema=parser.get_format_instructions())
            response = model_with_tools.invoke(formatted_prompt)
            
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_result = dataframe_scraper.invoke(tool_call['args'])
                
                follow_up_prompt = f"""
                Based on the query: {query}
                The tool returned: {tool_result}

                Please format this according to the output schema:
                {parser.get_format_instructions()}
                """
                
                final_response = model.invoke(follow_up_prompt)
                
                parsed_response = parser.parse(final_response.content)
                return parsed_response
            else:
                tool_result = dataframe_scraper.invoke({"query": query})
                
                format_prompt = f"""
                Query: {query}
                Tool Response: {tool_result}

                Format this according to the schema:
                {parser.get_format_instructions()}
                """
                
                formatted_response = model.invoke(format_prompt)
                parsed_response = parser.parse(formatted_response.content)
                return parsed_response
        
        except Exception as e:
            print(f"Error in retriever (attempt {retries + 1}): {e}")
            retries += 1
            time.sleep(5 * retries)
    
    return None

if __name__ == '__main__':
    response = retriever(query="What is the total number of rows in the data? List down the names of all the columns")
    
    if response:
        if hasattr(response, '__dict__'):
            for key, value in response.__dict__.items():
                print(f"{key}: {value}")
        else:
            print(f"Response: {response}")
    else:
        print("Failed to get response after all retries")