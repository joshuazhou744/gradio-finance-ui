import os
import gradio as gr
import pandas as pd
from pydantic import BaseModel
from agent import agent

class Account(BaseModel):
    name: str
    bank_statement_path: str
    expenses_path: str
    income_path: str
    stocks_path: str
    report_path: str

# Global storage for accounts
accounts: dict[str, Account] = {}
current_csv_type: str = "bank_statement"  # Track current CSV type for refresh/export

def init_accounts() -> dict[str, Account]:
    """Initialize default accounts using configuration."""
    base_dir = os.path.join(os.path.dirname(__file__))

    # Account configurations: (display_name, folder_name, file_prefix)
    account_configs = [
        ("Middle Class Person", "middle", "middle_class_person"),
        ("Struggling Person", "low", "struggling_person"),
        ("Wealthy Person", "high", "wealthy_person"),
    ]

    accounts_dict = {}
    for display_name, folder, prefix in account_configs:
        account = Account(
            name=display_name,
            bank_statement_path=os.path.join(base_dir, "csvs", folder, f"{prefix}_bank_statement.csv"),
            expenses_path=os.path.join(base_dir, "csvs", folder, f"{prefix}_expenses.csv"),
            income_path=os.path.join(base_dir, "csvs", folder, f"{prefix}_income.csv"),
            stocks_path=os.path.join(base_dir, "csvs", folder, f"{prefix}_stocks.csv"),
            report_path=os.path.join(base_dir, "reports", f"{prefix}_financial_analysis.md")
        )
        accounts_dict[display_name] = account

    return accounts_dict

# CSV type configuration
CSV_TYPES = ["bank_statement", "expenses", "income", "stocks"]
CSV_TYPE_TO_PATH_ATTR = {
    "bank_statement": "bank_statement_path",
    "expenses": "expenses_path",
    "income": "income_path",
    "stocks": "stocks_path"
}

def get_csv_path(account_name: str, csv_type: str) -> str:
    """Get the file path for a specific CSV type."""
    account = accounts.get(account_name)
    if not account:
        return ""
    path_attr = CSV_TYPE_TO_PATH_ATTR.get(csv_type)
    return getattr(account, path_attr, "") if path_attr else ""

def load_csv_data(account_name: str, csv_type: str) -> pd.DataFrame:
    """Load specific CSV data for an account."""
    path = get_csv_path(account_name, csv_type)
    if not path or not os.path.exists(path):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception as e:
        return pd.DataFrame()

def send_chat(user_message: str, history: list[dict], account_name: str, session_chat_histories: dict):
    user_message = (user_message or "").strip()
    if not user_message:
        return history, session_chat_histories, ""

    result = agent.invoke_agent(account_name, user_message)
    response = result["messages"][-1].content

    updated_history = (history or []) + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response},
    ]

    # Store chat history per account in session state
    if session_chat_histories is None:
        session_chat_histories = {}
    session_chat_histories[account_name] = updated_history

    enable_dropdown = gr.update(interactive=True)
    enable_button = gr.update(interactive=True)
    enable_input = gr.update(interactive=True, value="")

    return updated_history, session_chat_histories, enable_dropdown, enable_button, enable_input

custom_css = """
#transactions_section, #select_section, #chat_box {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;
}

#transactions_section, #select_section {
    display: flex !important;
    flex-direction: column !important;
    min-height: 500px !important;
}

#select_section {
    justify-content: flex-end !important;
}

#csv_selectors {
    display: flex;
    flex-direction: column;
}

#transactions_df {
    overflow: auto;
    max-width: 100%;
    min-height: 500px !important;
}

#transactions_df table {
    font-size: 14px;
    table-layout: auto;
}

#transactions_df th:nth-child(2), #transactions_df td:nth-child(2) {
    max-width: 220px;
    white-space: normal;
    overflow: hidden;
}

#transactions_df .label-wrap {
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: unset !important;
}
"""

