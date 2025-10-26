import json
import time
from datetime import datetime, timezone
from typing import Dict, Any
import requests
import os
from dotenv import load_dotenv



load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

def sanitize_input(text: str) -> str:
    """Basic text cleanup: normalize whitespace."""
    return ' '.join(text.split())

def create_llm_prompt(text: str) -> str:
    """
    Create a detailed prompt for Groq API to analyze grammar and tone.
    Focus on ONLY heavy errors and problematic tone issues.
    """
    prompt = f"""You are a professional legal document editor. Analyze the following text for ONLY CRITICAL issues:

TEXT TO ANALYZE:
{text}

INSTRUCTIONS:
1. **Grammar & Spelling Analysis** - ONLY flag if sentence has 2+ of these SEVERE errors:
   - Subject-verb disagreement (e.g., "They was" → "They were")
   - Double negatives (e.g., "don't have no" → "don't have any")
   - Completely broken sentence structure (missing subject or verb)
   - Severe spelling mistakes that change meaning
   
   DO NOT FLAG:
   - Minor punctuation issues (commas, quotation marks)
   - Slight awkwardness or style preferences,complex sentences
      
2. **Tone & Plain Language Analysis** - ONLY flag if sentence contains:
   - Harsh/aggressive language (e.g., "shut up", "idiot", directly insulting)
   - Extreme informal language in formal context (e.g., "ain't", "gonna", "y'all" in legal docs)
   - Excessive jargon (3+ complex legal terms in one sentence that obscure meaning)
   
   DO NOT FLAG:
   - Professional legal terminology (proper use of "pursuant", "aforementioned")
   - Normal formal vs informal balance,Descriptive language 
   

3. **Quality Threshold**:
   - Grammar: Only flag if error makes sentence UNREADABLE or CONFUSING
   - Tone: Only flag if CLEARLY inappropriate for professional setting
   
OUTPUT FORMAT (JSON):
Return ONLY a valid JSON object with this exact structure:
{{
  "grammar_errors": [
    {{
      "sentence_index":sentence_number_starting_at_0,
      "error_type": "grammar",
      "original_sentence": "exact sentence with error",
      "corrected_sentence": "corrected version",
      
    }}
  ],
  "tone_errors": [
    {{
      "sentence_index":sentence_number_starting_at_0,
      "error_type": "tone_analysis",
      "original_sentence": "exact sentence with tone issue",
      "corrected_sentence": "improved version",
      "tone_category": "harsh|jargon|informal"
    }}
  ]
}}

CRITICAL RULES:( VERY conservative - prioritize only issues no need of enhancement)
- If NO critical grammar errors exist, return "grammar_errors": []
- If NO critical tone issues exist, return "tone_errors": []
- Return ONLY the JSON object, no markdown or explanations
"""
    return prompt

def call_groq_api(prompt: str) -> Dict[str, Any]:
    """
    Call Groq API with the analysis prompt.
    Returns parsed JSON response.
    """
    # Ensure API key is present
    if not GROQ_API_KEY:
        return {"grammar_errors": [], "tone_errors": [], "api_error": "GROQ_API_KEY is not set. Create a .env file or set the GROQ_API_KEY environment variable. See .env.example."}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are a conservative legal document quality analyzer. Only flag critical errors. Return valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.2, 
        "max_tokens": 3000, 
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract content from Groq response
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from content (handle markdown code blocks if present)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            parsed = json.loads(content)
            
            # Ensure required keys exist
            if "grammar_errors" not in parsed:
                parsed["grammar_errors"] = []
            if "tone_errors" not in parsed:
                parsed["tone_errors"] = []
            
            # Limit to top 5 errors total
            total_errors = len(parsed["grammar_errors"]) + len(parsed["tone_errors"])
            if total_errors > 5:
                parsed["grammar_errors"] = parsed["grammar_errors"][:3]
                parsed["tone_errors"] = parsed["tone_errors"][:2]
                
            return parsed
        else:
            return {"grammar_errors": [], "tone_errors": [], "api_error": "No response from Groq"}
            
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg = f"{error_msg} | Details: {json.dumps(error_detail)}"
            except:
                error_msg = f"{error_msg} | Response: {e.response.text[:200]}"
        return {"grammar_errors": [], "tone_errors": [], "api_error": f"API request failed: {error_msg}"}
    except json.JSONDecodeError as e:
        return {"grammar_errors": [], "tone_errors": [], "api_error": f"JSON parse error: {str(e)}"}
    except Exception as e:
        return {"grammar_errors": [], "tone_errors": [], "api_error": f"Unexpected error: {str(e)}"}

def process_grammar_and_tone(text: str) -> Dict[str, Any]:
    """
    Main entrypoint for backend integration.
    Input: Raw text (str) - typically 1-2 paragraphs.
    Output: JSON-serializable dict matching schema.
    Usage: output = process_grammar_and_tone("Your text here")
    """
    start_time = time.time()
    
    # Sanitize input
    clean_text = sanitize_input(text)
    
    # Create prompt and call Groq API
    prompt = create_llm_prompt(clean_text)
    groq_response = call_groq_api(prompt)
    
    # Extract results
    grammar_errors = groq_response.get("grammar_errors", [])
    tone_errors = groq_response.get("tone_errors", [])
    api_error = groq_response.get("api_error", None)
    
    # Determine violation status
    violation_status = "Compliant"
    if len(grammar_errors) > 0 or len(tone_errors) > 0:
        violation_status = "Violation"
    
    # Build rules triggered list
    rules_triggered = []
    if len(grammar_errors) > 0:
        rules_triggered.append("WQ003_GRAMMAR")
    if len(tone_errors) > 0:
        rules_triggered.append("WQ003_TONE")
    
    processing_time = round(time.time() - start_time, 4)
    
    output = {
        "tool_id": "TOOL_003",
        "violation_status": violation_status,
        "grammar_errors": grammar_errors,
        "tone_errors": tone_errors,
        "total_grammar_issues": len(grammar_errors),
        "total_tone_issues": len(tone_errors),
        "rules_triggered": rules_triggered if rules_triggered else ["WQ003"],
        "processing_time": f"{processing_time}s",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    if api_error:
        output["api_error"] = api_error
    
    return output

if __name__ == "__main__":
    print("="*70)
    print("Groq API Grammar & Tone Analysis Tool (Conservative Mode)")
    print("Model: llama-3.3-70b-versatile")
    print("="*70 + "\n")
    
    
    sample_text = """
    The legal team was preparing for trial, reviewing all evidences submitted by both parties. However, the plaintiff don't have no solid proof to support their allegations, which makes the case weak. You guys are wasting everyone's time with this nonsense, said the defense attorney in a loud voice. The statutory framework pursuant to the aforementioned jurisprudential precedents necessitate a reevaluation of procedural compliance. It was raining hard outside, and the mood in the courtroom was tense. The judge, clearly annoyed, told them to shut up and get to the point. This ain't how we do things in a court of law, he added. The defendant's counsel presented a comprehensive paradigmatic analysis of the evidentiary substrata, which, frankly, sounded like a bunch of copied legalese. They was confident in their argument, despite the lack of clarity. Meanwhile, the jury looked confused, unsure what to make of the technical jargon being thrown around. The plaintiff's lawyer tried to rebut, but their sentence structure was broken and hard to follow. "We is here to prove our case," they said, stumbling. Overall, the courtroom felt more like a chaotic debate club than a professional legal proceeding.
    """
    
    print("Test 1: Text with critical errors")
    print("-"*70)
    output = process_grammar_and_tone(sample_text)
    print(json.dumps(output, indent=2))
    
   
   