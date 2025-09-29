"""
FastAPI Grammar and Spelling Checking Service - Legal Domain Enhanced with WebSocket
A high-performance grammar and spelling checking API using SymSpell with legal dictionary support,
LanguageTool for grammar checking, and WebSocket for real-time assistance.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager
import time
import re
import json

from symspellpy import SymSpell, Verbosity
from importlib.resources import files, as_file
import spacy
import language_tool_python
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from spacy.lang.en import English

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time grammar and spelling assistance"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)

class TextSegmenter:
    """Handles text segmentation with fallback methods"""
    
    def __init__(self, nlp_model=None):
        self.nlp_model = nlp_model
        self.sentence_pattern = re.compile(r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*$', re.MULTILINE)
    
    def segment_text(self, text: str) -> List[str]:
        text = text.strip()
        if not text:
            return []
            
        if self.nlp_model:
            try:
                doc = self.nlp_model(text)
                sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
                return sentences if sentences else [text]
            except Exception as e:
                logger.warning(f"SpaCy segmentation failed: {e}, using fallback")
        
        return self._fallback_segmentation(text)
    
    def _fallback_segmentation(self, text: str) -> List[str]:
        abbrev_pattern = r'\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|Inc|Corp|Ltd|Co|vs|etc|i\.e|e\.g|U\.S|et\.al|cf|ibid|op\.cit|supra|infra|Art|Sec|Para|Ch|Vol|No|P\.L|U\.S\.C|C\.F\.R)\.'
        protected_text = re.sub(abbrev_pattern, lambda m: m.group().replace('.', '<!DOT!>'), text, flags=re.IGNORECASE)
        sentences = re.split(r'[.!?]+(?:\s+|$)', protected_text)
        sentences = [sent.replace('<!DOT!>', '.').strip() for sent in sentences if sent.strip()]
        return sentences if sentences else [text]

class GrammarChecker:
    """Handles grammar checking with better error handling"""
    
    def __init__(self, language_tool: language_tool_python.LanguageTool):
        self.language_tool = language_tool
    
    def check_grammar(self, text: str) -> Tuple[str, bool, Optional[str]]:
        try:
            matches = self.language_tool.check(text)
            corrected = language_tool_python.utils.correct(text, matches)
            has_changes = text.strip() != corrected.strip()
            return corrected, has_changes, None
        except Exception as e:
            error_msg = f"Grammar check failed: {str(e)}"
            logger.error(error_msg)
            return text, False, error_msg

class EnhancedGrammarChecker(GrammarChecker):
    """Enhanced grammar checker with additional rule-based corrections"""
    
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
        question_pattern = r'^(What|Where|When|Who|Which)\s+(\w+)\s+(is|are|was|were)\s+(\w+)\?$'
        match = re.match(question_pattern, text, re.IGNORECASE)
        
        if match:
            q_word, noun1, verb, noun2 = match.groups()
            corrected = f"{q_word} {verb} the {noun2} of {noun1}?"
            return corrected
        
        words = text.split()
        if len(words) >= 3:
            first_word_lower = words[0].lower()
            
            if first_word_lower in ['what', 'where', 'when', 'who', 'which']:
                if len(words) >= 4 and words[2].lower() in ['is', 'are', 'was', 'were']:
                    if text.rstrip().endswith('?'):
                        last_word = words[-1].rstrip('?')
                        corrected = f"{words[0]} {words[2]} the {last_word} of {words[1]}?"
                        return corrected
        
        return text

class SyntaxRestructurer:
    """Handles syntax restructuring for malformed sentences"""
    
    def __init__(self, nlp):
        self.nlp = nlp
        
    def restructure_question(self, text: str) -> str:
        doc = self.nlp(text)
        
        if self._is_malformed_question(doc):
            return self._fix_question_structure(doc, text)
        return text
    
    def _is_malformed_question(self, doc) -> bool:
        if not doc or len(doc) < 3:
            return False
            
        if doc[0].text.lower() in ['what', 'where', 'who', 'when', 'which']:
            for i, token in enumerate(doc[1:], 1):
                if token.pos_ == "VERB" and i > 1:
                    for j in range(1, i):
                        if doc[j].pos_ in ["NOUN", "PROPN"]:
                            return True
        return False
    
    def _fix_question_structure(self, doc, original_text: str) -> str:
        tokens = [token.text for token in doc]
        
        question_word = tokens[0] if tokens else ""
        verb = None
        subject = None
        object_noun = None
        
        for token in doc:
            if token.pos_ == "VERB" and not verb:
                verb = token.text
            elif token.pos_ in ["NOUN", "PROPN"]:
                if not subject and token.i < (doc[0].i + 3):
                    subject = token.text
                elif not object_noun:
                    object_noun = token.text
        
        if question_word and verb and subject and object_noun:
            if original_text.rstrip().endswith('?'):
                return f"{question_word} {verb} the {object_noun} of {subject}?"
        
        return original_text

class EnhancedSpellChecker:
    """Enhanced spell checker with legal dictionary support"""
    
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
            
        except Exception as e:
            logger.error(f"Error getting suggestions for word '{word}': {e}")
            return []

class RealTimeProcessor:
    """Processes text in real-time for WebSocket connections"""
    
    def __init__(self, spell_checker: EnhancedSpellChecker, grammar_checker: GrammarChecker, 
                 segmenter: TextSegmenter, syntax_restructurer: SyntaxRestructurer = None):
        self.spell_checker = spell_checker
        self.grammar_checker = grammar_checker
        self.segmenter = segmenter
        self.syntax_restructurer = syntax_restructurer
        self.word_pattern = re.compile(r'\b[a-zA-Z]+\b')
    
    async def process_text_realtime(self, text: str, websocket: WebSocket, connection_manager: ConnectionManager):
        try:
            start_time = time.time()
            
            words = self.word_pattern.findall(text.lower())
            spelling_suggestions = {}
            
            for word in set(words):
                if len(word) > 2:
                    suggestions = self.spell_checker.get_suggestions(word, max_suggestions=3)
                    if suggestions:
                        spelling_suggestions[word] = suggestions
            
            grammar_result = None
            if len(text.strip()) > 10:
                corrected = await self.enhanced_grammar_check(text)
                
                if corrected != text:
                    grammar_result = {
                        "original": text,
                        "corrected": corrected,
                        "has_changes": True,
                        "error": None
                    }
            
            processing_time = (time.time() - start_time) * 1000
            response = {
                "type": "analysis_result",
                "timestamp": time.time(),
                "processing_time_ms": round(processing_time, 2),
                "spelling_suggestions": spelling_suggestions,
                "grammar_check": grammar_result,
                "word_count": len(words),
                "character_count": len(text)
            }
            
            await connection_manager.send_personal_message(response, websocket)
            
        except Exception as e:
            logger.error(f"Error in real-time processing: {e}")
            error_response = {
                "type": "error",
                "message": "Processing error occurred",
                "timestamp": time.time()
            }
            await connection_manager.send_personal_message(error_response, websocket)
    
    async def enhanced_grammar_check(self, text: str) -> str:
        corrected, has_changes, error_msg = self.grammar_checker.check_grammar(text)
        
        if self.syntax_restructurer:
            corrected = self.syntax_restructurer.restructure_question(corrected)
        
        return corrected

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application - Loading models...")
    
    app.state.initialization_errors = []
    app.state.dict_status = {}
    
    try:
        try:
            app.state.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except OSError as e:
            logger.warning(f"SpaCy model not found: {e}, using fallback")
            app.state.nlp = English()
            app.state.initialization_errors.append("SpaCy model fallback used")

        app.state.segmenter = TextSegmenter(app.state.nlp)

        try:
            app.state.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
            
            builtin_loaded = False
            try:
                with as_file(files("symspellpy").joinpath("frequency_dictionary_en_82_765.txt")) as dict_path:
                    app.state.sym_spell.load_dictionary(str(dict_path), 0, 1)
                    builtin_loaded = True
                    logger.info("SymSpell built-in English dictionary loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load built-in dictionary: {e}")
                app.state.initialization_errors.append(f"Built-in dictionary failed: {e}")
            
            legal_loaded = False
            try:
                app.state.sym_spell.load_dictionary("legal_dictionary.txt", term_index=0, count_index=1)
                legal_loaded = True
                logger.info("Custom legal dictionary loaded successfully (1771 legal terms)")
            except Exception as e:
                logger.warning(f"Failed to load legal dictionary: {e}")
                app.state.initialization_errors.append(f"Legal dictionary failed: {e}")
            
            if not builtin_loaded and not legal_loaded:
                raise RuntimeError("Critical error: No dictionaries could be loaded")
            
            app.state.dict_status = {
                "builtin_loaded": builtin_loaded,
                "legal_loaded": legal_loaded,
                "total_legal_terms": 1771 if legal_loaded else 0
            }
            
            app.state.spell_checker = EnhancedSpellChecker(app.state.sym_spell, max_edit_distance=2)

        except Exception as e:
            logger.error(f"Failed to initialize SymSpell: {e}")
            app.state.initialization_errors.append(f"SymSpell failed: {e}")
            raise RuntimeError(f"Critical error: Cannot initialize SymSpell - {e}")

        try:
            app.state.tool = language_tool_python.LanguageTool('en-US', motherTongue='en')
            app.state.grammar_checker = EnhancedGrammarChecker(app.state.tool, app.state.nlp)
            logger.info("Enhanced LanguageTool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LanguageTool: {e}")
            app.state.initialization_errors.append(f"LanguageTool failed: {e}")
            raise RuntimeError(f"Critical error: Cannot initialize LanguageTool - {e}")

        app.state.syntax_restructurer = SyntaxRestructurer(app.state.nlp)
        app.state.connection_manager = ConnectionManager()
        app.state.realtime_processor = RealTimeProcessor(
            app.state.spell_checker, 
            app.state.grammar_checker, 
            app.state.segmenter,
            app.state.syntax_restructurer
        )

        logger.info("Application startup complete")

    except Exception as e:
        logger.critical(f"Critical error during startup: {e}")
        raise

    yield

    logger.info("Shutting down - Cleaning up resources...")
    try:
         if hasattr(app.state, 'tool') and app.state.tool:
            app.state.tool.close()
            logger.info("LanguageTool closed")
    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")
    finally:
        for attr in ['nlp', 'tool', 'sym_spell', 'segmenter', 
                     'grammar_checker', 'spell_checker', 'initialization_errors', 
                     'dict_status', 'connection_manager', 'realtime_processor',
                     'syntax_restructurer']:
            if hasattr(app.state, attr):
                setattr(app.state, attr, None)
        logger.info("Application shutdown complete")

app = FastAPI(
    title="Real-time Legal Grammar and Spelling Checking API",
    lifespan=lifespan,
    description="A high-performance real-time grammar and spelling checking API with enhanced legal dictionary support using SymSpell, LanguageTool, and WebSocket.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"]
)

# Pydantic models
class WordRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100, description="Word to get spelling suggestions for")
    max_suggestions: Optional[int] = Field(3, ge=1, le=10, description="Maximum number of suggestions")
    verbosity: Optional[str] = Field("all", pattern="^(top|closest|all)$", description="Suggestion verbosity: top, closest, or all")

class SentenceModel(BaseModel):
    sentence: str = Field(..., min_length=1, max_length=5000, description="Sentence to check for grammar errors")

class WordSuggestionResponse(BaseModel):
    word: str
    suggestions: List[str]
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    dictionary_sources: Optional[List[str]] = Field(None, description="Sources of suggestions")

class GrammarCheckResponse(BaseModel):
    original: str
    corrected: str
    has_changes: bool
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if check failed")
    sentences_processed: Optional[int] = Field(None, description="Number of sentences processed")

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]
    dictionary_status: Optional[Dict[str, Any]] = None
    initialization_warnings: Optional[List[str]] = None
    websocket_connections: Optional[int] = None

# WebSocket endpoint
@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await app.state.connection_manager.connect(websocket)
    
    try:
        welcome_message = {
            "type": "connection_established",
            "message": "Real-time grammar and spelling assistance connected",
            "features": [
                "Real-time spelling suggestions",
                "Enhanced grammar checking with syntax restructuring",
                "Legal dictionary support (1771+ terms)",
                "Performance metrics"
            ],
            "timestamp": time.time()
        }
        await app.state.connection_manager.send_personal_message(welcome_message, websocket)
        
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "text_input":
                text = message_data.get("text", "")
                if text.strip():
                    await app.state.realtime_processor.process_text_realtime(
                        text, websocket, app.state.connection_manager
                    )
            elif message_data.get("type") == "ping":
                pong_response = {
                    "type": "pong",
                    "timestamp": time.time()
                }
                await app.state.connection_manager.send_personal_message(pong_response, websocket)
                
    except WebSocketDisconnect:
        app.state.connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        app.state.connection_manager.disconnect(websocket)

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Real-time Legal Grammar and Spelling Checking API",
        "version": "1.0.0",
        "description": "Enhanced with 1771 legal terms and WebSocket support for real-time assistance",
        "endpoints": {
            "websocket": "/ws/realtime - WebSocket - Real-time grammar and spelling assistance",
            "suggestions": "/suggestions - POST - Get spelling suggestions (general + legal terms)",
            "check_sentence": "/check_sentence - POST - Check grammar for a single sentence",
            "check_text": "/check_text - POST - Check grammar for multiple sentences",
            "health": "/health - GET - Health check endpoint",
            "docs": "/docs - GET - Interactive API documentation"
        },
        "features": [
            "Real-time WebSocket assistance",
            "Combined English and Legal dictionary support (1771+ legal terms)",
            "Advanced sentence segmentation with legal abbreviation support",
            "Enhanced grammar checking with syntax restructuring",
            "Configurable suggestion parameters",
            "Comprehensive error reporting",
            "Performance optimization"
        ]
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    services = {
        "spacy": "available" if hasattr(app.state, 'nlp') and app.state.nlp else "unavailable",
        "languagetool": "available" if hasattr(app.state, 'tool') and app.state.tool else "unavailable",
        "symspell": "available" if hasattr(app.state, 'sym_spell') and app.state.sym_spell else "unavailable",
        "legal_dictionary": "available" if getattr(app.state, 'dict_status', {}).get('legal_loaded', False) else "unavailable",
        "websocket": "available" if hasattr(app.state, 'connection_manager') else "unavailable",
        "syntax_restructurer": "available" if hasattr(app.state, 'syntax_restructurer') else "unavailable"
    }
    
    dict_status = getattr(app.state, 'dict_status', {})
    warnings = getattr(app.state, 'initialization_errors', None)
    websocket_count = len(getattr(app.state.connection_manager, 'active_connections', [])) if hasattr(app.state, 'connection_manager') else 0
    
    return HealthResponse(
        status="healthy" if all(s == "available" for s in [services["languagetool"], services["symspell"], services["websocket"]]) else "degraded",
        version="1.0.0",
        services=services,
        dictionary_status=dict_status,
        initialization_warnings=warnings if warnings else None,
        websocket_connections=websocket_count
    )

@app.post("/suggestions", response_model=WordSuggestionResponse)
async def get_word_suggestions(req: WordRequest):
    start_time = time.time()
    try:
        if not hasattr(app.state, 'spell_checker') or app.state.spell_checker is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Spell checking service not available"
            )

        word = req.word.strip()
        if not word:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Word cannot be empty after stripping whitespace"
            )

        verbosity_map = {
            "top": Verbosity.TOP,
            "closest": Verbosity.CLOSEST,
            "all": Verbosity.ALL
        }
        verbosity = verbosity_map.get(req.verbosity.lower(), Verbosity.ALL)

        suggestions = app.state.spell_checker.get_suggestions(
            word.lower(), 
            max_suggestions=req.max_suggestions,
            verbosity=verbosity
        )
        
        dict_sources = []
        if getattr(app.state, 'dict_status', {}).get('builtin_loaded', False):
            dict_sources.append("English")
        if getattr(app.state, 'dict_status', {}).get('legal_loaded', False):
            dict_sources.append("Legal")
        
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000

        return WordSuggestionResponse(
            word=req.word,
            suggestions=suggestions,
            processing_time_ms=round(processing_time_ms, 2),
            dictionary_sources=dict_sources
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_word_suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while getting suggestions"
        )

@app.post("/check_sentence", response_model=GrammarCheckResponse)
async def check_sentence(data: SentenceModel):
    start_time = time.time()
    try:
        if not hasattr(app.state, 'grammar_checker') or app.state.grammar_checker is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Grammar checking service not available"
            )

        sentence = data.sentence.strip()
        if not sentence:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sentence cannot be empty"
            )

        corrected, has_changes, error_msg = app.state.grammar_checker.check_grammar(sentence)
        
        if hasattr(app.state, 'syntax_restructurer') and app.state.syntax_restructurer:
            restructured = app.state.syntax_restructurer.restructure_question(corrected)
            if restructured != corrected:
                corrected = restructured
                has_changes = True
        
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000

        return GrammarCheckResponse(
            original=sentence,
            corrected=corrected,
            has_changes=has_changes,
            processing_time_ms=round(processing_time_ms, 2),
            error_message=error_msg,
            sentences_processed=1
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in check_sentence: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking grammar"
        )

@app.post("/check_text", response_model=GrammarCheckResponse)
async def check_full_text(data: SentenceModel):
    start_time = time.time()
    try:
        if not hasattr(app.state, 'grammar_checker') or app.state.grammar_checker is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Grammar checking service not available"
            )

        text = data.sentence.strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )

        sentences = app.state.segmenter.segment_text(text)
        
        corrected_sentences = []
        total_changes = False
        error_messages = []
        
        for sentence in sentences:
            corrected, has_changes, error_msg = app.state.grammar_checker.check_grammar(sentence)
            
            if hasattr(app.state, 'syntax_restructurer') and app.state.syntax_restructurer:
                restructured = app.state.syntax_restructurer.restructure_question(corrected)
                if restructured != corrected:
                    corrected = restructured
                    has_changes = True
            
            corrected_sentences.append(corrected)
            
            if has_changes:
                total_changes = True
            if error_msg:
                error_messages.append(error_msg)

        final_text = " ".join(corrected_sentences)
        combined_error_msg = "; ".join(error_messages) if error_messages else None

        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000

        return GrammarCheckResponse(
            original=text, 
            corrected=final_text, 
            has_changes=total_changes,
            processing_time_ms=round(processing_time_ms, 2),
            error_message=combined_error_msg,
            sentences_processed=len(sentences)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in check_full_text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking text"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
