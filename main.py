import json
from difflib import get_close_matches

def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as file:
        data: dict = json.load(file)
    return data

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def extract_keywords(text: str) -> set:
    """Extract important keywords from user question"""
    # Words to ignore (common words that don't help identify the topic)
    stop_words = {'where', 'is', 'the', 'are', 'can', 'i', 'find', 'locate', 
                  'location', 'tell', 'me', 'how', 'to', 'go', 'get', 'do',
                  'you', 'know', 'what', 'which', 'way', 'at', 'of', 'in', 'on',
                  'a', 'an', 'and', 'or', 'but', 'for', 'with', 'without', 'by'}
    
    # Clean and split the text
    text_lower = text.lower()
    # Remove punctuation
    for char in '?.,!;:()[]{}':
        text_lower = text_lower.replace(char, '')
    
    words = set(text_lower.split())
    # Remove stop words
    keywords = words - stop_words
    return keywords

def calculate_keyword_match(user_keywords: set, question_keywords: set) -> float:
    """Calculate how well user keywords match a question's keywords"""
    if not user_keywords or not question_keywords:
        return 0
    
    # Count matching keywords
    matches = user_keywords.intersection(question_keywords)
    match_count = len(matches)
    
    # Calculate score (higher is better)
    # Normalize by total unique keywords
    total_keywords = len(user_keywords.union(question_keywords))
    if total_keywords == 0:
        return 0
    
    score = match_count / total_keywords
    return score

def find_best_match_by_keywords(user_question: str, knowledge_base: dict) -> tuple | None:
    """Find best match using keyword extraction"""
    user_keywords = extract_keywords(user_question)
    
    if not user_keywords:
        return None
    
    best_match = None
    best_score = 0
    best_question = None
    
    for q in knowledge_base['questions']:
        # Get keywords from main question
        question_keywords = extract_keywords(q['question'])
        
        # Calculate match score
        score = calculate_keyword_match(user_keywords, question_keywords)
        
        # Also check synonyms if they exist
        if 'synonyms' in q:
            for synonym in q['synonyms']:
                synonym_keywords = extract_keywords(synonym)
                synonym_score = calculate_keyword_match(user_keywords, synonym_keywords)
                if synonym_score > score:
                    score = synonym_score
        
        # Bonus: If user keyword is exactly in question
        for keyword in user_keywords:
            if keyword in q['question'].lower():
                score += 0.1
        
        if score > best_score and score >= 0.3:  # 30% match required
            best_score = score
            best_match = q
            best_question = q['question']
    
    if best_match:
        print(f"🔍 Matched with {best_score*100:.0f}% confidence")  # Debug
        return best_question, best_match['answer']
    
    return None

def chat_bot():
    knowledge_base: dict = load_knowledge_base('knowledge_base.json')
    
    print("🤖 Keyword-Based Chatbot Started!")
    print("I understand questions based on keywords, not exact wording.\n")
    print(f"📚 Loaded {len(knowledge_base['questions'])} topics\n")

    while True:
        user_input: str = input("\nYou: ")

        if user_input.lower() == 'quit':
            print("Bot: Goodbye!")
            break

        # Find match using keywords
        match = find_best_match_by_keywords(user_input, knowledge_base)

        if match:
            question, answer = match
            print(f"Bot: {answer}")
            print(f"   (Matched topic: {question})")  # Optional: show what it matched
        else:
            print("Bot: I don't know the answer to that question.")
            print("Bot: Can you teach me?")
            
            # Ask for keywords to help future matching
            print("   Tip: Tell me keywords that should trigger this answer")
            keywords_hint = input("   Keywords for this answer (comma separated, or press Enter to skip): ")
            
            new_answer = input("Type the answer: ")
            
            if new_answer.lower() != 'skip':
                new_entry = {"question": user_input, "answer": new_answer}
                
                if keywords_hint.strip():
                    keywords_list = [k.strip().lower() for k in keywords_hint.split(',')]
                    new_entry["keywords"] = keywords_list
                    print(f"   ✅ Added keywords: {keywords_list}")
                
                knowledge_base["questions"].append(new_entry)
                save_knowledge_base('knowledge_base.json', knowledge_base)
                print("Bot: Thank you for teaching me!")

if __name__ == "__main__":
    chat_bot()