import re, json

def extract_last_json(text):
    # re.findall finds every instance of { ... }
    # [^}]* ensures we don't accidentally skip over nested structures
    matches = re.findall(r'(\{.*?\})', text, re.DOTALL)
    
    if not matches:
        return None
    
    # We take the last match [-1]
    last_json_str = matches[-1]
    
    try:
        # Replace single quotes with double quotes for valid JSON
        # (LLMs often use ' which is valid Python but invalid JSON)
        valid_json_str = last_json_str.replace("'", '"')
        data = json.loads(valid_json_str)
        return data.get("final_answer")
    except json.JSONDecodeError:
        return None