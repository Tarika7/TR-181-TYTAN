import pdfplumber
import json
import re
from claude import client

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"PDF extraction error: {str(e)}")
    
    return text.strip()

def generate_fallback_topics(content: str, subject: str = "mathematics") -> dict:
    """Generate synthetic topics without Claude API - works offline"""
    # Extract potential topic keywords from content
    lines = content.split('\n')
    
    # Simple keyword extraction
    potential_topics = []
    for line in lines[:50]:  # Look at first 50 lines
        if len(line.strip()) > 20 and any(keyword in line.lower() for keyword in ['chapter', 'section', 'topic', 'introduction', 'lesson', 'unit']):
            potential_topics.append(line.strip()[:60])
    
    # Create standard math topics as fallback
    default_topics = [
        {
            "id": "topic_1",
            "title": "Foundations & Basics",
            "difficulty": 1,
            "prerequisites": [],
            "key_concepts": ["definitions", "fundamentals", "core concepts"],
            "explanation": "Learn the foundational concepts and definitions that underpin this topic."
        },
        {
            "id": "topic_2",
            "title": "Core Principles",
            "difficulty": 2,
            "prerequisites": ["topic_1"],
            "key_concepts": ["rules", "properties", "theorems"],
            "explanation": "Understand the key rules and properties that govern this subject area."
        },
        {
            "id": "topic_3",
            "title": "Problem Solving",
            "difficulty": 3,
            "prerequisites": ["topic_1", "topic_2"],
            "key_concepts": ["application", "techniques", "strategies"],
            "explanation": "Apply your knowledge to solve problems using various techniques."
        },
        {
            "id": "topic_4",
            "title": "Advanced Concepts",
            "difficulty": 4,
            "prerequisites": ["topic_2", "topic_3"],
            "key_concepts": ["extensions", "advanced thinking", "deeper understanding"],
            "explanation": "Explore advanced concepts that build on foundational knowledge."
        },
        {
            "id": "topic_5",
            "title": "Real-World Applications",
            "difficulty": 3,
            "prerequisites": ["topic_2"],
            "key_concepts": ["practice", "real-world", "applications"],
            "explanation": "See how concepts apply to real-world scenarios and practical problems."
        }
    ]
    
    return {
        "main_topic": "Study Material",
        "description": "Adaptive learning content from your uploaded document",
        "topics": default_topics,
        "learning_objectives": [
            "Master foundational concepts",
            "Apply knowledge to solve problems",
            "Understand advanced applications"
        ],
        "estimated_duration_minutes": 60
    }

def generate_topics_from_content(content: str, subject: str = "mathematics") -> dict:
    """Use Claude to generate topic graph from extracted content, with fallback"""
    
    prompt = f"""
You are an expert educator. Analyze the following {subject} study material and create a structured learning path.

MATERIAL:
{content[:3000]}

Generate a JSON response with this exact structure:
{{
  "main_topic": "extracted main topic name",
  "description": "brief description of the material",
  "topics": [
    {{
      "id": "topic_id",
      "title": "Topic Title",
      "difficulty": 1,
      "prerequisites": [],
      "key_concepts": ["concept1", "concept2"],
      "explanation": "Detailed explanation of this topic"
    }}
  ],
  "learning_objectives": ["objective1", "objective2"],
  "estimated_duration_minutes": 45
}}

Create 5-7 topics in logical progression. Start with basics and move to advanced.
Return ONLY valid JSON, no other text.
"""

    try:
        print("🔄 Attempting to generate topics with Claude API...")
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = response.content[0].text.strip()
        
        # Parse JSON response
        try:
            topic_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON if response has extra text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                topic_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse Claude response")
        
        print(f"✅ Topics generated successfully from Claude API")
        return topic_data
        
    except Exception as e:
        print(f"⚠️ Claude API unavailable or error: {str(e)}")
        print(f"📊 Using fallback topic generation (system will still work)...")
        return generate_fallback_topics(content, subject)

