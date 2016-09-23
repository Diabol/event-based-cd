from flask import Flask
from flask import request
import json
import subprocess
import boto3

sns_topic_arn = 'arn:aws:sns:eu-west-1:944159926332:cdevent'
sns_client = boto3.client('sns')
app = Flask(__name__)


@app.route("/")
def hello():
    return "Event Based CD Engine - Adaptors"


@app.route("/notifications", methods=['POST'])
def notifications():
    jdata = json.loads(request.data)
    msg = json.loads(jdata['Message'])

    if jdata['Subject'] == 'built_image':
        if msg['status'] == "ok":
            deploy_and_test(msg['image'], msg['source'], msg['source_revision'])
        return "OK"
    elif jdata['Subject'] == "verified_test":
        print 'deploying to prod'
        if msg['status'] == "ok":
            deploy_prod(msg['image'], msg['source'], msg['source_revision'])
        return "OK"

    return ""


def deploy_and_test(image, src, rev):
    print 'deploying to test'
    stop_remove_container('test')

    if deploy_container('test', image) == 0:
        verified_test_msg = create_msg('ok', image, src, rev)
        sns_client.publish(TopicArn=sns_topic_arn, Subject='verified_test', MessageStructure='string', Message=json.dumps(verified_test_msg))
        print "Test OK"
        print "Sending verified_test event"
    else:
        print "Test Fail"
        # Send SNS Fail


def deploy_prod(image, src, rev):
    env = 'prod'
    print 'deploying to '+env
    stop_remove_container(env)
    if deploy_container(env, image) == 0:
        print 'Prod OK'
        verified_prod_msg = create_msg('ok', image, src, rev)
        sns_client.publish(TopicArn=sns_topic_arn, Subject='verified_prod', MessageStructure='string', Message=json.dumps(verified_prod_msg))
    else:
        print 'Prod Failed'


def stop_remove_container(env):
    name = 'event-based-cd-example-' + env.lower()
    print 'stoping and removing ' + name
    subprocess.call(["docker", "stop", name])
    subprocess.call(["docker", "rm", name])
    print 'stopped and removed ' + name


def deploy_container(env, image):
    print 'pulling latest image'
    subprocess.call(["docker", "pull", image])
    if env.lower() == 'prod':
        port = '80'
    else:
        port = '8080'
    print 'Start container for env: ' + env
    return subprocess.call(["docker", "run", "-d", "-p", port + ":5000", "--name", "event-based-cd-example-"+env.lower(), "-e", "PROVIDER="+env, image])


def create_msg(status, image, src, rev):
    msg = {}
    msg['status'] = status
    msg['source'] = src
    msg['source_revision'] = rev
    msg['image'] = image
    return msg


if __name__ == "__main__":
    app.run(host='0.0.0.0')
