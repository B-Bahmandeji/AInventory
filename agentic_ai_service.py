# pip install -r requirements.txt
# agentic_ai_test.py
#service is autorized to read data from google file
import os
import datetime
import pandas as pd
from openai import OpenAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from googleapiclient.discovery import build
from google.oauth2 import service_account
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv() # Obtaining over secret keys

# ---- CONFIG (via env or change for quick testing) ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")
GOOGLE_SERVICE_ACCOUNT_FILE = "service-account.json"

client = OpenAI(api_key=OPENAI_API_KEY)

def email_test():
    subject = "Inventory Shortage Alert"
    body = f"Agentic AI detected potential shortages:\n\n"
    sent = send_email_notification(subject, body)
    print(f"[node] notify -> email sent: {sent}")



# ---- Helper: read inventory (Google Sheets) ----
def read_inventory_df():
    """
    Returns a pandas DataFrame. If Google creds are missing, returns fake sample data
    so you can test right away.
    """
    if not GOOGLE_SERVICE_ACCOUNT_FILE or not SPREADSHEET_ID:
        # Fake sample — helpful for immediate testing
        sample = [
            {"date": datetime.date.today().isoformat(), "item": "Apple", "stock": 120},
            {"date": datetime.date.today().isoformat(), "item": "Banana", "stock": 20},
            {"date": (datetime.date.today() - datetime.timedelta(days=1)).isoformat(), "item": "Pear", "stock": 45},
        ]
        return pd.DataFrame(sample)
    
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )

    #print("Google try...")
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1").execute()
    values = result.get("values", [])
    if not values:
        return pd.DataFrame()
    df = pd.DataFrame(values[1:], columns=values[0])

    # try to coerce types
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce").dt.date
    if "stock" in df.columns:
        df["stock"] = pd.to_numeric(df["stock"], errors="coerce")

    return df

# ---- Email helper ----
def send_email_notification(subject: str, body: str):
    if not (EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER):
        print("Email config missing; skipping email send.")
        return False
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
    return True

# ---- LangGraph State ----
class State(TypedDict, total=False):
    # We'll carry small JSON-serializable structures through the graph
    records: list
    new_records: list
    prediction: str
    alert: bool
    notified: bool

# ---- Nodes ----
def read_inventory_node(state: State) -> dict:
    df = read_inventory_df()
    # convert date column to ISO strings for portability
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce").dt.date

    records = df.to_dict(orient="records")
    #print(f"[node] read_inventory -> {len(records)} records")
    return {"records": records}

def filter_new_records_node(state: State) -> dict:
    records = state.get("records", [])
    today = datetime.date.today()
    new_records = []
    for r in records:
        d = r.get("date")

        #print("DATE="+d)###

        if not d:
            continue
        try:
            date_obj = pd.to_datetime(d).date()
        except Exception:
            continue
        if date_obj == today:
            new_records.append(r)
    print(f"[node] filter_new_records -> {len(new_records)} new records for {today.isoformat()}")
    return {"new_records": new_records}

def predict_shortage_node(state: State) -> dict:
    new_records = state.get("new_records", [])
    if not new_records:
        return {"prediction": "No new records today.", "alert": False}

    prompt = (
        "You are an AI inventory analyst. Given these inventory records (date, item name, stock quantity, sales), "
        "predict if any item is likely to run out within the next 30 days. For each at-risk item, "
        "give an estimated date (or days until shortage) and a short reason.\n\n"
        f"Records: {new_records}\n\n"
        "Return a concise list and be explicit if no shortages are expected."
    )

    if not OPENAI_API_KEY:
        # safe fallback for testing without API key
        fake_prediction = "FAKE: Prediction skipped because OPENAI_API_KEY not set. If you set the key, the model will analyze and return shortages."
        print("[node] predict_shortage -> OPENAI_API_KEY not set, returning fake prediction.")
        return {"prediction": fake_prediction, "alert": False}

    try:
        # Call the chat completion API
        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # or "gpt-4o", "gpt-3.5-turbo", etc.
            messages=[
                {"role": "system", "content": "You are an expert inventory analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600,
        )
        prediction = resp.choices[0].message.content
    except Exception as e:
        prediction = f"OpenAI call failed: {e}"
        print("[node] predict_shortage -> OpenAI error:", e)
        return {"prediction": prediction, "alert": False}

    # simple heuristic: mark alert True if the assistant mentions 'shortage' or 'run out' etc.
    lowered = prediction.lower()
    alert = any(k in lowered for k in ["shortage", "run out", "out of stock", "will be out", "low stock", "deplete"])
    print(f"[node] predict_shortage -> alert={alert}")
    return {"prediction": prediction, "alert": alert}

def notify_node(state: State) -> dict:
    alert = state.get("alert", False)
    prediction = state.get("prediction", "")
    if not alert:
        print("[node] notify -> no alert, skipping email.")
        return {"notified": False}
    subject = "Inventory Shortage Alert"
    body = f"Agentic AI detected potential shortages:\n\n{prediction}"
    sent = send_email_notification(subject, body)
    print(f"[node] notify -> email sent: {sent}")
    return {"notified": sent}

# ---- Build & compile the StateGraph (correct LangGraph flow) ----
def build_graph():
    builder = StateGraph(State)
    # add nodes (LangGraph uses the function's __name__ as the node name by default)
    builder.add_node(read_inventory_node)
    builder.add_node(filter_new_records_node)
    builder.add_node(predict_shortage_node)
    builder.add_node(notify_node)
    # wire edges (START -> read -> filter -> predict -> notify)
    builder.add_edge(START, read_inventory_node.__name__)
    builder.add_edge(read_inventory_node.__name__, filter_new_records_node.__name__)
    builder.add_edge(filter_new_records_node.__name__, predict_shortage_node.__name__)
    builder.add_edge(predict_shortage_node.__name__, notify_node.__name__)
    graph = builder.compile()
    return graph

def run_agent_once_with_graph():
    graph = build_graph()
    # invoke the graph. We pass an empty input — graph will operate and return the full state.
    result = graph.invoke({})
    return result

# ---- For quick non-LangGraph testing ----
def run_agent_direct():
    # call the same logic without LangGraph orchestration
    df = read_inventory_df()
    print("Inventory (top rows):")
    print(df.head())
    # filter
    today = datetime.date.today()
    new_records = [r for r in df.to_dict(orient="records") if pd.to_datetime(r.get("date"), errors="coerce").date() == today]
    print("New records:", new_records)
    # predict
    node_out = predict_shortage_node({"new_records": new_records})
    print("Prediction:", node_out.get("prediction"))
    if node_out.get("alert"):
        send_email_notification("Inventory Shortage Alert", node_out.get("prediction"))

# ---- Run as script ----
if __name__ == "__main__":
    print("Invoking StateGraph once (this uses langgraph StateGraph + graph.invoke)...")
    try:
        result = run_agent_once_with_graph()
        print("Graph invocation result keys:", list(result.keys()))
        print("prediction preview:")
        print(result.get("prediction", "")[:1000])
    except Exception as e:
        print("Graph invocation failed:", e)
        print("Falling back to direct run for easier debugging.")
        run_agent_direct()
