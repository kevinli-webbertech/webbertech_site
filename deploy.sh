#!/bin/bash

scp -i ./webbertech.com.pem -r ./css/* ./js/* ubuntu@ec2-3-19-83-70.us-east-2.compute.amazonaws.com:/var/www/html
