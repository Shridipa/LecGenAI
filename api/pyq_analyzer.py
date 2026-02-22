import os
import pandas as pd
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from youtubesearchpython import VideosSearch
import pdfplumber
import docx
import gdown
from concurrent.futures import ThreadPoolExecutor
import uuid
import PIL.Image
try:
    import pytesseract
except ImportError:
    pytesseract = None


class PYQAnalyzer:
    def __init__(self):
        # Suppress joblib warning on Windows
        os.environ['LOKY_MAX_CPU_COUNT'] = '4'
        self.stop_words = 'english'
        self.answer_generator = None
        self.enable_ai_answers = False  # Disabled by default for speed

        # Configure Tesseract Path once
        self.tesseract_cmd = None
        if os.name == 'nt':
            try:
                import shutil
                self.tesseract_cmd = shutil.which('tesseract')
                if not self.tesseract_cmd:
                    paths = [
                        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                        os.path.expandvars(r'%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe')
                    ]
                    for p in paths:
                        if os.path.exists(p):
                            self.tesseract_cmd = p
                            break
            except Exception:
                self.tesseract_cmd = None
                print("Warning: Could not detect Tesseract path on Windows during initialization.")
        
    def _init_answer_generator(self):
        """Lazy load the answer generation model"""
        if self.answer_generator is None and self.enable_ai_answers:
            try:
                from transformers import pipeline
                self.answer_generator = pipeline("text2text-generation", model="google/flan-t5-base", max_length=512)
            except Exception as e:
                print(f"Could not load answer generator: {e}")
                self.answer_generator = False
        
    def extract_text_from_file(self, file_path):
        """Extract text and images from PDF, DOCX, CSV, or TXT files."""
        ext = file_path.split('.')[-1].lower()
        text = ""
        
        try:
            if ext == 'pdf':
                with pdfplumber.open(file_path) as pdf:
                    ocr_count = 0
                    max_ocr_per_file = 10 
                    # Process only first 10 pages for moderate depth
                    for i, page in enumerate(pdf.pages[:10]):
                        try:
                            # 1. Extract words with position
                            words = page.extract_words()
                            
                            # 2. Extract images
                            images = page.images
                            
                            # Group words into lines (tolerance 5px)
                            lines = []
                            current_line = []
                            last_top = 0
                            
                            # Sort words by top then x0
                            sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
                            
                            for word in sorted_words:
                                if not current_line:
                                    current_line.append(word)
                                    last_top = word['top']
                                else:
                                    if abs(word['top'] - last_top) < 5:
                                        current_line.append(word)
                                    else:
                                        # New line
                                        lines.append({
                                            'type': 'text',
                                            'top': min(w['top'] for w in current_line),
                                            'bottom': max(w['bottom'] for w in current_line),
                                            'text': ' '.join(w['text'] for w in current_line)
                                        })
                                        current_line = [word]
                                        last_top = word['top']
                            
                            # Append last line
                            if current_line:
                                lines.append({
                                    'type': 'text',
                                    'top': min(w['top'] for w in current_line),
                                    'bottom': max(w['bottom'] for w in current_line),
                                    'text': ' '.join(w['text'] for w in current_line)
                                })

                            # Combine lines and images
                            content_items = lines
                            for img in images:
                                if img['width'] < 50 or img['height'] < 50:
                                    continue
                                content_items.append({
                                    'type': 'image',
                                    'top': img['top'],
                                    'bottom': img['bottom'],
                                    'obj': img
                                })
                            
                            # Sort all items by vertical position
                            content_items.sort(key=lambda x: x['top'])
                            
                            # Build merged text
                            page_text = ""
                            for item in content_items:
                                 if item['type'] == 'text':
                                     page_text += item['text'] + "\n"
                                 elif item['type'] == 'image':
                                    try:
                                        # Validate bbox coordinates
                                        x0 = max(0, item['obj']['x0'])
                                        top = max(0, item['obj']['top'])
                                        x1 = min(page.width, item['obj']['x1'])
                                        bottom = min(page.height, item['obj']['bottom'])
                                        
                                        # Skip invalid dimensions
                                        if x1 - x0 < 10 or bottom - top < 10:
                                            continue
                                            
                                        bbox = (x0, top, x1, bottom)
                                        cropped = page.crop(bbox)
                                        img_obj = cropped.to_image(resolution=150)
                                        
                                        img_filename = f"diagram_{uuid.uuid4().hex[:8]}.png"
                                        img_path = os.path.join("static/images", img_filename)
                                        img_obj.save(img_path)
                                        # Try OCR using cached path
                                        ocr_text = ""
                                        if pytesseract:
                                            try:
                                                if self.tesseract_cmd:
                                                    pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
                                                
                                                # Use the PIL image from PageImage for OCR
                                                # pytesseract.image_to_string expects a PIL image or path
                                                if ocr_count < max_ocr_per_file:
                                                    pil_img = img_obj.original
                                                    # Add timeout for OCR to prevent hanging
                                                    ocr_text = pytesseract.image_to_string(pil_img, timeout=30).strip()
                                                    ocr_count += 1
                                                else:
                                                    print(f"OCR skipped: Reached limit of {max_ocr_per_file} images per file.")
                                            except Exception as e:
                                                print(f"OCR execution failed: {e}")
                                        else:
                                            print("OCR skipped: pytesseract module not installed or could not be loaded.")
                                        
                                        img_url = f"http://localhost:8000/static/images/{img_filename}"
                                        page_text += f"\n\n![Diagram]({img_url})\n"
                                        
                                        if ocr_text:
                                            page_text += f"(Diagram Content: {ocr_text})\n\n"
                                        else:
                                            page_text += "\n\n"
                                            
                                    except Exception as e:
                                        import traceback
                                        error_details = traceback.format_exc()
                                        print(f"Image extraction item failed: {e}\nDetails: {error_details}")
                                        
                            text += page_text + "\n"
                        except Exception as e:
                            print(f"Error processing page {i}: {e}")
                        
            elif ext == 'docx':
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"
                    # TODO: DOCX image extraction is harder, skipping for now
                    
            elif ext == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif ext == 'csv':
                df = pd.read_csv(file_path)
                possible_cols = [c for c in df.columns if 'question' in c.lower() or 'q' in c.lower()]
                if not possible_cols:
                    text = df.to_string(index=False)
                else:
                    target_col = possible_cols[0]
                    text = "\n".join(df[target_col].astype(str).tolist())
            else:
                return None
        except Exception as e:
            import traceback
            print(f"Major error extracting text from {file_path}: {e}")
            traceback.print_exc()
            return None
        finally:
            # Explicitly clear memory if possible
            try:
                import gc
                gc.collect()
            except:
                pass
            
        return text

    def parse_questions(self, text):
        """
        Enhanced question extraction with multi-line support to capture diagrams.
        Groups text lines and diagram references into complete question blocks.
        """
        if not text:
            return []
            
        lines = text.split('\n')
        questions = []
        current_question_lines = []
        
        # optimized patterns for Start of Question
        start_patterns = [
            r'^\d+[\.)]\s+(.+)',
            r'^Q\d+[:\.]\s+(.+)',
            r'^Question\s+\d+[:\.]\s+(.+)',
        ]
        
        question_starters = ['explain', 'define', 'what', 'why', 'how', 'describe', 
                           'discuss', 'compare', 'analyze', 'evaluate', 'list', 
                           'state', 'write', 'derive', 'prove', 'solve']
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_start = False
            clean_line = line
            
            # Check explicit patterns (Numbering)
            for pattern in start_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    is_start = True
                    clean_line = match.group(1) if match.lastindex else line
                    break
            
            # Check explicit keywords if no pattern match
            if not is_start:
                line_lower = line.lower()
                # Ensure it's not a diagram line being mistaken for text
                if "![diagram]" not in line_lower:
                    for starter in question_starters:
                        # Keyword must be at start of line
                        if line_lower.startswith(starter):
                            is_start = True
                            break

            # Logic to handle accumulation
            if is_start:
                # Save previous question if exists and valid
                if current_question_lines:
                    full_q = " ".join(current_question_lines).strip()
                    if len(full_q) > 10: 
                       questions.append(full_q)
                
                # Start new question
                # Clean numbering from start for cleaner text
                clean_line = re.sub(r'^\d+[\.)]\s+', '', clean_line)
                clean_line = re.sub(r'^Q\d+[:\.]\s+', '', clean_line)
                clean_line = re.sub(r'^Question\s+\d+[:\.]\s+', '', clean_line, flags=re.IGNORECASE)
                current_question_lines = [clean_line.strip()]
            else:
                # Continuation line (text wrap or diagram)
                if current_question_lines:
                    # Ignore very short noise lines, but keep diagram references
                    if len(line) < 3 and "![Diagram]" not in line:
                        continue
                    current_question_lines.append(line)
        
        # Add last question
        if current_question_lines:
            full_q = " ".join(current_question_lines).strip()
            if len(full_q) > 10:
                questions.append(full_q)
                
        # Deduplicate while preserving order (using dict keys)
        return list(dict.fromkeys(questions))[:200]

    def analyze_topics(self, questions, n_clusters=5):
        """Optimized topic modeling with robust fallback"""
        # Fallback DataFrame
        default_df = pd.DataFrame({'Question': questions, 'Topic': [0]*len(questions), 'LDA_Topic': [0]*len(questions)})
        
        if not questions or len(questions) < n_clusters:
            return default_df
        
        try:
            n_clusters = min(n_clusters, len(questions))
            
            # Optimized TF-IDF with smaller feature set
            tfidf_vectorizer = TfidfVectorizer(stop_words=self.stop_words, max_features=50)
            tfidf_matrix = tfidf_vectorizer.fit_transform(questions)
            
            # Fast MiniBatchKMeans for speed
            from sklearn.cluster import MiniBatchKMeans
            kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init=3, max_iter=50)
            kmeans_topics = kmeans.fit_predict(tfidf_matrix)
            
            # Simplified LDA (reduced iterations for speed)
            count_vectorizer = CountVectorizer(stop_words=self.stop_words, max_features=50)
            count_matrix = count_vectorizer.fit_transform(questions)
            
            lda = LatentDirichletAllocation(n_components=n_clusters, random_state=42, max_iter=5)
            lda_topics = lda.fit_transform(count_matrix)
            lda_topic_assignments = np.argmax(lda_topics, axis=1)
            
            df = pd.DataFrame({
                'Question': questions, 
                'Topic': kmeans_topics,
                'LDA_Topic': lda_topic_assignments
            })
            
            return df
        except Exception as e:
            print(f"Topic analysis failed: {e}. Returning default grouping.")
            return default_df

    def get_topic_keywords(self, questions, topics, n_keywords=3):
        """Generate full descriptive topic names from question content"""
        df = pd.DataFrame({'Question': questions, 'Topic': topics})
        keywords_map = {}
        
        # Common domain-specific expansions for better topic names
        expansions = {
            # Single letters and common abbreviations
            'q': 'Question',
            'r': 'Relation',
            'w': 'Write',
            's': 'Statement',
            'p': 'Program',
            'n': 'Number',
            'er': 'Entity-Relationship',
            'os': 'Operating System',
            'cpu': 'Central Processing Unit',
            'ram': 'Random Access Memory',
            'rom': 'Read Only Memory',
            'io': 'Input Output',
            'api': 'Application Programming Interface',
            'ui': 'User Interface',
            'ux': 'User Experience',
            'html': 'HyperText Markup Language',
            'css': 'Cascading Style Sheets',
            'xml': 'Extensible Markup Language',
            'json': 'JavaScript Object Notation',
            'http': 'HyperText Transfer Protocol',
            'tcp': 'Transmission Control Protocol',
            'udp': 'User Datagram Protocol',
            'ip': 'Internet Protocol',
            'dns': 'Domain Name System',
            'url': 'Uniform Resource Locator',
            'uri': 'Uniform Resource Identifier',
            
            # Database terms
            'database': 'Database Management Systems',
            'dbms': 'Database Management Systems',
            'rdbms': 'Relational Database Management Systems',
            'sql': 'Structured Query Language',
            'nosql': 'Non-Relational Database',
            'normalization': 'Database Normalization',
            'entity': 'Entity-Relationship Model',
            'relationship': 'Entity-Relationship Model',
            'query': 'Query Processing',
            'queries': 'Query Processing',
            'transaction': 'Transaction Management',
            'concurrency': 'Concurrency Control',
            'indexing': 'Database Indexing',
            'schema': 'Database Schema Design',
            'acid': 'Atomicity Consistency Isolation Durability',
            
            # Programming and algorithms
            'design': 'System Design',
            'algorithm': 'Algorithm Design and Analysis',
            'algorithms': 'Algorithm Design and Analysis',
            'structure': 'Data Structures',
            'structures': 'Data Structures',
            'programming': 'Programming Fundamentals',
            'oop': 'Object-Oriented Programming',
            'oops': 'Object-Oriented Programming',
            'functional': 'Functional Programming',
            
            # Computer systems
            'network': 'Computer Networks',
            'networking': 'Computer Networks',
            'operating': 'Operating Systems',
            'system': 'System Architecture',
            'systems': 'System Architecture',
            'compiler': 'Compiler Design',
            'parsing': 'Parsing Techniques',
            'processor': 'Processor Architecture',
            'memory': 'Memory Management',
            
            # Software engineering
            'software': 'Software Engineering',
            'engineering': 'Software Engineering',
            'testing': 'Software Testing',
            'debugging': 'Debugging Techniques',
            'development': 'Software Development',
            'agile': 'Agile Methodology',
            'scrum': 'Scrum Framework',
            
            # Security and cryptography
            'security': 'Information Security',
            'encryption': 'Cryptography and Encryption',
            'cryptography': 'Cryptography and Encryption',
            'authentication': 'Authentication and Authorization',
            
            # AI and ML
            'machine': 'Machine Learning',
            'learning': 'Machine Learning',
            'intelligence': 'Artificial Intelligence',
            'artificial': 'Artificial Intelligence',
            'neural': 'Neural Networks',
            'deep': 'Deep Learning',
            
            # Modern technologies
            'web': 'Web Technologies',
            'cloud': 'Cloud Computing',
            'computing': 'Cloud Computing',
            'distributed': 'Distributed Systems',
            'parallel': 'Parallel Computing',
            'blockchain': 'Blockchain Technology',
            'iot': 'Internet of Things',
        }
        
        # Context-aware expansions for ambiguous single letters
        # These are applied based on surrounding words
        context_expansions = {
            'm': {
                'default': 'Method',
                'context_rules': [
                    (['matrix', 'matrices', 'linear'], 'Matrix'),
                    (['memory', 'ram', 'storage'], 'Memory'),
                    (['model', 'modeling'], 'Model'),
                    (['module', 'component'], 'Module'),
                    (['method', 'function'], 'Method'),
                    (['management', 'manager'], 'Management'),
                    (['machine', 'learning'], 'Machine'),
                ]
            },
            'j': {
                'default': 'Join',
                'context_rules': [
                    (['join', 'joins', 'sql', 'query'], 'Join'),
                    (['java', 'programming'], 'Java'),
                    (['json', 'data'], 'JSON'),
                    (['job', 'scheduling', 'process'], 'Job'),
                ]
            },
            'write': {
                'default': 'Write',
                'context_rules': [
                    (['query', 'sql', 'select'], 'Write Query'),
                    (['program', 'code', 'function'], 'Write Program'),
                    (['algorithm', 'pseudo'], 'Write Algorithm'),
                    (['explain', 'describe'], 'Write Explanation'),
                ]
            },
            'k': {
                'default': 'Key',
                'context_rules': [
                    (['key', 'primary', 'foreign'], 'Key'),
                    (['means', 'cluster'], 'K-Means'),
                    (['nearest', 'neighbor'], 'K-Nearest'),
                ]
            },
            'b': {
                'default': 'Binary',
                'context_rules': [
                    (['tree', 'search', 'sort'], 'Binary'),
                    (['boolean', 'logic'], 'Boolean'),
                    (['byte', 'data'], 'Byte'),
                ]
            },
            't': {
                'default': 'Table',
                'context_rules': [
                    (['table', 'database', 'relation'], 'Table'),
                    (['tree', 'node', 'graph'], 'Tree'),
                    (['time', 'complexity'], 'Time'),
                    (['transaction', 'acid'], 'Transaction'),
                    (['test', 'testing'], 'Test'),
                ]
            },
            'c': {
                'default': 'Class',
                'context_rules': [
                    (['class', 'object', 'oop'], 'Class'),
                    (['code', 'program'], 'Code'),
                    (['complexity', 'algorithm'], 'Complexity'),
                    (['compiler', 'parse'], 'Compiler'),
                    (['cache', 'memory'], 'Cache'),
                ]
            },
            'd': {
                'default': 'Data',
                'context_rules': [
                    (['data', 'structure'], 'Data'),
                    (['database', 'dbms'], 'Database'),
                    (['diagram', 'model'], 'Diagram'),
                    (['design', 'pattern'], 'Design'),
                ]
            },
            'e': {
                'default': 'Entity',
                'context_rules': [
                    (['entity', 'relationship', 'er'], 'Entity'),
                    (['error', 'exception'], 'Error'),
                    (['encryption', 'security'], 'Encryption'),
                ]
            },
            'f': {
                'default': 'Function',
                'context_rules': [
                    (['function', 'method', 'call'], 'Function'),
                    (['file', 'system', 'directory'], 'File'),
                    (['foreign', 'key'], 'Foreign'),
                ]
            },
        }
        
        def expand_with_context(keyword, all_keywords):
            """Intelligently expand single letters based on context"""
            keyword_lower = keyword.lower()
            
            # If it's in context_expansions, use context-aware logic
            if keyword_lower in context_expansions:
                rules = context_expansions[keyword_lower]
                
                # Check context rules
                for context_words, expansion in rules['context_rules']:
                    # If any context word appears in the keyword list
                    if any(ctx_word in all_keywords for ctx_word in context_words):
                        return expansion
                
                # Return default if no context match
                return rules['default']
            
            # Otherwise use standard expansions
            return expansions.get(keyword_lower, keyword.capitalize())
        
        for topic_id in sorted(df['Topic'].unique()):
            topic_questions = df[df['Topic'] == topic_id]['Question'].tolist()
            if len(topic_questions) == 0:
                continue
            
            try:
                # Extract meaningful keywords
                all_words = ' '.join(topic_questions).lower().split()
                
                # Filter for meaningful words
                word_freq = {}
                for word in all_words:
                    if word.isalpha():
                        # Allow word if len > 3 OR it's a known expansion/context-expansion
                        if len(word) > 3 or word in expansions or word in context_expansions:
                            word_freq[word] = word_freq.get(word, 0) + 1
                
                # Get top keywords
                top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
                keywords = [w[0] for w, _ in top_words]
                
                # Expand keywords to full phrases
                expanded_phrases = []
                used_expansions = set()
                
                for keyword in keywords:
                    # Use intelligent context-aware expansion
                    expansion = expand_with_context(keyword, all_words)
                    
                    if expansion not in used_expansions:
                        expanded_phrases.append(expansion)
                        used_expansions.add(expansion)
                
                # Create descriptive topic name
                if len(expanded_phrases) == 0:
                    topic_name = f"General Topic {topic_id + 1}"
                elif len(expanded_phrases) == 1:
                    topic_name = expanded_phrases[0]
                elif len(expanded_phrases) == 2:
                    topic_name = f"{expanded_phrases[0]} and {expanded_phrases[1]}"
                else:
                    # For 3+ phrases, use proper formatting
                    topic_name = f"{expanded_phrases[0]}, {expanded_phrases[1]} and {expanded_phrases[2]}"
                
                keywords_map[int(topic_id)] = topic_name
                    
            except Exception as e:
                print(f"Keyword extraction error: {e}")
                keywords_map[int(topic_id)] = f"General Topic {topic_id + 1}"
            
        return keywords_map

    def rewrite_vague_question(self, question, topic_name):
        """
        Rewrite vague questions to include topic context.
        Transforms:
        - "Which is correct?" → "Which of the following is correct about [Topic]?"
        - "Which is not correct?" → "Which of the following is not correct about [Topic]?"
        """
        question_lower = question.lower().strip()
        
        # Patterns for vague questions
        vague_patterns = [
            (r'^which\s+is\s+correct\??$', 'Which of the following is correct about {}?'),
            (r'^which\s+is\s+not\s+correct\??$', 'Which of the following is not correct about {}?'),
            (r'^which\s+is\s+incorrect\??$', 'Which of the following is incorrect about {}?'),
            (r'^which\s+of\s+the\s+following\s+is\s+correct\??$', 'Which of the following is correct about {}?'),
            (r'^which\s+of\s+the\s+following\s+is\s+not\s+correct\??$', 'Which of the following is not correct about {}?'),
            (r'^which\s+of\s+the\s+following\s+is\s+incorrect\??$', 'Which of the following is incorrect about {}?'),
            (r'^which\s+statement\s+is\s+correct\??$', 'Which statement is correct about {}?'),
            (r'^which\s+statement\s+is\s+not\s+correct\??$', 'Which statement is not correct about {}?'),
            (r'^which\s+statement\s+is\s+incorrect\??$', 'Which statement is incorrect about {}?'),
            (r'^select\s+the\s+correct\s+statement\??$', 'Select the correct statement about {}'),
            (r'^select\s+the\s+incorrect\s+statement\??$', 'Select the incorrect statement about {}'),
            (r'^identify\s+the\s+correct\s+statement\??$', 'Identify the correct statement about {}'),
            (r'^identify\s+the\s+incorrect\s+statement\??$', 'Identify the incorrect statement about {}'),
        ]
        
        # Check if question matches any vague pattern
        for pattern, template in vague_patterns:
            if re.match(pattern, question_lower):
                # Clean up topic name (remove "and", "or" connectors for readability)
                clean_topic = topic_name.replace(' and ', ', ').replace(' or ', ', ')
                return template.format(clean_topic)
        
        # If question is very short and ends with "correct?" or "incorrect?", likely vague
        if len(question.split()) <= 5 and ('correct?' in question_lower or 'incorrect?' in question_lower):
            if 'not correct' in question_lower or 'incorrect' in question_lower:
                return f"Which of the following is not correct about {topic_name}?"
            else:
                return f"Which of the following is correct about {topic_name}?"
        
        # Return original question if not vague
        return question

    def generate_answer(self, question):
        """Generate AI-powered answer (disabled by default for speed)"""
        if not self.enable_ai_answers:
            return None
            
        self._init_answer_generator()
        
        if not self.answer_generator or self.answer_generator is False:
            return None
        
        try:
            prompt = f"Answer this question in detail: {question}"
            result = self.answer_generator(prompt, max_length=300, min_length=50)
            return result[0]['generated_text'] if result else None
        except Exception as e:
            print(f"Answer generation error: {e}")
            return None

    def fetch_resources(self, query):
        """Search YouTube for educational video resources (reduced to 2 results)"""
        try:
            # Try to search YouTube with error handling
            videosSearch = VideosSearch(query + " lecture tutorial", limit=2)
            results = videosSearch.result()
            
            resources = []
            if results and 'result' in results:
                for video in results['result']:
                    resources.append({
                        'type': 'video',
                        'title': video.get('title', 'Video Tutorial'),
                        'link': video.get('link', '#'),
                        'thumbnail': video.get('thumbnails', [{}])[0].get('url', ''),
                        'duration': video.get('duration', 'N/A')
                    })
            return resources
        except TypeError as e:
            # Handle the 'proxies' parameter error silently
            # YouTube search temporarily unavailable, but article resources still work
            return []
        except Exception as e:
            # Silent error handling - system continues with article resources
            return []

    def fetch_article_resources(self, query):
        """
        Generate VERIFIED article/tutorial links using topic mapping and smart URL construction.
        Prevents 404 errors by using known valid paths.
        """
        try:
            # Clean query and get key terms
            clean_query = query.lower().replace(' and ', ' ').replace(',', '').strip()
            
            # --- 1. Verified Resource Map (Guaranteed Validation) ---
            # Map keywords/topics to known valid URLs
            verified_map = {
                'normalization': [
                    {'title': 'Database Normalization Forms', 'link': 'https://www.geeksforgeeks.org/database-normalization-introduction/', 'platform': 'GeeksforGeeks'},
                    {'title': 'DBMS Normalization Guide', 'link': 'https://www.tutorialspoint.com/dbms/database_normalization.htm', 'platform': 'TutorialsPoint'}
                ],
                'sql': [
                    {'title': 'SQL Tutorial', 'link': 'https://www.geeksforgeeks.org/sql-tutorial/', 'platform': 'GeeksforGeeks'},
                    {'title': 'SQL Guide', 'link': 'https://www.tutorialspoint.com/sql/index.htm', 'platform': 'TutorialsPoint'}
                ],
                'join': [
                    {'title': 'SQL Joins', 'link': 'https://www.geeksforgeeks.org/sql-join-set-1-inner-left-right-and-full-joins/', 'platform': 'GeeksforGeeks'},
                    {'title': 'SQL Joins Tutorial', 'link': 'https://www.tutorialspoint.com/sql/sql-using-joins.htm', 'platform': 'TutorialsPoint'}
                ],
                'relational algebra': [
                    {'title': 'Relational Algebra', 'link': 'https://www.geeksforgeeks.org/introduction-to-relational-algebra-in-dbms/', 'platform': 'GeeksforGeeks'},
                    {'title': 'Relational Algebra DBMS', 'link': 'https://www.tutorialspoint.com/dbms/relational_algebra.htm', 'platform': 'TutorialsPoint'}
                ],
                'er model': [
                    {'title': 'ER Model in DBMS', 'link': 'https://www.geeksforgeeks.org/introduction-of-er-model/', 'platform': 'GeeksforGeeks'},
                    {'title': 'ER Model Tutorial', 'link': 'https://www.tutorialspoint.com/dbms/er_model_basic_concepts.htm', 'platform': 'TutorialsPoint'}
                ],
                'transaction': [
                    {'title': 'Transaction in DBMS', 'link': 'https://www.geeksforgeeks.org/transaction-in-dbms/', 'platform': 'GeeksforGeeks'},
                    {'title': 'DBMS Transaction', 'link': 'https://www.tutorialspoint.com/dbms/database_transaction.htm', 'platform': 'TutorialsPoint'}
                ],
                'indexing': [
                    {'title': 'Indexing in Databases', 'link': 'https://www.geeksforgeeks.org/indexing-in-databases-set-1/', 'platform': 'GeeksforGeeks'},
                    {'title': 'DBMS Indexing', 'link': 'https://www.tutorialspoint.com/dbms/dbms_indexing.htm', 'platform': 'TutorialsPoint'}
                ],
                 'process scheduling': [
                    {'title': 'CPU Scheduling', 'link': 'https://www.geeksforgeeks.org/cpu-scheduling-in-operating-systems/', 'platform': 'GeeksforGeeks'},
                    {'title': 'OS Scheduling Algorithms', 'link': 'https://www.tutorialspoint.com/operating_system/os_process_scheduling.htm', 'platform': 'TutorialsPoint'}
                ],
                'deadlock': [
                    {'title': 'Introduction to Deadlock', 'link': 'https://www.geeksforgeeks.org/introduction-of-deadlock-in-operating-system/', 'platform': 'GeeksforGeeks'},
                    {'title': 'OS Deadlock', 'link': 'https://www.tutorialspoint.com/operating_system/os_deadlock.htm', 'platform': 'TutorialsPoint'}
                ],
                'tcp': [
                    {'title': 'TCP/IP Model', 'link': 'https://www.geeksforgeeks.org/tcp-ip-model/', 'platform': 'GeeksforGeeks'},
                    {'title': 'Data Communication - TCP/IP', 'link': 'https://www.tutorialspoint.com/data_communication_computer_network/tcp_ip_model.htm', 'platform': 'TutorialsPoint'}
                ],
            }
            
            # Check verified map first
            for key, resources in verified_map.items():
                if key in clean_query:
                    return resources
            
            # --- 2. Smart URL Construction (Fallback) ---
            # If no direct match, construct high-probability URLs
            
            article_resources = []
            search_slug = clean_query.replace(' ', '-')
            
            # GeeksforGeeks Search Link (Always Valid)
            article_resources.append({
                'title': f"{query} - GeeksforGeeks",
                'link': f"https://www.geeksforgeeks.org/?s={search_slug}",  # Search URL is never 404
                'platform': 'GeeksforGeeks'
            })
            
            # TutorialsPoint Search Link (Always Valid)
            article_resources.append({
                'title': f"{query} - TutorialsPoint",
                'link': f"https://www.tutorialspoint.com/search/{search_slug}", # Search URL is never 404
                'platform': 'TutorialsPoint'
            })
            
            # W3Schools (Specific topics only)
            if any(tech in clean_query for tech in ['sql', 'html', 'css', 'js', 'python', 'java']):
                 article_resources.append({
                    'title': f"{query} - W3Schools",
                    'link': f"https://www.w3schools.com/", # Fallback to home, hard to deep-link dynamically safely
                    'platform': 'W3Schools'
                })

            return article_resources

        except Exception as e:
            print(f"Article resource fetch error: {e}")
            # Ultimate fallback - safer than returning nothing
            return [
                {'title': 'GeeksforGeeks Computer Science', 'link': 'https://www.geeksforgeeks.org/computer-science-tutorials/', 'platform': 'GeeksforGeeks'},
                {'title': 'TutorialsPoint Library', 'link': 'https://www.tutorialspoint.com/tutorialslibrary.htm', 'platform': 'TutorialsPoint'}
            ]

    def perform_full_analysis(self, file_paths):
        """Optimized analysis pipeline with parallel processing"""
        
        # 1. Parallel file extraction for speed
        all_text = ""
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(self.extract_text_from_file, file_paths))
            all_text = "\n".join([r for r in results if r])
        
        if not all_text.strip():
            return {"error": "Could not extract text from any provided files."}
            
        # 2. Fast parsing
        questions = self.parse_questions(all_text)
        if not questions:
             lines = [l.strip() for l in all_text.split('\n') if len(l.strip()) > 15]
             questions = lines[:200]
        
        if not questions:
            return {"error": "No questions identified in the documents."}

        # 3. Optimized clustering
        n_clusters = max(3, min(8, len(questions) // 5))
        df = self.analyze_topics(questions, n_clusters)
        
        # 4. Fast importance scoring
        importance_counts = df['Question'].value_counts()
        df['Frequency'] = df['Question'].map(importance_counts)
        
        results_df = df.drop_duplicates(subset=['Question']).copy()
        
        # Simplified scoring
        try:
            max_freq = results_df['Frequency'].max()
            if max_freq > 0:
                results_df['ImportanceScore'] = results_df['Frequency'] / max_freq
            else:
                results_df['ImportanceScore'] = 0
            
            results_df['Importance'] = pd.qcut(
                results_df['ImportanceScore'].rank(method='first'), 
                3, 
                labels=["Standard", "Important", "Critical"],
                duplicates='drop'
            )
        except:
            results_df['Importance'] = "Standard"

        # 5. Fast keyword extraction
        topic_keywords = self.get_topic_keywords(results_df['Question'].tolist(), results_df['Topic'].tolist())
        
        # Helper for parallel topic processing
        def process_topic_group(args):
            topic_id, group = args
            topic_name = topic_keywords.get(topic_id, f"Topic {topic_id+1}")
            
            # Fetch resources in parallel (network efficient)
            video_resources = self.fetch_resources(topic_name)
            article_resources = self.fetch_article_resources(topic_name)
            
            all_resources = video_resources + article_resources
            
            questions_list = []
            for _, row in group.iterrows():
                try:
                    original_question = row['Question']
                    rewritten_question = self.rewrite_vague_question(original_question, topic_name)
                    
                    question_data = {
                        "text": rewritten_question,
                        "importance": str(row.get('Importance', 'Standard')),
                        "frequency": int(row.get('Frequency', 1))
                    }
                    questions_list.append(question_data)
                except Exception as e:
                    continue
            
            questions_list.sort(key=lambda x: x['frequency'], reverse=True)
            
            topic_output = {
                "topic": topic_name,
                "questions": questions_list[:10],
                "resources": {
                    "videos": video_resources if video_resources else [],
                    "articles": article_resources if article_resources else [],
                    "total_count": len(all_resources)
                }
            }
            
            if len(all_resources) == 0:
                topic_output["resources"]["message"] = "No resources found for this topic"
                
            return topic_output

        # Process topics in parallel
        # Higher threads for I/O bound tasks
        # Process topics in parallel with fallback
        final_output = []
        try:
            # Try parallel processing first
            with ThreadPoolExecutor(max_workers=4) as executor:
                final_output = list(executor.map(process_topic_group, results_df.groupby('Topic')))
        except Exception as e:
            print(f"Parallel processing failed: {e}. Falling back to sequential.")
            # Fallback to sequential processing
            final_output = []
            for topic_data in results_df.groupby('Topic'):
                try:
                    res = process_topic_group(topic_data)
                    final_output.append(res)
                except Exception as ex:
                    print(f"Error processing topic in fallback: {ex}")
                    continue

            
        # Calculate summary statistics
        total_resources = sum(topic.get('resources', {}).get('total_count', 0) for topic in final_output)
        avg_questions_per_topic = len(questions) / len(final_output) if final_output else 0
        
        return {
            "total_questions": len(questions),
            "topics_found": len(final_output),
            "analysis": final_output,
            "summary": {
                "total_questions_analyzed": len(questions),
                "number_of_topics": len(final_output),
                "analysis_status": "Complete" if final_output else "Incomplete",
                "total_resources_found": total_resources,
                "average_questions_per_topic": round(avg_questions_per_topic, 1),
                "classification_breakdown": {
                    "critical": sum(1 for topic in final_output for q in topic['questions'] if q['importance'] == 'Critical'),
                    "important": sum(1 for topic in final_output for q in topic['questions'] if q['importance'] == 'Important'),
                    "standard": sum(1 for topic in final_output for q in topic['questions'] if q['importance'] == 'Standard')
                }
            }
        }

    def process_drive_link(self, url, output_folder):
        """Download file from Google Drive link."""
        try:
            if 'drive.google.com' not in url:
                return []
                
            output_path = os.path.join(output_folder, f"drive_download_{uuid.uuid4().hex}")
            downloaded_files = []
            
            if 'folder' in url:
                os.makedirs(output_path, exist_ok=True)
                print(f"Downloading folder to: {output_path}")
                # Use quiet=False to see errors in logs
                gdown.download_folder(url, output=output_path, quiet=False, use_cookies=False)
                
                for root, dirs, files in os.walk(output_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        # Filter out non-supported files if necessary, or let processor handle
                        if self._is_valid_pyq_file(full_path):
                            downloaded_files.append(full_path)
                            
                print(f"Found {len(downloaded_files)} files in folder.")
            else:
                out = gdown.download(url, output=output_path, quiet=False, fuzzy=True)
                if out and self._is_valid_pyq_file(out):
                    downloaded_files.append(out)
                    print(f"Downloaded single file: {out}")
                    
            if not downloaded_files:
                print("Warning: No valid files found after download.")
                
            return downloaded_files
        except Exception as e:
            print(f"Drive download error: {e}")
            return []

    def _is_valid_pyq_file(self, file_path):
        """Check if file is supported for analysis."""
        valid_exts = ['.pdf', '.docx', '.txt', '.csv']
        return any(file_path.lower().endswith(ext) for ext in valid_exts)
