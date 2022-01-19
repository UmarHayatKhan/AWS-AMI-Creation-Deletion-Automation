import boto3
import collections
import datetime
import time
import sys

ec = boto3.client("ec2")
ec2 = boto3.resource("ec2")

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
    print("Found %d instances that need evaluated" % len(instances))

    to_tag = collections.defaultdict(list)

    date = datetime.datetime.now()
    date_fmt = date.strftime("%Y-%m-%d")
    
    imagesList = []
    backupSuccess = False
    imagecount = 0
    
    for instance in instances:
        images = ec2.images.filter(Owners=["self"],Filters=[{"Name":"tag-value","Values":[instance["InstanceId"]]}])
        for image in images:
            print(image)
            if image.name.startswith("Lambda - " + instance["InstanceId"]):
                imagecount = imagecount + 1
                try:
                    if image.tags is not None:
                        deletion_date = [
                            t.get("Value") for t in image.tags
                            if t["Key"] == "DeleteOn"][0]
                        delete_date = datetime.datetime.strptime(deletion_date, "%m-%d-%Y %H:%M:%S")
                        delete_date = delete_date.strftime("%m-%d-%Y %H:%M:%S")
                        print(delete_date)
                except IndexError:
                    deletion_date = False
                    delete_date = False

                delete_time = datetime.datetime.now() - datetime.timedelta(hours=6) 
                delete_time = delete_time.strftime("%m-%d-%Y %H:%M:%S")
                print(delete_time)
                #today_date = time.strptime(today_time, "%m-%d-%Y")

                if delete_date <= delete_time:
                    imagesList.append(image.id)
                    print(imagesList)

                if date_fmt in image.name:#if image.name.endswith(date_fmt):
                    backupSuccess = True
                    print("Latest backup from " + date_fmt + " was a success")
                else:
                    print("Today Backup not done yet")
        if(imagecount >= 75):
            break
        print("instance " + instance["InstanceId"] + " has " + str(imagecount) + " AMIs")


        if backupSuccess == True:

            myAccount = boto3.client("sts").get_caller_identity()["Account"]
            snapshots = ec.describe_snapshots(MaxResults=1000, OwnerIds=[myAccount])["Snapshots"]

            imgcount=0
            for image in imagesList:
                imgcount=imgcount+1
                print("deregistering image %s" % image)
                amiResponse = ec.deregister_image(
                    DryRun=False,
                    ImageId=image,
                )
                print(amiResponse)

                for snapshot in snapshots:
                    if snapshot["Description"].find(image) > 0:
                        snap = ec.delete_snapshot(SnapshotId=snapshot["SnapshotId"])
                        print("Deleting snapshot " + snapshot["SnapshotId"])

                if(imgcount>=75):
                    break

        else:
            print("No current backup found. Termination suspended.")