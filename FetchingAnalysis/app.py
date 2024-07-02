from flask import Flask, request, render_template
import asyncio
import articleAnalysis

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results', methods=['POST'])
def results():
    keyword = request.form['keyword']
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    # Run the article analysis asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(articleAnalysis.main(keyword, start_date, end_date))

    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
