from flask import Flask, render_template, request, redirect, url_for, make_response
import time
from multiprocessing import Process

app = Flask(__name__)

spic_status = {
    'logged_in': False,
    'messages' : []
}


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/status", methods=["GET", "POST"])
def status():
    return render_template("status.html")

@app.route("/update", methods=["POST"])
def update():
    pass

@app.route("/status/auth", methods=["GET"])
def soap_auth_status():
    response = make_response('Logged in' if spic_status['logged_in'] else 'Not logged in', 200)
    return response

#test  
def main_loop() -> None:
    with open("./output2.txt", "w") as f:
        while True:
            time.sleep(1)
            print("test", file=f)
        pass


if __name__ == "__main__":
    p = Process(target=main_loop)
    p.start() 
    app.run()
    p.join()
        