# %% [markdown]
# # media evaluator
# ## iterative workflow
# ### real life example for itterative work flow basically its a workflow in which we run loop on nodes to get result 

# %%
from langgraph.graph import StateGraph,START,END
from langchain_openai import ChatOpenAI
from typing import TypedDict,Literal,Annotated
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
import os
import operator
load_dotenv()

# %%
llm_generator=ChatOpenAI(model="gpt-4o-mini")
llm_evaluator=ChatOpenAI(model="gpt-4o")
llm_optimizer=ChatOpenAI(model="gpt-4o")

# %%
from typing import TypedDict,Literal,Annotated

class Tweeterpost(TypedDict):
    topic:str
    post_generation:str
    post_evaluation: Literal["good","needs improvement"]
    post_optimization:str
    iteration:int
    max_iterations:int
    final_post:str
    tweet_history: Annotated[list[str], operator.add]
    feedback_history: Annotated[list[str], operator.add]

# %%
graph=StateGraph(Tweeterpost)

# %%
def generate_tweet(state:Tweeterpost)->Tweeterpost:
    prompt=f"you are expert in writing post for twitter/X platform . i am providing you a topic that is  {state['topic']} write me a twitter post on this topic . post should be funny and realistic"
    tweet=llm_generator.invoke(prompt).content
    
    return {"post_generation":tweet,"tweet_history":[tweet]}

# %%
from pydantic import Field,BaseModel
class Twitter_evaluation(BaseModel):
    evaluation:Literal["good","needs improvement"]=Field(...,description="final_evaluation")

    feedback:str=Field(...,description="feedback for the tweet")

# %%
structure_evaluator=llm_evaluator.with_structured_output(Twitter_evaluation)

# %%
def evaluation_tweet(state:Tweeterpost)->Tweeterpost:
    prompt=f"""i am providing you a tweet that is  {state['post_generation']} please provide me a evaluation of this tweet . tweet should be funny and realistic
    Use the criteria below to evaluate the tweet:

1. Originality – Is this fresh, or have you seen it a hundred times before?  
2. Humor – Did it genuinely make you smile, laugh, or chuckle?  
3. Punchiness – Is it short, sharp, and scroll-stopping?  
4. Virality Potential – Would people retweet or share it?  
5. Format – Is it a well-formed tweet (not a setup-punchline joke, not a Q&A joke, and under 280 characters)?

Auto-reject if:
- It's written in question-answer format (e.g., "Why did..." or "What happens when...")
- It exceeds 280 characters
- It reads like a traditional setup-punchline joke
- Dont end with generic, throwaway, or deflating lines that weaken the humor (e.g., “Masterpieces of the auntie-uncle universe” or vague summaries)

### Respond ONLY in structured format:
- evaluation: "approved" or "needs_improvement"  
- feedback: One paragraph explaining the strengths and weaknesses
    
    """
    evaluate_tweet=structure_evaluator.invoke(prompt)
    evaluation = evaluate_tweet.evaluation
    feedback = evaluate_tweet.feedback
    return {"post_evaluation": evaluation, "post_optimization": feedback,"feedback_history":[feedback]}

# %%
def optimize_tweet(state:Tweeterpost)->Tweeterpost:
    prompt=f"""i am providing you a tweet that is  {state['post_generation']} and its evaluation that is {state['post_evaluation']}. please generate optimized  tweet based on the evaluation
    Improve the tweet based on this feedback:
"{state['post_optimization']}"

Topic: "{state['topic']}"
Original Tweet:
{state['post_generation']}

Re-write it as a short, viral-worthy tweet. Avoid Q&A style and stay under 280 characters."""
    optimized_tweet=llm_optimizer.invoke(prompt).content
    iteration=state["iteration"]+1
    
    return {"post_optimization":optimized_tweet,"iteration":iteration,"tweet_history":optimized_tweet}

# %%
def check_condition(state:Tweeterpost)->Literal["good","needs improvement"]:
    if state["post_evaluation"] == "good" or state["iteration"] == state["max_iterations"]:
        return "good"
    else:
        return "needs improvement"

# %%
#add node
# Check if the node "generation" is already present before adding
if "generation" not in graph.nodes:
    graph.add_node("generation", generate_tweet)

# Add other nodes
if "evaluation" not in graph.nodes:
    graph.add_node("evaluation", evaluation_tweet)

if "optimization" not in graph.nodes:
    graph.add_node("optimization", optimize_tweet)
# graph.add_node("final_post",final_post)

#add edge
graph.add_edge(START,"generation")
graph.add_edge("generation","evaluation")
graph.add_conditional_edges("evaluation",check_condition,{"good":END,"needs improvement":"optimization"})

# graph.add_edge("evaluation",END)
# graph.add_edge("optimization",check_condition)
graph.add_edge("optimization",END)

#compile


# %%
workflow=graph.compile()

# %%
# from IPython.display import Image
# Image(workflow.get_graph().draw_mermaid_png())

# %%
initial_state = {
    "topic": "srhberhb",
    "iteration": 1,
    "max_iterations": 5
}
final_state=workflow.invoke(initial_state)
print(final_state)
print("********************")
for post_generations in final_state['tweet_history']:
    print(post_generations)

# %%