def generate_fallback_questions(topic_id: str, title: str, concepts: list, difficulty: int) -> list:
    """Generate synthetic questions without Claude API"""
    questions = []
    
    # Create question templates based on difficulty
    if difficulty <= 2:
        questions.append({
            "question": f"What is {concepts[0] if concepts else 'this concept'}?",
            "answer": f"A fundamental concept in {title}",
            "type": "short_answer",
            "hint": "Review the definition in your material"
        })
        questions.append({
            "question": f"Which of these is an example of {concepts[0] if concepts else 'this topic'}?",
            "answer": "Check the examples in your material",
            "type": "multiple_choice",
            "hint": "Look for worked examples"
        })
    elif difficulty <= 3:
        questions.append({
            "question": f"How would you apply {title} to solve a problem?",
            "answer": "Use the principles: " + ", ".join(concepts[:2]) if len(concepts) >= 2 else concepts[0],
            "type": "short_answer",
            "hint": "Think about the steps and strategies"
        })
    else:
        questions.append({
            "question": f"Why is {concepts[0] if concepts else 'this concept'} important in {title}?",
            "answer": "It provides the foundation for more advanced topics",
            "type": "short_answer",
            "hint": "Consider deeper connections and applications"
        })
    
    # Add a second question
    questions.append({
        "question": f"Practice: Can you explain {concepts[1] if len(concepts) > 1 else concepts[0]}?",
        "answer": "Yes, and here's how: [your explanation]",
        "type": "short_answer",
        "hint": "Use your own words to explain the concept"
    })
    
    # Add a third question
    questions.append({
        "question": f"What would happen if you changed a key aspect of {title}?",
        "answer": "The outcome would be different, showing the importance of this principle",
        "type": "short_answer",
        "hint": "Think about dependencies and relationships"
    })
    
    return questions

def generate_questions_for_topics(topics: list, subject: str = "mathematics") -> dict:
    """Generate questions for each topic, with fallback"""
    
    questions_dict = {}
    use_fallback = False
    
    for topic in topics:
        topic_id = topic.get("id", "unknown")
        title = topic.get("title", "")
        concepts = topic.get("key_concepts", [])
        difficulty = topic.get("difficulty", 1)
        
        prompt = f"""
Generate 3 questions for a {subject} topic about '{title}'.
Key concepts: {', '.join(concepts)}
Difficulty level: {difficulty}/5

Return as JSON array with this structure:
[
  {{
    "question": "The question text",
    "answer": "The correct answer",
    "type": "multiple_choice OR short_answer",
    "hint": "A helpful hint if stuck"
  }}
]

Return ONLY valid JSON array, no other text.
"""
        
        try:
            if not use_fallback:
                print(f"🔄 Generating questions for {topic_id}...")
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=800,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                response_text = response.content[0].text.strip()
                
                try:
                    questions = json.loads(response_text)
                except json.JSONDecodeError:
                    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                    if json_match:
                        questions = json.loads(json_match.group())
                    else:
                        questions = []
                
                questions_dict[topic_id] = questions
            else:
                # Use fallback
                questions_dict[topic_id] = generate_fallback_questions(topic_id, title, concepts, difficulty)
            
        except Exception as e:
            print(f"⚠️ Claude API failed for questions: {e}")
            print(f"📊 Using fallback questions for {topic_id}...")
            use_fallback = True
            questions_dict[topic_id] = generate_fallback_questions(topic_id, title, concepts, difficulty)
    
    return questions_dict

def process_pdf_to_topic_graph(pdf_path: str, subject: str = "mathematics") -> tuple:
    """Complete pipeline: PDF → Topics → Questions"""
    
    # Step 1: Extract text
    print("Extracting text from PDF...")
    content = extract_text_from_pdf(pdf_path)
    
    # Use fallback if PDF has minimal content
    if not content or len(content) < 50:
        print("⚠️ PDF content is minimal, using basic structure")
        content = "Study material"
    
    # Step 2: Generate topics
    print("Generating topics from content...")
    topic_data = generate_topics_from_content(content, subject)
    
    topics = topic_data.get("topics", [])
    if not topics:
        print("⚠️ No topics generated, using defaults")
        topic_data = generate_fallback_topics(content, subject)
        topics = topic_data.get("topics", [])
    
    # Step 3: Generate questions
    print("Generating questions for each topic...")
    questions = generate_questions_for_topics(topics, subject)
    
    return topic_data, questions
