import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END, MessagesState
from typing import TypedDict, Annotated, Literal
from langchain_core.tools import tool
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Define tools
@tool
def search(query: str):
    """Search for current weather information for a location. Returns weather description in the form of a string."""
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."

tools = [search]
tools_node = ToolNode(tools=tools)
llm_with_tools = llm.bind_tools(tools)

# Define agent function
def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Define router function
def router_function(state: MessagesState) -> Literal["tools", "END"]:
    messages = state['messages']
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tools"
    return "END"

# Setup workflow
def setup_workflow():
    memory = MemorySaver()
    workflow = StateGraph(MessagesState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tools_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        router_function,
        {"tools": "tools", "END": END}
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=memory)

def main():
    app = setup_workflow()

    # Configure memory with all required fields
    config = {
        "configurable": {
            "thread_id": "1",

        }
    }

    print("Welcome to the CLI Chatbot! Type 'quit' to exit.")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == 'quit':
            print("Goodbye!")
            break

        try:
            # Prepare the input for the workflow
            input_state = {"messages": [user_input]}

            # Get the response with config
            result = app.invoke(input_state, config=config)

            # Extract and print the assistant's response
            assistant_message = result["messages"][-1]
            print("\nAssistant:", assistant_message.content)

        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again.")

if __name__ == "__main__":
    main()
    