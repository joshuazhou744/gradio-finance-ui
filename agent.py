from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self):
        model = ChatOpenAI(model="gpt-5-nano")
        workflow = StateGraph(state_schema=MessagesState)

        def call_model(state: MessagesState):
            system_prompt = (
                "You are a helpful assistant. Answer all questions to the best of your ability."
            )
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = model.invoke(messages)
            return {"messages": response}
        
        workflow.add_node("call_model", call_model)
        workflow.add_edge(START, "call_model")

        self.memory = MemorySaver()
        self.app = workflow.compile(checkpointer=self.memory)

    def invoke_agent(self, thread_id: str, text: str):
        return self.app.invoke(
            {"messages": [HumanMessage(content=text)]},
            config={"configurable": {"thread_id": thread_id}}
        )

agent = Agent()