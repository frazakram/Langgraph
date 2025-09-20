# %%
from langgraph.graph import StateGraph,START,END
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
load_dotenv()

# %%
class BlogPost(TypedDict):
    tittle: str
    outline: str
    blog: str

# %%
model=ChatOpenAI(model="gpt-4o-mini")

# %%
def outline(state:BlogPost)->BlogPost:
    tittle=state["tittle"]
    prompt1=f"i am giving you a tittle of a blog post {tittle}. Generate an outline for the blog post"
    outline=model.invoke(prompt1).content
    state['outline']=outline
    return state

# %%
def blog(state:BlogPost)->BlogPost:
    tittle=state["tittle"]
    blog=state["outline"]
    prompt2=f"i am giving you a tittle of a blog post {tittle} and outline {outline}. Generate content for the blog post using ouline {outline} ."
    blog=model.invoke(prompt2).content
    state['blog']=blog
    return state

# %%
graph=StateGraph(BlogPost)
#add node

graph.add_node("outline",outline)
graph.add_node("blog",blog)
#add edge
graph.add_edge(START,"outline")
graph.add_edge("outline","blog")
graph.add_edge("blog",END)

# %%
workflow=graph.compile()


# %%
# from IPython.display import Image
# Image(workflow.get_graph().draw_mermaid_png())

# %%
initial_state={"tittle":"Poverty in India"}
final_state=workflow.invoke(initial_state)
print(final_state)


# %%



