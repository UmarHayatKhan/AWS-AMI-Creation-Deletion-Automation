# AWS-AMI-Creation-Deletion-Automation

This template will help you automate the AWS EC2 AMI automation. It can easily create AMI based on the time you set to create and will add the retention period to the tag of the AMI. After the retention period is over the Lambda will delete the AMI.

## Installation Instructions
 - Create an AWS account if you do not already have one and login.
 - Create EC2 instance if not already running.
 - Add "backup" tag to your Ec2 instnace/s that you want to schedule AMI automation.
 - Clone the repo onto your local development machine using git clone.

## Setup

To deploy this template, run in a terminal:
```bash
aws cloudformation create-stack --region <<Aws region>> \
                                --stack-name create-ami-automation-cfn \
                                --template-body file://./CreateLambdas.yaml\
                                --parameters  ParameterKey=AppName,ParameterValue=TestApp ParameterKey=OperatorEMail,ParameterValue=test@gmail.com ParameterKey=LambdaRate,ParameterValue=rate(1 hour)

```
Note that the template-body parameter must include the file:// prefix when run locally.

