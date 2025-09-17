import os
from typing import Dict, Tuple, List
import gradio as gr
import pandas as pd

# Global storage for accounts
accounts: Dict[str, str] = {}

def init_accounts() -> Dict[str, str]:
    """Initialize default accounts (existing CSVs if available)."""
    base_dir = os.path.dirname(__file__)
    default_accounts = {
        "middle_class_person_expense": os.path.join(base_dir, "middle_class_person_expense.csv"),
        "high_net_worth_person_expense": os.path.join(base_dir, "high_net_worth_person_expense.csv"),
    }
    return {k: v for k, v in default_accounts.items() if os.path.exists(v)}

def load_account_data(account_name: str) -> Tuple[pd.DataFrame, str]:
    path = accounts.get(account_name, "")
    if not path or not os.path.exists(path):
        return pd.DataFrame(), f"No data found for '{account_name}'."
    try:
        df = pd.read_csv(path)
    except Exception as e:
        return pd.DataFrame(), f"Failed to load data: {e}"
    return df, f"Showing {os.path.basename(path)} — {len(df)} rows"

def add_account(file_path: str):
    """Add uploaded CSV file as a new account."""
    if not file_path:
        return gr.update(), "No file uploaded.", gr.update(value=None)

    uploaded_filename = os.path.basename(file_path)
    
    for account_name, existing_path in accounts.items():
        if os.path.basename(existing_path) == uploaded_filename:
            return (
                gr.update(value=account_name),
                f"File already exists as {account_name}",
                gr.update(value=None)
            )

    filename = os.path.basename(file_path)
    account_name = os.path.splitext(filename)[0]
    accounts[account_name] = file_path

    return (
        gr.update(choices=list(accounts.keys()), value=account_name), 
        f"Added account: {account_name}",
        gr.update(value=None)
    )

def send_chat(user_message: str, history: List[dict]):
    user_message = (user_message or "").strip()
    if not user_message:
        return history, ""
    response = "This is a placeholder assistant. We'll connect the real agent soon."
    updated_history = (history or []) + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response},
    ]
    return updated_history, ""

custom_css = """
#account_box, #selector_box, #chat_box {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
}
#transactions_df table {
  font-size: 14px;
}

#upload_block{
    border-radius:5px;
}
"""

accounts = init_accounts()
default_account = next(iter(accounts.keys()), None)

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("# Finance Dashboard")

    with gr.Row(equal_height=True):
        with gr.Column(scale=7, min_width=480):
            with gr.Group(elem_id="account_box"):
                gr.Markdown("**Account Transactions**")
                transactions_df = gr.Dataframe(
                    value=None, interactive=False, wrap=True,
                    elem_id="transactions_df", label=""
                )
        with gr.Column(scale=5, min_width=360):
            with gr.Group(elem_id="selector_box"):
                gr.Markdown("**Select or Add Account/User**")
                account_dropdown = gr.Dropdown(
                    choices=list(accounts.keys()),
                    value=default_account,
                    label="Account/User",
                )
                account_info = gr.Markdown("", elem_id="account_info")
                file_upload = gr.File(
                    label="Upload CSV",
                    file_types=[".csv"],
                    type="filepath",
                    elem_id="upload_block"
                )
                upload_status = gr.Markdown("")

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

    # Wire dropdown change
    account_dropdown.change(
        fn=load_account_data,
        inputs=account_dropdown,
        outputs=[transactions_df, account_info],
    )

    # Initialize with default
    demo.load(
        fn=load_account_data,
        inputs=account_dropdown,
        outputs=[transactions_df, account_info],
    )

    # File upload adds new account & refreshes dropdown
    file_upload.upload(
        fn=add_account,
        inputs=file_upload,
        outputs=[account_dropdown, upload_status, file_upload],
    )

    # Chat
    send_btn.click(fn=send_chat, inputs=[user_input, chat_history],
                    outputs=[chat_history, user_input])
    user_input.submit(fn=send_chat, inputs=[user_input, chat_history],
                        outputs=[chat_history, user_input])

if __name__ == "__main__":
    demo.launch()
