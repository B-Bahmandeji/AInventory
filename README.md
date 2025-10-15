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
```python 
pip install -r requirements.txt
```



    
Your requirements.txt file should contain the following:

pandas  
google-auth  
google-auth-oauthlib  
google-api-python-client  
openai  
langchain  
langgraph  
python-dotenv  

# Share your Google Doc
To read Google Spreadsheet documents using OAuth 2.0 with a service account, you need to obtain and utilize a service account JSON key file.
Go to Google Cloud Console: https://console.cloud.google.com/  
# 1. Create a Service Account and Download the JSON Key:
From Google Cloud Console: Navigate to Menu > IAM & Admin > Service Accounts.  
Create Service Account: Click + CREATE SERVICE ACCOUNT. Provide a name and description, then click DONE.  
Create Key: Select your newly created service account, then go to Keys > ADD KEY > Create new key.  
Choose JSON: Select JSON as the key type and click Create. This will download a JSON file containing your service account credentials. Save this file securely, as it's the only copy of the private key.  
# 2. Share the Google Sheet with the Service Account:
Identify Service Account Email: The downloaded JSON file contains an client_email field. This is the email address of your service account.  
You can ask others to share their document with this email, if you upgrade the application to serve others!  
Share the Spreadsheet: Open the Google Sheet you want to access, click Share, and add the service account's email address with at least Editor permissions.  
This version serve just to you! So just get your Google Spreadsheet ID from doc share link.  
Right click on the Google doc and copy link like this: https://docs.google.com/spreadsheets/d/this-is-your-file-id/edit?usp=drive_link  
Get the part between d and edit like: this-is-your-file-id and use it as SPREADSHEET_ID inside your app.  
# 3. Enable the Google Sheets API:
Go to APIs & Services > Library: in the Google Cloud Console.  
Search for "Google Sheets API": and enable it for your project.  
