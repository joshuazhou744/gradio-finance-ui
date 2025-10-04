from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_community.document_loaders import UnstructuredMarkdownLoader

from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self):
        model = ChatOpenAI(model="gpt-5-nano")
        workflow = StateGraph(state_schema=MessagesState)

        def load_markdown(path: str):
            loader = UnstructuredMarkdownLoader(path)
            docs = loader.load()
            return docs

        def call_model(state: MessagesState, config):
            thread_id = config["configurable"]["thread_id"]
            report_path = config["configurable"]["report_path"]

            system_prompt = SystemMessage(
                content="You are a helpful assistant. Answer all questions to the best of your ability."
            )

            docs = load_markdown(report_path)
            context_message = SystemMessage(content=f"Here is reference context for this account:\n{docs}")

            messages = [system_prompt, context_message] + state["messages"]

            response = model.invoke(messages)
            return {"messages": [response]}
        
        workflow.add_node("call_model", call_model)
        workflow.add_edge(START, "call_model")

        self.memory = MemorySaver()
        self.app = workflow.compile(checkpointer=self.memory)

    def invoke_agent(self, thread_id: str, report_path: str, text: str):
        return self.app.invoke(
            {"messages": [HumanMessage(content=text)]},
            config={"configurable": {"thread_id": thread_id, "report_path": report_path}}
        )

agent = Agent()