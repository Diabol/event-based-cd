
from flask import Flask
from flask import request
import pprint
import json
import subprocess


app = Flask(__name__)

@app.route("/")
def hello():
    return "Event Based CD Engine - Adaptors"

@app.route("/deploy_test", methods=['POST'])
def deploy_test():
    pprint.pprint(request.data)
    jdata = json.loads(request.data)
    if jdata['Subject'] == 'build_image':
        msg = json.loads(jdata['Message'])
        if msg['status'] == "ok":
            deploy_and_test(msg['image'])

        return "OK"

    return ""


def deploy_and_test(image):
    subprocess.call(["docker", "stop", "event-based-cd-example-test"])
    subprocess.call(["docker", "rm", "event-based-cd-example-test"])
    subprocess.call(["docker", "pull", image])

    if subprocess.call(["docker", "run", "-d", "-p", "8080:5000", "--name",
        "event-based-cd-example-test", "-e", "PROVIDER=Test", image]) == 0:
        print "Test OK"
        # Send SNS OK
    else:
        print "Test Fail"
        # Send SNS Fail

if __name__ == "__main__":
    app.run(host='0.0.0.0')

