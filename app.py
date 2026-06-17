from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>RMETI Student Portal is working!</h1><p>Deployment successful.</p>"

if __name__ == "__main__":
    app.run()
