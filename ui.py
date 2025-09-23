import os
from typing import Dict, Tuple, List
import gradio as gr
import pandas as pd
from pydantic import BaseModel

class Account(BaseModel):
    name: str
    bank_statement_path: str
    expense_path: str
    income_path: str
    stocks_path: str

# Global storage for accounts
accounts: Dict[str, Account] = {}

def init_accounts() -> Dict[str, Account]:
    """Initialize default accounts."""
    base_dir = os.path.join(os.path.dirname(__file__), "csvs")
    
    middle_class_account = Account(
        name="Middle Class Person",
        bank_statement_path=os.path.join(base_dir, "middle", "middle_class_person_bank_statement.csv"),
        expense_path=os.path.join(base_dir, "middle", "middle_class_person_expense.csv"),
        income_path=os.path.join(base_dir, "middle", "middle_class_person_income.csv"),
        stocks_path=os.path.join(base_dir, "middle", "middle_class_person_stocks.csv")
    )

    struggling_account = Account(
        name="Struggling Person",
        bank_statement_path=os.path.join(base_dir, "low", "struggling_person_bank_statement.csv"),
        expense_path=os.path.join(base_dir, "low", "struggling_person_expense.csv"),
        income_path=os.path.join(base_dir, "low", "struggling_person_income.csv"),
        stocks_path=os.path.join(base_dir, "low", "struggling_person_stocks.csv")
    )

    wealthy_account = Account(
        name="Wealthy Person",
        bank_statement_path=os.path.join(base_dir, "high", "wealthy_person_bank_statement.csv"),
        expense_path=os.path.join(base_dir, "high", "wealthy_person_expense.csv"),
        income_path=os.path.join(base_dir, "high", "wealthy_person_income.csv"),
        stocks_path=os.path.join(base_dir, "high", "wealthy_person_stocks.csv")
    )
    
    return {
        "Middle Income Person": middle_class_account,
        "High Income Person": wealthy_account,
        "Low Income Person": struggling_account
        }

def load_csv_data(account_name: str, csv_type: str) -> pd.DataFrame:
    """Load specific CSV data for an account."""
    account = accounts.get(account_name)
    if not account:
        return pd.DataFrame()
    
    # Get the appropriate CSV path based on type
    path_mapping = {
        "Bank Statement": account.bank_statement_path,
        "Expenses": account.expense_path,
        "Income": account.income_path,
        "Stocks": account.stocks_path
    }
    
    path = path_mapping.get(csv_type, "")
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        return pd.DataFrame()

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
#account_section, #select_section, #chat_box {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;
}

#select_section {
    height: 100%;
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

#transactions_df {
    overflow: auto;
    max-width: 100%;
}
"""

accounts = init_accounts()
default_account = next(iter(accounts.keys()), None) if accounts else None

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("# Finance Dashboard")

    with gr.Row(equal_height=True):
        with gr.Column(scale=7, min_width=480, elem_id="account_section"):
            gr.Markdown("**Account Transactions**")
            transactions_df = gr.Dataframe(
                value=None,
                interactive=True,
                wrap=False,
                line_breaks=False,
                show_fullscreen_button=True,
                show_search="search",
                elem_id="transactions_df",
                label=""
            )

        with gr.Column(scale=3, min_width=320, elem_id="select_section"):
            gr.Markdown("**Select Account**")
            account_dropdown = gr.Dropdown(
                choices=list(accounts.keys()),
                value=default_account,
                allow_custom_value=False,
                label="Account",
                elem_id="account_dropdown",
                filterable=False
            )

            gr.Markdown("**Select CSV File**")
            with gr.Column(elem_id="csv_selectors"):
                bank_statement_btn = gr.Button("Bank Statement", variant="secondary")
                expenses_btn = gr.Button("Expenses", variant="secondary")
                income_btn = gr.Button("Income", variant="secondary")
                stocks_btn = gr.Button("Stocks", variant="secondary")



    with gr.Row():
        with gr.Column():
            with gr.Group(elem_id="chat_box"):
                gr.Markdown("**Assistant**")
                chat_history = gr.Chatbot(label="Agent Chat", type="messages")
                with gr.Row(equal_height=True):
                    user_input = gr.Textbox(
                        show_label=False,
                        placeholder="Type a message and press Send…",
                        lines=1,
                        scale=8,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

    # CSV button click handlers
    def load_bank_statement(account_name):
        account_name = account_name or default_account
        return load_csv_data(account_name, "Bank Statement")
    
    def load_expenses(account_name):
        account_name = account_name or default_account
        return load_csv_data(account_name, "Expenses")
    
    def load_income(account_name):
        account_name = account_name or default_account
        return load_csv_data(account_name, "Income")
    
    def load_stocks(account_name):
        account_name = account_name or default_account
        return load_csv_data(account_name, "Stocks")

    # Wire CSV button clicks
    bank_statement_btn.click(
        fn=load_bank_statement,
        inputs=[account_dropdown],
        outputs=[transactions_df]
    )
    
    expenses_btn.click(
        fn=load_expenses,
        inputs=[account_dropdown],
        outputs=[transactions_df]
    )
    
    income_btn.click(
        fn=load_income,
        inputs=[account_dropdown],
        outputs=[transactions_df]
    )
    
    stocks_btn.click(
        fn=load_stocks,
        inputs=[account_dropdown],
        outputs=[transactions_df]
    )

    # When account changes, load that person's default CSV (Bank Statement)
    def on_account_change(account_name: str):
        return load_csv_data(account_name, "Bank Statement")

    account_dropdown.change(
        fn=on_account_change,
        inputs=[account_dropdown],
        outputs=[transactions_df],
    )

    # Initialize with default account and Bank Statement CSV
    demo.load(
        fn=lambda: load_csv_data(default_account, "Bank Statement") if default_account else pd.DataFrame(),
        outputs=[transactions_df],
    )

    # Chat
    send_btn.click(fn=send_chat, inputs=[user_input, chat_history],
                    outputs=[chat_history, user_input])
    user_input.submit(fn=send_chat, inputs=[user_input, chat_history],
                        outputs=[chat_history, user_input])

if __name__ == "__main__":
    demo.launch()
