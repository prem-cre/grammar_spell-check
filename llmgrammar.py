import requests
import time
from typing import Dict, Any

class FastGrammarCorrector:
    """Fast OpenAI grammar corrector - simple and efficient"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # GPT-3.5-turbo is the fastest OpenAI model
        self.model = "gpt-3.5-turbo"
        
    def correct_text(self, text: str) -> Dict[str, Any]:
        """Correct grammar in text - returns corrected text with timing"""
        start_time = time.time()
        
        if not text.strip():
            return {
                "original": text,
                "corrected": text,
                "time_ms": 0,
                "success": True
            }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Fix only grammar, spelling, and punctuation errors. Keep the original sentence structure and meaning. Change only incorrect words, not the entire sentence."
                },
                {
                    "role": "user", 
                    "content": text
                }
            ],
            "temperature": 0,  # Zero for consistent corrections
            "max_tokens": len(text.split()) * 2,  # Enough for corrections
            "top_p": 0.1,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    corrected = data['choices'][0]['message']['content'].strip()
                    elapsed_ms = (time.time() - start_time) * 1000
                    
                    return {
                        "original": text,
                        "corrected": corrected,
                        "time_ms": elapsed_ms,
                        "success": True
                    }
                else:
                    return {
                        "original": text,
                        "corrected": text,
                        "time_ms": (time.time() - start_time) * 1000,
                        "success": False,
                        "error": "No response from API"
                    }
            else:
                return {
                    "original": text,
                    "corrected": text,
                    "time_ms": (time.time() - start_time) * 1000,
                    "success": False,
                    "error": f"API error {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "original": text,
                "corrected": text,
                "time_ms": (time.time() - start_time) * 1000,
                "success": False,
                "error": str(e)
            }
    
    def correct(self, text: str) -> str:
        """Simple correction - returns only corrected text"""
        result = self.correct_text(text)
        return result["corrected"]
    
    def test_connection(self) -> bool:
        """Test if OpenAI API is working"""
        test_result = self.correct_text("This are a test.")
        return test_result["success"] and test_result["corrected"] != "This are a test."


# Simple usage functions
def correct_grammar(text: str, api_key: str) -> str:
    """Simplest usage - just returns corrected text"""
    corrector = FastGrammarCorrector(api_key)
    return corrector.correct(text)


def correct_with_timing(text: str, api_key: str) -> Dict[str, Any]:
    """Returns corrected text with timing information"""
    corrector = FastGrammarCorrector(api_key)
    return corrector.correct_text(text)


# Demo and testing
def demo_corrections(api_key: str):
    """Demo various grammar corrections"""
    corrector = FastGrammarCorrector(api_key)
    
    test_sentences = [
        "Their are many reason why this dont work.",
        "She don't like the way he speak.",
        "The informations is incorrect.",
        "We was working on this project since morning.",
        "He have many ideas for improvement.",
        "The data are showing interesting pattern.",
        "They is going to the meeting tomorrow.",
        "The lawyer was preparing the case document which have many clause.",
        "He say that the evidences is strong.",
        "The party who signed it dont understand the implication."
    ]
    
    print("\n" + "="*70)
    print("GRAMMAR CORRECTION DEMO - OpenAI GPT-3.5-Turbo")
    print("="*70)
    
    total_time = 0
    corrections_made = 0
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n{i}. Original:  {sentence}")
        
        result = corrector.correct_text(sentence)
        
        if result["success"]:
            print(f"   Corrected: {result['corrected']}")
            print(f"   Time: {result['time_ms']:.0f}ms", end="")
            
            if result['time_ms'] < 300:
                print(" ⚡ FAST")
            elif result['time_ms'] < 600:
                print(" ✓ Good")
            else:
                print("")
            
            total_time += result['time_ms']
            if result['original'] != result['corrected']:
                corrections_made += 1
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    avg_time = total_time / len(test_sentences)
    print("\n" + "="*70)
    print(f"📊 SUMMARY:")
    print(f"   • Sentences processed: {len(test_sentences)}")
    print(f"   • Corrections made: {corrections_made}")
    print(f"   • Average time: {avg_time:.0f}ms")
    print(f"   • Total time: {total_time:.0f}ms")
    print("="*70)


if __name__ == "__main__":
    # Your OpenAI API key
    OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"  # Replace with your actual key
    
    print("🚀 FAST GRAMMAR CORRECTOR - OpenAI GPT-3.5-Turbo")
    print("="*70)
    
    # Initialize corrector
    corrector = FastGrammarCorrector(OPENAI_API_KEY)
    
    # Test connection
    print("\n🔍 Testing OpenAI API connection...")
    if corrector.test_connection():
        print("✅ OpenAI API is working!\n")
    else:
        print("❌ OpenAI API connection failed!")
        print("Please check your API key")
        print("Get your key from: https://platform.openai.com/api-keys")
        exit(1)
    
    # Example 1: Simple correction
    print("="*70)
    print("EXAMPLE 1: Simple Correction")
    print("="*70)
    
    text = "Their are many reason why this dont work properly."
    corrected = corrector.correct(text)
    print(f"Original:  {text}")
    print(f"Corrected: {corrected}")
    
    # Example 2: Correction with timing
    print("\n" + "="*70)
    print("EXAMPLE 2: Correction with Timing")
    print("="*70)
    
    text = "She don't understand why the system are not working."
    result = corrector.correct_text(text)
    print(f"Original:  {result['original']}")
    print(f"Corrected: {result['corrected']}")
    print(f"Time:      {result['time_ms']:.0f}ms")
    
    # Example 3: Simple one-liner usage
    print("\n" + "="*70)
    print("EXAMPLE 3: One-liner Usage")
    print("="*70)
    
    # Direct function call
    corrected = correct_grammar("He have many idea for the project.", OPENAI_API_KEY)
    print(f"Input:  He have many idea for the project.")
    print(f"Output: {corrected}")
    
    # Run full demo
    print("\n" + "="*70)
    print("RUNNING FULL DEMO")
    print("="*70)
    demo_corrections(OPENAI_API_KEY)
    
    # Usage instructions
    print("\n" + "="*70)
    print("📚 HOW TO USE")
    print("="*70)
    print("""
# Method 1: Create corrector instance
corrector = FastGrammarCorrector(api_key)
corrected_text = corrector.correct("Your text here")

# Method 2: Direct function (simplest)
corrected_text = correct_grammar("Your text here", api_key)

# Method 3: With timing information
result = correct_with_timing("Your text here", api_key)
print(f"Corrected: {result['corrected']}")
print(f"Time: {result['time_ms']}ms")
    """)
    
    print("\n✅ Ready to use!")