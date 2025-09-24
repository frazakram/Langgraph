from langgraph.graph import StateGraph,START,END
from typing import TypedDict, Literal,Annotated
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage

from dotenv import load_dotenv
load_dotenv()
class Chat_bot(TypedDict):
    question: str
    chat_reply: str
graph=StateGraph(Chat_bot)
model=ChatOpenAI(model="gpt-4o-mini")
def chatting(state:Chat_bot)->Chat_bot:
    while True:

        if state["question"] in {"Q"}:
            break
    
        prompt=f"you are expert in giving answer on question . i am providing you a question that is  {state['question']} write me a answer on this question . answer should be funny and realistic"
        state["chat_reply"]=model.invoke(prompt).content
    return state
#add node
graph.add_node("chat_reply",chatting)

#add edge
graph.add_edge(START,"chat_reply")
graph.add_edge("chat_reply",END)
#compile
workflow=graph.compile()

#invoke
initial_state={"question":input("enter your question"),"chat_reply":""}
final_state=workflow.invoke(initial_state)
print(final_state['chat_reply'])