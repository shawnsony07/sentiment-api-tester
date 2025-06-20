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
    """Generate random test cases for sentiment analysis"""
    positive_texts = [
        "I love my life",
        "This is absolutely amazing",
        "I'm so happy and excited",
        "What a wonderful day",
        "I feel fantastic today",
        "This brings me so much joy",
        "I'm grateful for everything",
        "Life is beautiful",
        "I'm having the best time ever",
        "This made my day perfect"
    ]

    negative_texts = [
        "I am very sad and disappointed",
        "This is terrible and awful",
        "I hate everything about this",
        "I'm feeling really depressed",
        "This ruined my entire day",
        "I'm so angry and frustrated",
        "This is the worst thing ever",
        "I feel completely hopeless",
        "I'm devastated by this news",
        "This makes me extremely upset"
    ]

    neutral_texts = [
        "It is an ordinary day",
        "The weather is cloudy today",
        "I need to go to the store",
        "The meeting is at 3 PM",
        "I have work tomorrow",
        "The book has 300 pages",
        "The train arrives at noon",
        "I'm wearing a blue shirt",
        "The temperature is 25 degrees",
        "There are five items on the list"
    ]

    # Randomly select test cases
    test_cases = []
    test_cases.extend(random.sample(positive_texts, random.randint(2, 4)))
    test_cases.extend(random.sample(negative_texts, random.randint(2, 4)))
    test_cases.extend(random.sample(neutral_texts, random.randint(2, 4)))

    # Create tuples with expected sentiments
    final_cases = []
    for text in test_cases:
        if text in positive_texts:
            final_cases.append((text, "positive"))
        elif text in negative_texts:
            final_cases.append((text, "negative"))
        else:
            final_cases.append((text, "neutral"))

    # Shuffle the order
    random.shuffle(final_cases)
    return final_cases

def test_endpoint(api_url, num_tests=5):
    """Test an API endpoint multiple times with random test cases"""
    total_score = 0
    all_results = []
    test_logs = []

    for test_round in range(1, num_tests + 1):
        test_cases = generate_test_cases()
        round_score = 0
        correct_predictions = 0
        fast_responses = 0
        round_logs = []

        try:
            for i, (text, expected_sentiment) in enumerate(test_cases, 1):
                start = time.time()
                try:
                    r = requests.get(api_url, params={"text": text}, timeout=10)
                    latency = time.time() - start

                    log_entry = {
                        'test_num': i,
                        'text': text[:50] + '...' if len(text) > 50 else text,
                        'expected': expected_sentiment,
                        'latency': round(latency, 2)
                    }

                    if r.status_code != 200:
                        log_entry['status'] = 'ERROR'
                        log_entry['error'] = f'Status: {r.status_code}'
                        round_logs.append(log_entry)
                        continue

                    data = r.json()
                    predicted = data.get("sentiment")
                    log_entry['predicted'] = predicted

                    # Points for correct prediction
                    if predicted == expected_sentiment:
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
                    log_entry['status'] = 'ERROR'
                    log_entry['error'] = str(e)
                    round_logs.append(log_entry)

        except Exception as e:
            round_logs.append({'error': f'Round {test_round} failed: {str(e)}'})

        total_score += round_score
        all_results.append({
            'round': test_round,
            'score': round_score,
            'correct': correct_predictions,
            'total_tests': len(test_cases),
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