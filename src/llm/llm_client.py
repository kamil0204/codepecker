"""
LLM client for generating codebase review plans
"""
import os
import httpx
import requests
import json
from openai import OpenAI


def get_bearer_token():
    """Get bearer token using Client Credentials OAuth flow"""
    auth_url = os.getenv('APIGEE_AUTH_URL')
    client_id = os.getenv('APIGEE_CLIENT_ID')
    client_secret = os.getenv('APIGEE_CLIENT_SECRET')

    if not client_id or not client_secret:
        raise ValueError("Environment variables 'APIGEE_CLIENT_ID' and 'APIGEE_CLIENT_SECRET' must be set.")
    if not auth_url:
        raise ValueError("Environment variable 'APIGEE_AUTH_URL' must be set.")

    proxy_url = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
    proxies = {'https': proxy_url, 'http': proxy_url} if proxy_url else None
    
    post_params = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
    
    try:
        response = requests.post(
            auth_url, 
            data=post_params, 
            headers=headers,
            timeout=60.0,
            proxies=proxies,
            verify=False
        )
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            raise ValueError("No access_token found in response")
            
        return access_token
        
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to get bearer token: {str(e)}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse token response: {str(e)}")


def initialize_llm_client():
    """Initialize OpenAI client with Intel's internal API"""
    try:
        api_key = get_bearer_token()
    except Exception:
        return None
    
    proxy_url = os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
    
    http_client = httpx.Client(
        proxy=proxy_url,
        timeout=120.0,
        verify=False
    ) if proxy_url else None
    
    base_url = "https://apis-internal.intel.com/generativeaiinference/v4"
    
    client = OpenAI(
        api_key=api_key, 
        base_url=base_url,
        timeout=120.0,
        max_retries=3,
        http_client=http_client
    )
    
    return client


def generate_entrypoints_list(text_tree, project_path):
    """Generate a list of entry points in the codebase using LLM"""
    client = initialize_llm_client()
    if not client:
        return None
    
    prompt = f"""Analyze the following C# project structure and identify ALL entry points in the codebase.

Project Path: {project_path}
Project Structure:
{text_tree}

Return ONLY a JSON array with the following structure. Do not include any additional text, explanations, or formatting outside of the JSON:

[
  {{
    "entrypoint": "entry point name",
    "file": "relative/path/to/file.cs",
    "type": "entry point type",
    "trigger": "how this entry point gets triggered"
  }}
]

Entry point types to look for:
- Main method (Program.cs)
- Controller actions (HTTP endpoints)
- Background services/hosted services
- Event handlers
- Scheduled jobs/tasks
- Message queue consumers
- Database triggers/stored procedures
- Startup/configuration methods

The trigger description must be one line maximum and describe how the entry point is invoked."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a C# code analyzer. Return only valid JSON arrays without any additional text, explanations, or markdown formatting."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=4000,
            stream=False
        )
        
        return response.choices[0].message.content
        
    except Exception:
        return None
