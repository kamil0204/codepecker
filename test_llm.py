#!/usr/bin/env python3
"""
Test LLM client specifically
"""
import os
import sys

print("Testing LLM client imports...")

try:
    print("Importing individual modules...")
    import httpx
    print("✅ httpx imported")
    
    import requests
    print("✅ requests imported")
    
    import json
    print("✅ json imported")
    
    from openai import OpenAI
    print("✅ OpenAI imported")
    
    print("Now importing our LLM client...")
    from src.llm.llm_client import generate_entrypoints_list
    print("✅ generate_entrypoints_list imported")
    
    from src.llm.llm_client import review_csharp_methods
    print("✅ review_csharp_methods imported")
    
    print("LLM client test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
