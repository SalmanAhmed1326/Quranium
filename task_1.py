# app.py
import os
import re
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv
from openai import OpenAI
from web3 import Web3
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configuration
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
SEPOLIA_RPC_URL = os.getenv('SEPOLIA_RPC_URL', 'https://rpc.sepolia.org')

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))

def is_contract_address(address):
    return re.match(r'^0x[a-fA-F0-9]{40}$', address) and w3.is_address(address)

def get_contract_abi(address):
    try:
        url = f"https://api-sepolia.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(url)
        data = response.json()
        return data['result'] if data['status'] == '1' else None
    except Exception as e:
        print(f"Error fetching ABI: {e}")
        return None
def generate_solidity_code(description):
    prompt = f"""
    Generate secure Solidity code for: {description}
    
    Requirements:
    1. Use latest Solidity version with security features
    2. Include necessary access controls
    3. Follow best security practices
    4. Keep code minimal but functional
    
    Output format:
    CODE:
    ```solidity
    // Generated code here
    ```
    
    SECURITY:
    - Bullet points of security considerations
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a smart contract security expert."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def explain_contract(input_data):
    prompt = f"""
    Analyze this smart contract and provide a technical summary:
    
    1. Key functions and their purposes
    2. Permissions and access controls
    3. Security patterns used
    4. Potential risks
    
    Contract details:
    {input_data}
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a smart contract auditor."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/task1', methods=['POST'])
def task1():
    description = request.form['description']
    try:
        result = generate_solidity_code(description)
        code = result.split('CODE:')[1].split('SECURITY:')[0].strip()
        security = result.split('SECURITY:')[1].strip()
        return render_template('index.html', 
                             task1_code=code,
                             task1_security=security)
    except Exception as e:
        return render_template('index.html', task1_error=str(e))

@app.route('/task2', methods=['POST'])
def task2():
    input_data = request.form['contract_input']
    try:
        if is_contract_address(input_data):
            abi = get_contract_abi(input_data)
            if not abi:
                raise ValueError("Contract ABI not found or not verified")
            input_type = f"ABI for {input_data}"
        else:
            abi = input_data
            input_type = "Solidity code"
        
        explanation = explain_contract(abi)
        return render_template('index.html', 
                             task2_explanation=explanation,
                             input_type=input_type)
    except Exception as e:
        return render_template('index.html', task2_error=str(e))

if __name__ == '__main__':
    app.run(debug=True)