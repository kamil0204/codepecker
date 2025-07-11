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


def generate_codebase_review_plan(text_tree, project_path):
    """Generate a codebase review plan using LLM"""
    client = initialize_llm_client()
    if not client:
        return None
    
    prompt = f"""You are a senior software architect and code reviewer. I need you to analyze the following project structure and create a comprehensive codebase review plan.

Project Path: {project_path}
Project Structure:
{text_tree}

Based on this structure, please provide:

1. **Project Overview**: 
   - Identify the technology stack and frameworks being used
   - Determine the project type and architecture pattern
   - Identify key components and their relationships

2. **Review Priorities** (in order of importance):
   - Critical files that should be reviewed first
   - Core business logic components
   - Configuration and setup files
   - Test coverage areas

3. **Architecture Analysis**:
   - Identify potential architectural concerns
   - Suggest areas that might need refactoring
   - Point out missing components or patterns

4. **Review Checklist**:
   - Security considerations to review
   - Performance optimization opportunities
   - Code quality and maintainability aspects
   - Documentation and testing gaps

5. **Recommended Review Order**:
   - Step-by-step plan for reviewing the codebase
   - Estimated time for each component
   - Dependencies between components

Please provide a structured, actionable plan that a development team can follow to conduct a thorough code review of this project."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert software architect and code reviewer with deep knowledge of software engineering best practices, security, and maintainability."
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
