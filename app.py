from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import time
import random
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Ensure leaderboard file exists
LEADERBOARD_FILE = 'leaderboard.json'

def load_leaderboard():
    """Load leaderboard from JSON file"""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_leaderboard(leaderboard):
    """Save leaderboard to JSON file"""
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f, indent=4)

def generate_test_cases():
    """Generate random test cases for all three endpoints"""
    # Test cases for analyze-mood endpoint
    mood_cases = {
        "happy": [
            "I feel amazing today!",
            "I'm so excited about this weekend",
            "What a wonderful surprise, I'm thrilled!",
            "This is the best day ever",
            "I'm feeling incredibly joyful right now"
        ],
        "sad": [
            "I'm feeling down today",
            "This news has made me very unhappy",
            "I can't stop crying about what happened",
            "Everything seems so depressing lately",
            "I'm really disappointed with the outcome"
        ],
        "angry": [
            "This is absolutely infuriating",
            "I'm so mad I could scream",
            "Why does this always happen to me?!",
            "They completely disrespected me",
            "I can't believe how frustrating this is"
        ],
        "neutral": [
            "The sky is blue today",
            "I'm going to the store later",
            "The meeting is scheduled for 3pm",
            "The book has 250 pages",
            "The car is parked outside"
        ]
    }
    
    # Test cases for detect-crisis endpoint
    crisis_cases = {
        True: [
            "I'm feeling hopeless and might hurt myself",
            "I don't see any reason to continue living",
            "Everyone would be better off without me",
            "I've been thinking about ending it all",
            "I can't take this pain anymore, I want to die"
        ],
        False: [
            "I had a bad day but tomorrow will be better",
            "This homework is really difficult",
            "My friend didn't respond to my text",
            "The traffic was terrible this morning",
            "I spilled coffee on my new shirt"
        ]
    }
    
    # Test cases for summarize endpoint
    summarize_cases = [
        "Climate change is the long-term alteration in Earth's climate and weather patterns. It is caused by human activities, particularly the burning of fossil fuels, which leads to increased levels of greenhouse gases in the atmosphere. These gases trap heat, causing global warming. The effects of climate change include rising sea levels, extreme weather events, loss of biodiversity, and threats to food security.",
        "Artificial intelligence refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. It encompasses various technologies like machine learning, natural language processing, and computer vision. AI systems can analyze data, recognize patterns, make decisions, and improve over time based on experience. While AI offers numerous benefits in healthcare, transportation, and many other fields, it also raises concerns about privacy, security, and potential job displacement.",
        "The history of space exploration began in the mid-20th century, with the Soviet Union launching the first artificial satellite, Sputnik 1, in 1957. This was followed by the first human in space, Yuri Gagarin, in 1961. The United States responded with the Apollo program, landing Neil Armstrong and Buzz Aldrin on the Moon in 1969. Since then, numerous countries have sent probes to explore the planets, and the International Space Station has been continuously occupied since 2000, representing a global collaboration in space research.",
        "The internet evolved from ARPANET, a network created by the U.S. Department of Defense in the 1960s. It gained popularity in the 1990s with the creation of the World Wide Web. Today, the internet connects billions of devices worldwide, facilitating information sharing, communication, commerce, entertainment, and social networking. It has revolutionized how we work, learn, and interact with each other.",
        "Renewable energy sources, such as solar, wind, hydroelectric, and geothermal power, are derived from naturally replenishing resources. Unlike fossil fuels, they produce minimal greenhouse gas emissions and have a smaller environmental impact. The adoption of renewable energy is growing globally as technology improves and costs decrease, playing a crucial role in addressing climate change and creating a sustainable energy future."
    ]
    
    # Randomly select test cases for each endpoint
    selected_mood_cases = []
    for emotion, texts in mood_cases.items():
        selected_texts = random.sample(texts, min(2, len(texts)))
        for text in selected_texts:
            selected_mood_cases.append((text, emotion))
    
    selected_crisis_cases = []
    for is_crisis, texts in crisis_cases.items():
        selected_texts = random.sample(texts, min(2, len(texts)))
        for text in selected_texts:
            selected_crisis_cases.append((text, is_crisis))
    
    selected_summarize_cases = random.sample(summarize_cases, min(3, len(summarize_cases)))
    
    return {
        "analyze-mood": selected_mood_cases,
        "detect-crisis": selected_crisis_cases,
        "summarize": selected_summarize_cases
    }

