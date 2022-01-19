import boto3
import collections
import datetime
import sys
import pprint
import json
from dateutil import parser
import time



ec = boto3.client("ec2")
ec2 = boto3.resource("ec2")

def newest_image(list_of_images):
    latest = None
    for image in list_of_images:

        if not latest:
            latest = image
            continue

        if parser.parse(image["CreationDate"]) > parser.parse(latest["CreationDate"]):
            latest = image

    return latest

def lambda_handler(event, context):
    
    message = json.loads(event["Records"][0]["Sns"]["Message"])
    instance_id = message["Trigger"]["Dimensions"][0]["value"]
    images = ec.describe_images(Owners=["self"],Filters=[{"Name":"tag-value","Values":[instance_id]}, {"Name": "state", "Values": ["available"]}])
    latest_image = newest_image(images["Images"])
    response = ec.run_instances(
        ImageId=latest_image["ImageId"],
        NetworkInterfaces=[
            {
            "DeviceIndex": 0,
            "PrivateIpAddress": [
                    t.get("Value") for t in latest_image["Tags"]
                    if t["Key"] == "privateip"][0],
            },
        ],
        
        MaxCount=1,
        MinCount=1,
        LaunchTemplate={
            "LaunchTemplateId": [
                    t.get("Value") for t in latest_image["Tags"]
                    if t["Key"] == "LaunchTemplateId"][0],
        },
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {
                        "Key": "Name", 
                        "Value": [
                        t.get("Value") for t in latest_image["Tags"]
                        if t["Key"] == "Name"][0]
                    },
                    {
                        "Key": "ami-status", 
                        "Value": "backup",
                        
                    },
                    {
                        "Key": "LaunchTemplateId", 
                        "Value":[
                        t.get("Value") for t in latest_image["Tags"]
                        if t["Key"] == "LaunchTemplateId"][0]
                    },
                    {
                        "Key": "LaunchTemplateName", 
                        "Value": [
                        t.get("Value") for t in latest_image["Tags"]
                        if t["Key"] == "LaunchTemplateName"][0]
                    },
                    {
                        "Key": "privateip", 
                        "Value": [
                        t.get("Value") for t in latest_image["Tags"]
                        if t["Key"] == "privateip"][0]
                    },
                    
                    
                ]
            },
        ],
       
    )
    cloudwatch = boto3.client("cloudwatch")

    delete_response = cloudwatch.delete_alarms(
        AlarmNames=[
            instance_id + "Status_check_failed",
        ]
    )
    time.sleep(120) 

    cloudwatch.put_metric_alarm(
        AlarmName= response["Instances"][0]["InstanceId"] + "Status_check_failed",
        AlarmActions=[
            !Join [':',[arn:aws:sns, !Ref AWS::Region,!Ref AWS::AccountId,Launch-Fail-EC2-Trigger-Topic]],
            !Join [':',[arn:aws:automate, !Ref AWS::Region,ec2:terminate]],
        ], 
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        EvaluationPeriods=2,
        DatapointsToAlarm=2,
        MetricName="StatusCheckFailed",
        Namespace="AWS/EC2",
        Period=60,
        Statistic="Average",
        Threshold=1.0,
        ActionsEnabled=False,
        TreatMissingData= "breaching",
        Dimensions=[
            {
                "Name": "InstanceId", 
                "Value": response["Instances"][0]["InstanceId"],
            },
        ],
        Unit="Seconds"
    )

 
