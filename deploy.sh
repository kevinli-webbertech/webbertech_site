#!/bin/bash

scp -i ./webbertech.com.pem index.html ubuntu@ec2-3-19-83-70.us-east-2.compute.amazonaws.com:/var/www/html/index.html

scp -i ./webbertech.com.pem -r ./css/ ./js/ ./images/  ubuntu@ec2-3-19-83-70.us-east-2.compute.amazonaws.com:/var/www/html/

ssh -i ./webbertech.com.pem ubuntu@ec2-3-19-83-70.us-east-2.compute.amazonaws.com

