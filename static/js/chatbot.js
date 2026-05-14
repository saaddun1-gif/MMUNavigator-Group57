// MMU Navigator Chatbot - Pure JavaScript Version
// No Python or server needed!

const knowledgeBase = {
    "questions": [
        {
            "question": "where is the library",
            "answer": "📍 The library is located in the middle of the campus, next to the cafeteria."
        },
        {
            "question": "how to go to fci",
            "answer": "🏫 FCI (Faculty of Computing and Informatics) is located at the north wing. Take the main corridor, go past the library, and follow the signs to FCI."
        },
        {
            "question": "where is the cafeteria",
            "answer": "🍽️ The main cafeteria is near the library on the ground floor. There's also a food court near FCI."
        },
        {
            "question": "where is the surau",
            "answer": "🕌 The surau (prayer room) is located near the library, on the first floor."
        },
        {
            "question": "where is the gym",
            "answer": "💪 The gym is located at the sports complex, behind the main building."
        },
        {
            "question": "where is the clinic",
            "answer": "🏥 The university clinic is on the ground floor of the student services building."
        },
        {
            "question": "what is your name",
            "answer": "🤖 I'm MMU Navigator Bot! I'm here to help you find your way around MMU campus."
        },
        {
            "question": "what can you do",
            "answer": "I can help you find locations around MMU campus like the library, FCI, cafeteria, surau, gym, and more! Just ask me 'Where is the library?' or 'How to go to FCI?'"
        },
        {
            "question": "help",
            "answer": "Here are some things you can ask me:\n• Where is the library?\n• How to go to FCI?\n• Where is the cafeteria?\n• Where is the surau?\n• Where is the gym?"
        }
    ]
};

function findBestMatch(userQuestion, questions) {
    userQuestion = userQuestion.toLowerCase().trim();
    
    // Remove punctuation
    userQuestion = userQuestion.replace(/[^\w\s]/g, '');
    
    // Exact match
    for (let q of questions) {
        if (q.toLowerCase() === userQuestion) {
            return q;
        }
    }
    
    // Contains match
    for (let q of questions) {
        if (userQuestion.includes(q.toLowerCase()) || q.toLowerCase().includes(userQuestion)) {
            return q;
        }
    }
    
    // Word match scoring
    let bestMatch = null;
    let highestScore = 0;
    const userWords = userQuestion.split(' ');
    
    for (let q of questions) {
        let score = 0;
        const qWords = q.toLowerCase().split(' ');
        
        for (let userWord of userWords) {
            for (let qWord of qWords) {
                if (userWord === qWord) {
                    score += 3;
                } else if (userWord.length > 3 && qWord.includes(userWord)) {
                    score += 2;
                } else if (qWord.includes(userWord) && userWord.length > 2) {
                    score += 1;
                }
            }
        }
        
        if (score > highestScore && score > 0) {
            highestScore = score;
            bestMatch = q;
        }
    }
    
    return bestMatch;
}

function getAnswer(question) {
    const found = knowledgeBase.questions.find(q => q.question.toLowerCase() === question.toLowerCase());
    return found ? found.answer : null;
}

function addMessage(message, isUser) {
    const chatContainer = document.getElementById('chatMessages');
    if (!chatContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = isUser ? 'user-msg' : 'bot-msg';
    messageDiv.style.whiteSpace = 'pre-line';
    messageDiv.style.margin = '8px';
    messageDiv.style.padding = '10px';
    messageDiv.style.borderRadius = '10px';
    messageDiv.style.maxWidth = '80%';
    
    if (isUser) {
        messageDiv.style.backgroundColor = '#007bff';
        messageDiv.style.color = 'white';
        messageDiv.style.alignSelf = 'flex-end';
        messageDiv.style.marginLeft = 'auto';
    } else {
        messageDiv.style.backgroundColor = '#e9ecef';
        messageDiv.style.color = 'black';
        messageDiv.style.alignSelf = 'flex-start';
    }
    
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTyping() {
    const chatContainer = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typingIndicator';
    typingDiv.className = 'bot-msg';
    typingDiv.textContent = '🤖 Typing...';
    typingDiv.style.padding = '10px';
    typingDiv.style.margin = '8px';
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTyping() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

async function handleUserInput() {
    const inputElement = document.getElementById('userInput');
    const message = inputElement.value.trim();
    
    if (!message) return;
    
    addMessage(message, true);
    inputElement.value = '';
    
    showTyping();
    
    // Simulate thinking time
    setTimeout(() => {
        removeTyping();
        
        const allQuestions = knowledgeBase.questions.map(q => q.question);
        const bestMatch = findBestMatch(message, allQuestions);
        
        if (bestMatch) {
            const answer = getAnswer(bestMatch);
            if (bestMatch.toLowerCase() !== message.toLowerCase()) {
                addMessage(`🤔 Did you mean "${bestMatch}"?\n\n${answer}`, false);
            } else {
                addMessage(answer, false);
            }
        } else {
            addMessage("❓ I don't know the answer to that yet.\n\n💡 Try asking me about:\n• Library\n• FCI\n• Cafeteria\n• Surau\n• Gym\n\nOr type 'help' for more options!", false);
        }
    }, 500);
}

function fillChat(text) {
    const inputElement = document.getElementById('userInput');
    if (inputElement) {
        inputElement.value = text;
        handleUserInput();
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    const inputElement = document.getElementById('userInput');
    if (inputElement) {
        inputElement.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleUserInput();
            }
        });
    }
    
    // Add welcome message if chat is empty
    const chatContainer = document.getElementById('chatMessages');
    if (chatContainer && chatContainer.children.length === 0) {
        addMessage("Hello! How can I help you navigate MMU today?", false);
    }
});

// Make functions global for onclick handlers
window.fillChat = fillChat;
window.handleUserInput = handleUserInput;