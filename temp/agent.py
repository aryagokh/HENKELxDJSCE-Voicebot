# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_experimental.agents import create_pandas_dataframe_agent
# from langchain.prompts import PromptTemplate
# from langchain_core.output_parsers import PydanticOutputParser
# from langchain.agents.agent_types import AgentType
# from langchain_core.tools import tool
# from pydantic import Field, BaseModel
# import pandas as pd
# from config import get_secret, where_is_it_running
# import time

# llm = ChatGoogleGenerativeAI(
#     model = 'gemini-2.0-flash',
#     temperature=0,
#     api_key = get_secret("GEMINI_API_KEY")
# )

# model = ChatGoogleGenerativeAI(
#     model = 'gemini-2.0-flash-lite',
#     temperature=0,
#     api_key = get_secret("GEMINI_API_KEY")
# )

# def get_df():
#     """
#     Loads Dataframe
#     """
#     where_is_prog_running = where_is_it_running()
#     print(where_is_prog_running)
#     if where_is_prog_running=='local':
#         print("Local Running...")
#         df = pd.read_excel(io='./data/excel/henkel_inventory_dummy_data.xlsx')
#         return df
#     elif where_is_prog_running == 'streamlit':
#         # Handle when deployable
#         raise

# @tool
# def dataframe_scraper(query: str)->str:
#     """
#     Uses a language model agent to answer a query about the data.
#     This tool is intended to allow an LLM to interact with tabular data stored in an Excel file.

#     Parameters:
#         query (str): A natural language question or instruction about the data.

#     Returns:
#         str: The result of the query execution by the agent, as a string. Returns None if an error occurs.
#     """
#     try:
#         print(f"Query sent to the agent: {query}")
#         df = get_df()
#         agent = create_pandas_dataframe_agent(
#             llm=llm,
#             df=df,
#             verbose=True,
#             agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#             allow_dangerous_code=True,
#             max_iterations=20
#         )
#         response = agent.invoke(query)
    
#         return response
    
#     except Exception as e:
#         print(e)

#     return None

# tools = [dataframe_scraper]
# model_with_tools = model.bind_tools(tools)


# class OutputSchema(BaseModel):
#     query: str = Field(description="The query sent to the tool to retrieve the information")
#     response: str = Field(description="The output received from the tool for the received query")
#     paraphrased_output: str = Field(description="The paraphrased output from the received which includes both query and the response but in the human-understandable format")

# parser = PydanticOutputParser(pydantic_object=OutputSchema)

# prompt = PromptTemplate(
#     template=
# """
# You are an expert Data Analyst for inventory management.
# You will be given input of the query which you need to pass to the dataframe_scraper tool provided.

# Query: {query}

# The answer should be direct and there should not be any filler text from your side.
# The answer should be in the following schema:
# {output_schema}
# """,
# input_variables=['query'],
# partial_variables={"output_schema" : parser.get_format_instructions()}
# )


# def retriever(query: str)-> dict:
#     retries, max_retries = 0, 5
#     while(retries < max_retries):
#         try:
#             response = model_with_tools.invoke(prompt.invoke(input={"query": query}))
#             response = parser.invoke(response)
#             return response
        
#         except Exception as e:
#             print(e)
#             retries+=1
#             time.sleep(5 * retries)
    
#     return None


# if __name__ == '__main__':
#     reponse = retriever(query="What is the total number of rows in the data? List down the names of all the columns")
#     for key, value in reponse:
#         print(f"{key}: {value}")
