import os
from typing import Dict, Tuple, List, Any

import gradio as gr
import pandas as pd


def get_accounts() -> Dict[str, str]:
    base_dir = os.path.dirname(__file__)
    return {
        "Middle Class Person": os.path.join(base_dir, "middle_class_person_expense.csv"),
        "High Net Worth Person": os.path.join(base_dir, "high_net_worth_person_expense.csv"),
        "Student": os.path.join(base_dir, "student_person_expense.csv"),
    }


def load_account_data(account_name: str) -> Tuple[pd.DataFrame, str]:
    accounts = get_accounts()
    path = accounts.get(account_name, "")
    if not path or not os.path.exists(path):
        empty_df = pd.DataFrame()
        return empty_df, f"No data found for '{account_name}'."

    try:
        df = pd.read_csv(path)
    except Exception as e:
        return pd.DataFrame(), f"Failed to load data: {e}"

    info = f"Showing {os.path.basename(path)} — {len(df)} rows"
    return df, info


def send_chat(user_message: str, history: List[List[str]]) -> Tuple[List[List[str]], str]:
    user_message = (user_message or "").strip()
    if not user_message:
        return history, ""

    response = "This is a placeholder assistant. We'll connect the real agent soon."
    updated_history = (history or []) + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}
    ]
    return updated_history, ""


custom_css = """
#account_box, #selector_box, #chat_box {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px;
}
#transactions_df table {
  font-size: 14px;
}
"""


def build_ui() -> gr.Blocks:
    accounts = get_accounts()
    default_account = "Middle Class Person" if "Middle Class Person" in accounts else list(accounts.keys())[0]

    with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.Markdown("## Personal Finance Dashboard")

        with gr.Row(equal_height=True):
            with gr.Column(scale=7, min_width=480):
                with gr.Group(elem_id="account_box"):
                    gr.Markdown("**Account Transactions**")
                    transactions_df = gr.Dataframe(
                        value=None,
                        interactive=False,
                        wrap=True,
                        elem_id="transactions_df",
                        label="",
                    )
            with gr.Column(scale=5, min_width=360):
                with gr.Group(elem_id="selector_box"):
                    gr.Markdown("**Select Account/User**")
                    account_dropdown = gr.Dropdown(
                        choices=list(accounts.keys()),
                        value=default_account,
                        label="Account/User",
                    )
                    account_info = gr.Markdown("", elem_id="account_info")

        with gr.Row():
            with gr.Column():
                with gr.Group(elem_id="chat_box"):
                    gr.Markdown("**Assistant** — simple chatbot UI (agent to be connected later)")
                    chat_history = gr.Chatbot(label="Agent Chat", type="messages")
                    with gr.Row(equal_height=True):
                        user_input = gr.Textbox(
                            show_label=False,
                            placeholder="Type a message and press Send…",
                            lines=1,
                            scale=8,
                        )
                        send_btn = gr.Button("Send", variant="primary", scale=1)

        # Wiring: account selection updates transactions table and info
        account_dropdown.change(
            fn=load_account_data,
            inputs=account_dropdown,
            outputs=[transactions_df, account_info],
            preprocess=True,
            postprocess=True,
        )

        # Initialize with default account on load
        demo.load(
            fn=load_account_data,
            inputs=account_dropdown,
            outputs=[transactions_df, account_info],
        )

        # Chat events
        send_btn.click(
            fn=send_chat,
            inputs=[user_input, chat_history],
            outputs=[chat_history, user_input],
        )
        user_input.submit(
            fn=send_chat,
            inputs=[user_input, chat_history],
            outputs=[chat_history, user_input],
        )

    return demo


if __name__ == "__main__":
    app = build_ui()
    app.launch()
