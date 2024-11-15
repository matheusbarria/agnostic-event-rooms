TRIVIA_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Trivia Game</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f0f0f0;
            text-align: center;
        }}
        .question-box {{
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        .question-text {{
            font-size: 24px;
            color: #333;
            margin-bottom: 20px;
        }}
        .options-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }}
        .option-button {{
            background-color: #4CAF50;
            color: white;
            padding: 15px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }}
        .option-button:hover {{
            background-color: #45a049;
        }}
        .score-board {{
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        .score-title {{
            font-size: 20px;
            color: #333;
            margin-bottom: 10px;
        }}
        .player-score {{
            font-size: 16px;
            color: #666;
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="score-board">
        <div class="score-title">Scores</div>
        {scores}
    </div>
    
    <div class="question-box">
        <div class="question-text">{question}</div>
        <div class="options-container">
            {options}
        </div>
    </div>

    <script>
        function sendAnswer(answerIndex) {{
            let data = {{
                "answer": answerIndex
            }};
            fetch(window.location.href, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.correct) {{
                    alert('Correct!');
                }} else {{
                    alert('Incorrect!');
                }}
                // Reload to show next question
                location.reload();
            }})
            .catch(error => {{
                console.error('Error:', error);
                alert('Error submitting answer. Please try again.');
            }});
        }}
    </script>
</body>
</html>
'''