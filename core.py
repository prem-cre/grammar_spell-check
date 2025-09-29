"""
Core NLP Grammar and Spelling Checking Logic
"""

import re
from typing import List, Tuple, Optional
from symspellpy import SymSpell, Verbosity
import language_tool_python
import spacy
from spacy.lang.en import English

class TextSegmenter:
    """Handles text segmentation"""
    
    def __init__(self, nlp_model=None):
        self.nlp_model = nlp_model
    
    def segment_text(self, text: str) -> List[str]:
        text = text.strip()
        if not text:
            return []
            
        if self.nlp_model:
            try:
                doc = self.nlp_model(text)
                sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
                return sentences if sentences else [text]
            except:
                pass
        
        return self._fallback_segmentation(text)
    
    def _fallback_segmentation(self, text: str) -> List[str]:
        abbrev_pattern = r'\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|Inc|Corp|Ltd|Co|vs|etc|i\.e|e\.g|U\.S|et\.al|cf|ibid|op\.cit|supra|infra|Art|Sec|Para|Ch|Vol|No|P\.L|U\.S\.C|C\.F\.R)\.'
        protected_text = re.sub(abbrev_pattern, lambda m: m.group().replace('.', '<!DOT!>'), text, flags=re.IGNORECASE)
        sentences = re.split(r'[.!?]+(?:\s+|$)', protected_text)
        sentences = [sent.replace('<!DOT!>', '.').strip() for sent in sentences if sent.strip()]
        return sentences if sentences else [text]

class GrammarChecker:
    """Grammar checking using LanguageTool"""
    
    def __init__(self, language_tool: language_tool_python.LanguageTool):
        self.language_tool = language_tool
    
    def check_grammar(self, text: str) -> Tuple[str, bool, Optional[str]]:
        try:
            matches = self.language_tool.check(text)
            corrected = language_tool_python.utils.correct(text, matches)
            has_changes = text.strip() != corrected.strip()
            return corrected, has_changes, None
        except Exception as e:
            return text, False, str(e)

class EnhancedGrammarChecker(GrammarChecker):
    """Enhanced grammar checker with additional rules"""
    
    def __init__(self, language_tool: language_tool_python.LanguageTool, nlp=None):
        super().__init__(language_tool)
        self.nlp = nlp
        
    def check_grammar(self, text: str) -> Tuple[str, bool, Optional[str]]:
        corrected, has_changes, error_msg = super().check_grammar(text)
        further_corrected = self._apply_additional_rules(corrected)
        
        if further_corrected != corrected:
            return further_corrected, True, error_msg
        
        return corrected, has_changes, error_msg
    
    def _apply_additional_rules(self, text: str) -> str:
        # Fix inverted question word order
        question_pattern = r'^(What|Where|When|Who|Which)\s+(\w+)\s+(is|are|was|were)\s+(\w+)\?$'
        match = re.match(question_pattern, text, re.IGNORECASE)
        
        if match:
            q_word, noun1, verb, noun2 = match.groups()
            return f"{q_word} {verb} the {noun2} of {noun1}?"
        
        words = text.split()
        if len(words) >= 4 and words[0].lower() in ['what', 'where', 'when', 'who', 'which']:
            if words[2].lower() in ['is', 'are', 'was', 'were'] and text.rstrip().endswith('?'):
                last_word = words[-1].rstrip('?')
                return f"{words[0]} {words[2]} the {last_word} of {words[1]}?"
        
        return text

class SpellChecker:
    """Spell checking using SymSpell"""
    
    def __init__(self, sym_spell: SymSpell, max_edit_distance: int = 2):
        self.sym_spell = sym_spell
        self.max_edit_distance = max_edit_distance
    
    def get_suggestions(self, word: str, max_suggestions: int = 3, verbosity: Verbosity = Verbosity.ALL) -> List[str]:
        try:
            suggestions = self.sym_spell.lookup(
                word, 
                verbosity,
                max_edit_distance=self.max_edit_distance,
                include_unknown=False
            )
            
            suggestion_terms = []
            seen = set()
            
            for suggestion in suggestions:
                if suggestion.term not in seen and suggestion.term.lower() != word.lower():
                    suggestion_terms.append(suggestion.term)
                    seen.add(suggestion.term)
                    
                    if len(suggestion_terms) >= max_suggestions:
                        break
            
            return suggestion_terms
        except:
            return []

# Usage example:
if __name__ == "__main__":
    # Initialize SpaCy
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        nlp = English()
    
    # Initialize SymSpell
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    # Load dictionary (you need to provide the path)
    # sym_spell.load_dictionary("path/to/dictionary.txt", 0, 1)
    
    # Initialize LanguageTool
    language_tool = language_tool_python.LanguageTool('en-US')
    
    # Create instances
    segmenter = TextSegmenter(nlp)
    spell_checker = SpellChecker(sym_spell)
    grammar_checker = EnhancedGrammarChecker(language_tool, nlp)
    
    # Example usage
    text = "What France is capital?"
    corrected, has_changes, error = grammar_checker.check_grammar(text)
    print(f"Original: {text}")
    print(f"Corrected: {corrected}")
    
    word = "teh"
    suggestions = spell_checker.get_suggestions(word)
    print(f"Suggestions for '{word}': {suggestions}")
    
    # Clean up
    language_tool.close()