accounts = init_accounts()
default_account = next(iter(accounts.keys()), None) if accounts else None

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("# Finance Dashboard")

    with gr.Row(equal_height=True):
        with gr.Column(scale=7, min_width=480, elem_id="transactions_section"):
            gr.Markdown("## Transaction Details")
            transactions_df = gr.Dataframe(
                value=None,
                interactive=True,
                row_count=(1, 'dynamic'),
                col_count=None,
                datatype="auto",
                wrap=False,
                line_breaks=False,
                show_fullscreen_button=True,
                show_search="search",
                elem_id="transactions_df",
                label=""
            )

        with gr.Column(scale=3, min_width=320, elem_id="select_section"):
            gr.Markdown("## Dashboard Settings")

            with gr.Column(elem_id="account_dropdown"):
                gr.Markdown("**Select Account**")
                account_dropdown = gr.Dropdown(
                    choices=list(accounts.keys()),
                    value=default_account,
                    allow_custom_value=False,
                    label="Account",
                    filterable=False
                )

            with gr.Column(elem_id="csv_selectors"):
                gr.Markdown("**Select CSV File**")
                with gr.Column():
                    bank_statement_btn = gr.Button("Bank Statement", variant="secondary")
                    expenses_btn = gr.Button("Expenses", variant="secondary")
                    income_btn = gr.Button("Income", variant="secondary")
                    stocks_btn = gr.Button("Stocks", variant="secondary")

            with gr.Column(elem_id="quick_actions"):
                gr.Markdown("**Quick Actions**")
                refresh_btn = gr.Button("🔄 Refresh Data", variant="primary")
                download_btn = gr.DownloadButton("📥 Download CSV", variant="primary")



    with gr.Row():
        with gr.Column():
            with gr.Group(elem_id="chat_box"):
                chat_history = gr.Chatbot(label="Chat with a Financial Agent", type="messages")
                with gr.Row(equal_height=True):
                    user_input = gr.Textbox(
                        show_label=False,
                        placeholder="Type a message and press Send…",
                        lines=1,
                        scale=8,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

    # Session state for storing chat histories per user session
    session_chat_histories = gr.State(value={})

    # Generic CSV loader
    def load_csv_type(csv_type: str, account_name: str):
        """Generic function to load any CSV type and update UI accordingly."""
        global current_csv_type
        current_csv_type = csv_type
        account_name = account_name or default_account
        file_path = get_csv_path(account_name, csv_type)

        # Generate button variants (active button gets "primary", others get "secondary")
        button_variants = [
            gr.Button(variant="primary" if t == csv_type else "secondary")
            for t in CSV_TYPES
        ]

        return (
            load_csv_data(account_name, csv_type),
            *button_variants,
            gr.DownloadButton("📥 Download CSV", value=file_path, variant="primary")
        )

    def refresh_data(account_name):
        """Refresh the currently displayed CSV"""
        global current_csv_type
        account_name = account_name or default_account
        return load_csv_data(account_name, current_csv_type)



    # Wire CSV button clicks - each button uses the same generic function with different csv_type
    csv_buttons = [bank_statement_btn, expenses_btn, income_btn, stocks_btn]
    for csv_type, button in zip(CSV_TYPES, csv_buttons):
        button.click(
            fn=lambda account_name, ct=csv_type: load_csv_type(ct, account_name),
            inputs=[account_dropdown],
            outputs=[transactions_df, bank_statement_btn, expenses_btn, income_btn, stocks_btn, download_btn]
        )

    # Wire quick action buttons
    refresh_btn.click(
        fn=refresh_data,
        inputs=[account_dropdown],
        outputs=[transactions_df]
    )

    # When account changes, load that person's default CSV (Bank Statement)
    def on_account_change(account_name: str, session_chat_histories: dict):
        # Load chat history from session state for this account
        if session_chat_histories is None:
            session_chat_histories = {}
        chat_hist = session_chat_histories.get(account_name, [])
        csv_outputs = load_csv_type("bank_statement", account_name)
        return [*csv_outputs, chat_hist]

    account_dropdown.change(
        fn=on_account_change,
        inputs=[account_dropdown, session_chat_histories],
        outputs=[transactions_df, bank_statement_btn, expenses_btn, income_btn, stocks_btn, download_btn, chat_history],
    )

    def init():
        if default_account:
            return load_csv_type("bank_statement", default_account)
        else:
            return (
                pd.DataFrame(), 
                *[gr.Button(variant="secondary") for _ in CSV_TYPES],
                gr.DownloadButton("📥 Download CSV", variant="primary")
            )

    # Initialize with default account and Bank Statement CSV
    demo.load(
        fn=init,
        outputs=[transactions_df, bank_statement_btn, expenses_btn, income_btn, stocks_btn, download_btn]
    )

    # Chat
    send_btn.click(
        fn=send_chat,
        inputs=[user_input, chat_history, account_dropdown, session_chat_histories],
        outputs=[chat_history, session_chat_histories, account_dropdown, send_btn, user_input]
    )

    user_input.submit(
        fn=send_chat,
        inputs=[user_input, chat_history, account_dropdown, session_chat_histories],
        outputs=[chat_history, session_chat_histories, account_dropdown, send_btn, user_input]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")