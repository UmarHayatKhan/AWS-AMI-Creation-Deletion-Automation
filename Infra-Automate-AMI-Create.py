import boto3
import collections
import datetime
import sys
import pprint

ec = boto3.client("ec2")

def lambda_handler(event, context):
    
    reservations = ec.describe_instances(
        Filters=[
            {"Name": "tag-value", "Values": ["backup", "Backup"]},
        ]
    ).get(
        "Reservations", []
    )

    instances = sum(
        [
            [i for i in r["Instances"]]
            for r in reservations
        ], [])
    print(instances)

    print("Found %d instances that need backing up" % len(instances))

    for instance in instances:
        print(instance)
        try:
            retention_days = [
                int(t.get("Value")) for t in instance["Tags"]
                if t["Key"] == "Retention"][0]
        except IndexError:
            retention_days = 6

        create_time = datetime.datetime.now()
        create_fmt = create_time.strftime("%Y-%m-%d %H-%M-%S")
        
        AMIid = ec.create_image(InstanceId=instance["InstanceId"], Name="Lambda - " + instance["InstanceId"] + 
            " from " + create_fmt, Description="Infra-Lambda created AMI of instance " + instance["InstanceId"] +
            " from " + create_fmt, NoReboot=True, DryRun=False)
            
            
        delete_date = datetime.datetime.now() + datetime.timedelta(hours=retention_days)
        delete_fmt = delete_date.strftime("%m-%d-%Y %H:%M:%S")

        ec.create_tags(
            Resources=[
                AMIid["ImageId"],
                ],
            Tags=[
                {"Key": "Name", "Value": [
                    t.get("Value") for t in instance["Tags"]
                    if t["Key"] == "Name"][0]
                },
                {"Key": "InstanceId", "Value": instance["InstanceId"]},
                {"Key": "LaunchTemplateId", "Value":[
                    t.get("Value") for t in instance["Tags"]
                    if t["Key"] == "LaunchTemplateId"][0]
                },
                {"Key": "LaunchTemplateName", "Value": [
                    t.get("Value") for t in instance["Tags"]
                    if t["Key"] == "LaunchTemplateName"][0]
                },
                {"Key": "privateip", "Value": instance["PrivateIpAddress"]
                },
                {"Key": "DeleteOn", "Value": delete_fmt},
            ]
        )
                
 