from flask import Flask
app = Flask(__name__)
@app.route("/")
def hello():
    return "Hello, you're now in the item catalog folder."
if __name__ == "__main__":
    app.run()
