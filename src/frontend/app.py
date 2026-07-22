from flask import Flask, render_template

# 같은 폴더 내의 templates 디렉터리를 인식하도록 설정합니다.
app = Flask(__name__, template_folder="templates")

# 1. 홈 화면
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

# 2. 내 포트폴리오 입력
@app.route("/portfolio/input")
def portfolio_input():
    return render_template("portfolio_input.html")

# 3. 포트폴리오 관리 (수정)
@app.route("/portfolio/edit")
def portfolio_edit():
    return render_template("portfolio_edit.html")

# 4. 포트폴리오 요약
@app.route("/portfolio/summary")
def portfolio_summary():
    return render_template("portfolio_summary.html")

# 5. 진단 결과
@app.route("/diagnosis/result")
def diagnosis_result():
    return render_template("diagnosis_result.html")

# 6. 이슈 분석
@app.route("/issue/analysis")
def issue_analysis():
    return render_template("issue_analysis.html")

if __name__ == "__main__":
    # 개발용 서버 실행 (포트 5000)
    app.run(debug=True, port=5000)