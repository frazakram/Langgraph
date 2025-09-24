from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Literal,Annotated
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,BaseMessage
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
checkpointer=MemorySaver()
load_dotenv()
model=ChatOpenAI(model="gpt-4o-mini")
# from langgraph.graph.message import add_messages

# class Chat_bot(TypedDict):
#     messages=Annotated[list[BaseMessage],add_messsages]
from langgraph.graph.message import add_messages

class Chat_bot(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]
graph=StateGraph(Chat_bot)
def chatbot(state:Chat_bot)->Chat_bot:

    messages = state['messages']

    response=model.invoke(messages).content
    return {"messages":[response]}
graph.add_node("chatbot",chatbot)
graph.add_edge(START,"chatbot")
graph.add_edge("chatbot",END)
workflow=graph.compile(checkpointer=checkpointer)
# initial_state = {
#     'messages': [HumanMessage(content='What is the capital of india')]
# }
thread_id='1'
while True:
    user_message=input("enter your message : ")
    print("User",user_message)

    if user_message.strip().lower() in ["quit","exit"]:
        break
    config={"configurable":{"thread_id":thread_id}}
    response = workflow.invoke({"messages":[HumanMessage(content=user_message)]},config=config)


    print("AI message",response['messages'][-1].content)
workflow.get_state(config=config)