def test_endpoint(base_url, num_tests=5):
    """Test all three API endpoints multiple times with random test cases"""
    total_score = 0
    all_results = []
    test_logs = []
    
    # Ensure base_url ends with a slash
    if not base_url.endswith('/'):
        base_url += '/'
    
    endpoints = ["analyze-mood", "detect-crisis", "summarize"]
    
    for test_round in range(1, num_tests + 1):
        test_cases = generate_test_cases()
        round_score = 0
        correct_predictions = 0
        fast_responses = 0
        total_tests = 0
        round_logs = []
        
        try:
            # Test analyze-mood endpoint
            for i, (text, expected_emotion) in enumerate(test_cases["analyze-mood"], 1):
                start = time.time()
                try:
                    url = base_url + "analyze-mood"
                    r = requests.post(url, json={"text": text}, timeout=10)
                    latency = time.time() - start
                    
                    log_entry = {
                        'endpoint': 'analyze-mood',
                        'test_num': i,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'expected': expected_emotion,
                        'latency': round(latency, 2)
                    }
                    total_tests += 1
                    
                    if r.status_code != 200:
                        log_entry['status'] = 'ERROR'
                        log_entry['error'] = f'Status: {r.status_code}'
                        round_logs.append(log_entry)
                        continue
                    
                    data = r.json()
                    predicted = data.get("emotion")
                    log_entry['predicted'] = predicted
                    
                    # Points for correct prediction
                    if predicted == expected_emotion:
                        round_score += 3
                        correct_predictions += 1
                        log_entry['status'] = 'CORRECT'
                    else:
                        log_entry['status'] = 'INCORRECT'
                    
                    # Bonus points for fast response
                    if latency < 1.0:
                        round_score += 2
                        fast_responses += 1
                        log_entry['speed_bonus'] = 'FAST'
                    elif latency < 2.0:
                        round_score += 1
                        log_entry['speed_bonus'] = 'MEDIUM'
                    
                    round_logs.append(log_entry)
                    
                except requests.exceptions.RequestException as e:
                    log_entry = {
                        'endpoint': 'analyze-mood',
                        'test_num': i,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'expected': expected_emotion,
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    round_logs.append(log_entry)
            
            # Test detect-crisis endpoint
            for i, (text, expected_crisis) in enumerate(test_cases["detect-crisis"], 1):
                start = time.time()
                try:
                    url = base_url + "detect-crisis"
                    r = requests.post(url, json={"text": text}, timeout=10)
                    latency = time.time() - start
                    
                    log_entry = {
                        'endpoint': 'detect-crisis',
                        'test_num': i,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'expected': expected_crisis,
                        'latency': round(latency, 2)
                    }
                    total_tests += 1
                    
                    if r.status_code != 200:
                        log_entry['status'] = 'ERROR'
                        log_entry['error'] = f'Status: {r.status_code}'
                        round_logs.append(log_entry)
                        continue
                    
                    data = r.json()
                    predicted = data.get("crisis_detected")
                    log_entry['predicted'] = predicted
                    
                    # Points for correct prediction
                    if predicted == expected_crisis:
                        round_score += 3
                        correct_predictions += 1
                        log_entry['status'] = 'CORRECT'
                    else:
                        log_entry['status'] = 'INCORRECT'
                    
                    # Bonus points for fast response
                    if latency < 1.0:
                        round_score += 2
                        fast_responses += 1
                        log_entry['speed_bonus'] = 'FAST'
                    elif latency < 2.0:
                        round_score += 1
                        log_entry['speed_bonus'] = 'MEDIUM'
                    
                    round_logs.append(log_entry)
                    
                except requests.exceptions.RequestException as e:
                    log_entry = {
                        'endpoint': 'detect-crisis',
                        'test_num': i,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'expected': expected_crisis,
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    round_logs.append(log_entry)
            
            # Test summarize endpoint
            for i, text in enumerate(test_cases["summarize"], 1):
                start = time.time()
                try:
                    url = base_url + "summarize"
                    r = requests.post(url, json={"text": text}, timeout=15)  # Longer timeout for summarization
                    latency = time.time() - start
                    
                    log_entry = {
                        'endpoint': 'summarize',
                        'test_num': i,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'latency': round(latency, 2)
                    }
                    total_tests += 1
                    
                    if r.status_code != 200:
                        log_entry['status'] = 'ERROR'
                        log_entry['error'] = f'Status: {r.status_code}'
                        round_logs.append(log_entry)
                        continue
                    
                    data = r.json()
                    summary = data.get("summary")
                    log_entry['summary'] = summary[:100] + '...' if summary and len(summary) > 100 else summary
                    
                    # For summary, we check if it's not empty and shorter than original text
                    if summary and len(summary) < len(text) * 0.8:
                        round_score += 3
                        correct_predictions += 1
                        log_entry['status'] = 'GOOD'
                    else:
                        log_entry['status'] = 'INADEQUATE'
                    
                    # Bonus points for fast response (higher threshold for summarization)
                    if latency < 2.0:
                        round_score += 2
                        fast_responses += 1
                        log_entry['speed_bonus'] = 'FAST'
                    elif latency < 4.0:
                        round_score += 1
                        log_entry['speed_bonus'] = 'MEDIUM'
                    
                    round_logs.append(log_entry)
                    
                except requests.exceptions.RequestException as e:
                    log_entry = {
                        'endpoint': 'summarize',
                        'test_num': i,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    round_logs.append(log_entry)
                    
        except Exception as e:
            round_logs.append({'error': f'Round {test_round} failed: {str(e)}'})
        
        total_score += round_score
        all_results.append({
            'round': test_round,
            'score': round_score,
            'correct': correct_predictions,
            'total_tests': total_tests,
            'fast_responses': fast_responses
        })
        test_logs.append({
            'round': test_round,
            'logs': round_logs,
            'score': round_score
        })
    
    return total_score, all_results, test_logs

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test', methods=['POST'])
def test_api():
    user_name = request.form.get('user_name', '').strip()
    api_url = request.form.get('api_url', '').strip()
    api_name = request.form.get('api_name', 'User API').strip()

    if not user_name or not api_url:
        flash('Please provide both your name and API URL', 'error')
        return redirect(url_for('index'))

    if not api_url.startswith(('http://', 'https://')):
        flash('Invalid URL format. Please include http:// or https://', 'error')
        return redirect(url_for('index'))

    # Test the API
    num_test_rounds = random.randint(3, 7)
    total_score, detailed_results, test_logs = test_endpoint(api_url, num_test_rounds)

    # Calculate statistics
    avg_score_per_round = total_score / num_test_rounds if num_test_rounds > 0 else 0
    total_correct = sum(r['correct'] for r in detailed_results)
    total_tests = sum(r['total_tests'] for r in detailed_results)
    accuracy = (total_correct / total_tests * 100) if total_tests > 0 else 0
    total_fast = sum(r['fast_responses'] for r in detailed_results)

    # Performance rating
    if accuracy >= 90:
        rating = "🏆 EXCELLENT"
    elif accuracy >= 75:
        rating = "🥈 GOOD"
    elif accuracy >= 60:
        rating = "🥉 FAIR"
    else:
        rating = "❌ NEEDS IMPROVEMENT"

    # Create results dictionary
    results = {
        'total_score': total_score,
        'rounds_tested': num_test_rounds,
        'avg_score': round(avg_score_per_round, 1),
        'accuracy': round(accuracy, 1),
        'total_correct': total_correct,
        'total_tests': total_tests,
        'fast_responses': total_fast,
        'rating': rating,
        'timestamp': datetime.now().isoformat()
    }

    # Save to leaderboard
    leaderboard = load_leaderboard()
    leaderboard.append({
        'user': user_name,
        'api_name': api_name,
        'results': results,
        'test_logs': test_logs
    })
    save_leaderboard(leaderboard)

    return render_template('results.html', 
                         user_name=user_name,
                         api_name=api_name,
                         results=results,
                         test_logs=test_logs)

@app.route('/leaderboard')
def leaderboard():
    leaderboard_data = load_leaderboard()
    # Sort by total score descending
    leaderboard_data.sort(key=lambda x: x['results']['total_score'], reverse=True)
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

@app.route('/api/leaderboard')
def api_leaderboard():
    """API endpoint to get leaderboard data"""
    leaderboard_data = load_leaderboard()
    leaderboard_data.sort(key=lambda x: x['results']['total_score'], reverse=True)
    return jsonify(leaderboard_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)