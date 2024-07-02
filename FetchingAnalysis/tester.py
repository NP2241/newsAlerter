import subprocess

def main():
    keyword = "rangoon ruby"
    start_date = "20190101"
    end_date = "20190201"

    # Call articleAnalysis.py with the specified parameters
    subprocess.run(['python3', 'articleAnalysis.py', keyword, start_date, end_date])

if __name__ == "__main__":
    main()
