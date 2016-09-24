#!/bin/bash
set -x
set -e
repo=$1
name=$2
revision=$3

#TODO check parameters

tmp=$(mktemp -d)
function finish (){
  rm -rf ${tmp}
}
trap finish EXIT

cd ${tmp}
git clone ${repo}
cd ${name}
git checkout ${revision}

docker build -f Dockerfile -t diabol/event-based-cd-example:latest .
docker_repo=944159926332.dkr.ecr.eu-west-1.amazonaws.com/event-based-cd-example:latest
docker tag diabol/event-based-cd-example:latest ${docker_repo}

eval $(aws ecr get-login)
docker push ${docker_repo}
