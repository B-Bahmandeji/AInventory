# Langchain Agnetic AI Service

This service can read data records from your Google Spreadsheet sales and send them to OpenAI to analyzed and figure out how much it will take for each item in inventory to be restock!
It can then sends an email to you and notify you about each item!
It is not a final product, just a start point to learn how you can use Landchain and the orchestrate states by Langgraph.
You need to add youur OpenAI key, Spreadsheet id, submit your service to google account and get a service-client.json file, get a password key from your gamil account to be able run ths project.

# Requirements
Python 3.7+
An OpenAI API key
A Google Service Client json file
A Gmail password for sending email, is different from your personal password!

# Installation
Before you begin, ensure you have Python installed on your system. Then clone this repository and navigate into the project directory.

# Clone the Repository
git clone https://github.com/B-Bahmandeji/AInventory
cd AInventory

# Install Dependencies
<pre> ```python pip install -r requirements.txt``` </pre>

    
Your requirements.txt file should contain the following:

pandas  
google-auth  
google-auth-oauthlib  
google-api-python-client  
openai  
langchain  
langgraph  
python-dotenv  
