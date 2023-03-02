from typing import Any, Dict

import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_stepfunctions as sfn
import aws_cdk.aws_stepfunctions_tasks as tasks
from aws_cdk import Duration, RemovalPolicy, Stack
from constructs import Construct


class MusabiStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)
        self.input_bucket = self.create_s3_bucket("Input")
        self.output_bucket = self.create_s3_bucket("Output")
        self.ecr_repository = self.create_ecr_repository()
        self.create_statemachine()

    def create_s3_bucket(self, bucket_prefix: str) -> Dict[str, Any]:
        params = {
            "removal_policy": RemovalPolicy.DESTROY,
            "auto_delete_objects": True,
            "block_public_access": s3.BlockPublicAccess.BLOCK_ALL,
            "bucket_key_enabled": False,
            "bucket_name": f"{bucket_prefix.lower()}-musabi-bot-bucket",
            "encryption": s3.BucketEncryption.S3_MANAGED,
            "object_ownership": s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            "public_read_access": False,
            "versioned": False,
        }
        return s3.Bucket(self, f"{bucket_prefix}MusabiBucket", **params)

    def create_ecr_repository(self) -> ecr.Repository:
        lifecycle_rule = ecr.LifecycleRule(
            description="Keep only one image.",
            max_image_count=1,
            rule_priority=1,
            tag_status=ecr.TagStatus.ANY,
        )
        return ecr.Repository(
            self,
            "MusabiRepository",
            repository_name="musabi-bot-repository",
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[lifecycle_rule],
            image_scan_on_push=False,
        )

    def create_statemachine(self):
        success_step = sfn.Succeed(self, "Succeded")
        preprocess_step = self._create_task()
        definition = preprocess_step.next(success_step)
        sfn.StateMachine(
            self,
            "MusabiStateMachine",
            state_machine_name="musabi-bot-statemachine",
            definition=definition,
            timeout=Duration.minutes(30),
            role=self._get_statemachine_role(),
        )

    def _create_task(self) -> sfn.CustomState:
        return sfn.CustomState(
            self,
            "SagemakerProcessingTask",
            state_json=self._create_processing_job_state(),
        )

    def _create_processing_job_state(self) -> Dict[str, Any]:
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createProcessingJob.sync",
            "Parameters": {
                "AppSpecification": {
                    "ImageUri": self.ecr_repository.repository_uri_for_tag("latest")
                },
                "Environment": {
                    "PROMPT.$": "$.Prompt",
                    "NEGATIVE_PROMPT.$": "$.NegativePrompt",
                    "WIDTH.$": "$.Width",
                    "HEIGHT.$": "$.Height",
                },
                "ProcessingJobName.$": (
                    "States.Format('PreprocessingJob-{}', $$.Execution.Name)"
                ),
                "ProcessingResources": {
                    "ClusterConfig": {
                        "InstanceCount": 1,
                        "InstanceType": "ml.g4dn.12xlarge",
                        "VolumeSizeInGB": 1,
                    }
                },
                "ProcessingInputs": [
                    {
                        "InputName": "PreprocessingJobInput",
                        "S3Input": {
                            "LocalPath": "/opt/ml/processing/input",
                            "S3CompressionType": "None",
                            "S3DataType": "S3Prefix",
                            "S3InputMode": "File",
                            "S3Uri": self.input_bucket.url_for_object(),
                        },
                    }
                ],
                "ProcessingOutputConfig": {
                    "Outputs": [
                        {
                            "OutputName": "PreprocessingJobOutput",
                            "S3Output": {
                                "LocalPath": "/opt/ml/processing/output",
                                "S3UploadMode": "EndOfJob",
                                "S3Uri.$": (
                                    f"States.Format('{self.output_bucket.s3_url_for_object()}/{{}}',"
                                    " $$.Execution.Name)"
                                ),
                            },
                        }
                    ],
                },
                "RoleArn": self._get_sagemaker_processing_job_role().role_arn,
                "StoppingCondition": {"MaxRuntimeInSeconds": 600},
            },
        }

    def _get_statemachine_role(self) -> iam.Role:
        return iam.Role(
            self,
            "MusabiStateMachineRole",
            assumed_by=iam.ServicePrincipal("states.ap-northeast-1.amazonaws.com"),
            inline_policies={
                "CreateSageMakerProcessingJobPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["sagemaker:CreateProcessingJob", "iam:PassRole"],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                    ]
                ),
                "CreateSageMakerProcessingJobSyncPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "sagemaker:DescribeProcessingJob",
                                "sagemaker:StopProcessingJob",
                                "sagemaker:ListTags",
                                "sagemaker:AddTags",
                                "events:PutTargets",
                                "events:PutRule",
                                "events:DescribeRule",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                    ]
                ),
            },
        )

    def _get_sagemaker_processing_job_role(self) -> iam.Role:
        # https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-roles.html#sagemaker-roles-createprocessingjob-perms
        return iam.Role(
            self,
            "SageMakerProcessingJobRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            inline_policies={
                "SageMakerProcessingJobPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "cloudwatch:PutMetricData",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:CreateLogGroup",
                                "logs:DescribeLogStreams",
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListBucket",
                                "ecr:GetAuthorizationToken",
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                    ]
                )
            },
        )
