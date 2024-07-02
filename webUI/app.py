import sys
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import asyncio
import json

# Add the FetchingAnalysis directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'FetchingAnalysis'))

# Make sure that the SSL_CERT_FILE environment variable is set
# nano ~/.zshrc
# export SSL_CERT_FILE=/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/certifi/cacert.pem

import articleAnalysis  # Now we can import articleAnalysis

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    return render_template('results.html')

@socketio.on('start_analysis')
def handle_start_analysis(data):
    keyword = data['keyword']
    start_date = data['start_date']
    end_date = data['end_date']

    # Run the article analysis asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(articleAnalysis.main(keyword, start_date, end_date))

    emit('analysis_complete', {'results': results})

if __name__ == '__main__':
    socketio.run(app, debug=True)
