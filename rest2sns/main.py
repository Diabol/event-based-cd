from flask import Flask
from flask import request
import json
import subprocess
import boto3
import pprint
import datetime
import time

sns_topic_arn = 'arn:aws:sns:eu-west-1:944159926332:cdevent'
sns_client = boto3.client('sns')
app = Flask(__name__)


@app.route("/")
def hello():
    return "Event Based CD Engine - Adaptors"


@app.route("/notifications", methods=['POST'])
def notifications():
    #print request.data
    jdata = json.loads(request.data)
    msg = json.loads(jdata['Message'])
    #pprint.pprint(msg) 
    if jdata.has_key('Subject'):
        if jdata['Subject'] == 'built_image':
            print '\n########Received built_image event.\n'
            if msg['status'] == "ok":
                deploy_and_test(msg['image'], msg['source'], msg['source_revision'])
            return "OK"
        elif jdata['Subject'] == "verified_test":
            print '\n#######Received verified_test event\n'
            if msg['status'] == "ok":
                deploy_prod(msg['image'], msg['source'], msg['source_revision'])
            return "OK"
    try:
        if jdata['MessageAttributes']['X-Github-Event']['Value'] == 'push':
	    print '\n#######Received git push event'
	    print '#######Building docker image\n'
	    source = msg['repository']['url']
            name = msg['repository']['name']
	    source_revision = msg['after']
            if build(source, name, source_revision) == 0:
                image = '944159926332.dkr.ecr.eu-west-1.amazonaws.com/event-based-cd-example:latest'
	        built_image_msg = create_msg('ok', image, source, source_revision)
                sns_client.publish(TopicArn=sns_topic_arn, Subject='built_image', MessageStructure='string', Message=json.dumps(built_image_msg))
                return "OK"
    except Exception as e:
        print e
	       

    print 'Received event, no handling rules. Message data is: \n' + request.data

    return "OK"

def build(source, name,  source_revision):
    print 'building image'
    return subprocess.call(['./build.sh', source, name,  source_revision])


def deploy_and_test(image, src, rev):
    print '#######deploying to test'
    stop_remove_container('test')

    if deploy_container('test', image, rev) == 0:
        verified_test_msg = create_msg('ok', image, src, rev)
        sns_client.publish(TopicArn=sns_topic_arn, Subject='verified_test', MessageStructure='string', Message=json.dumps(verified_test_msg))
        print "#######Test OK"
        print "Sending verified_test event"
    else:
        print "Test Fail"
        # Send SNS Fail


def deploy_prod(image, src, rev):
    env = 'prod'
    print '#######deploying to '+env
    stop_remove_container(env)
    if deploy_container(env, image, rev) == 0:
        print '#######Prod OK'
        verified_prod_msg = create_msg('ok', image, src, rev)
        sns_client.publish(TopicArn=sns_topic_arn, Subject='verified_prod', MessageStructure='string', Message=json.dumps(verified_prod_msg))
    else:
        print 'Prod Failed'


def stop_remove_container(env):
    time.sleep(10)
    name = 'event-based-cd-example-' + env.lower()
    print 'stoping and removing ' + name
    subprocess.call(["docker", "stop", name])
    subprocess.call(["docker", "rm", name])
    print 'stopped and removed ' + name


def deploy_container(env, image, rev):
    print 'pulling latest image'
    subprocess.call(["docker", "pull", image])
    if env.lower() == 'prod':
        port = '80'
    else:
        port = '8080'
    print 'Start container for env: ' + env
    deployed_time = str(datetime.datetime.now())
    return subprocess.call(["docker", "run", "-d", "-p", port + ":5000", 
	"--name", "event-based-cd-example-"+env.lower(), 
	"-e", "ENV="+env, 
	"-e", "DEPLOYED_TIME=UTC " + deployed_time,
	"-e", "DEPLOYED_REVISION=" + rev,
	image])


def create_msg(status, image, src, rev):
    msg = {}
    msg['status'] = status
    msg['source'] = src
    msg['source_revision'] = rev
    msg['image'] = image
    return msg


if __name__ == "__main__":
    app.run(host='0.0.0.0')
