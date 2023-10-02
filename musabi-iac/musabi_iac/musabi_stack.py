from typing import Any, Dict

import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as lambda_
import aws_cdk.aws_lambda_python_alpha as lambda_python
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
        self.generate_image_repository = self.create_ecr_repository(
            "GenerateImageRepository", "generate-image-repository"
        )
        self.generate_dish_function = self.create_generate_dish_lambda()
        self.publish_image_function = self.create_publish_image_lambda()
        self.state_machine = self.create_statemachine()
        self.create_event()

    def create_s3_bucket(self, bucket_prefix: str) -> s3.Bucket:
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

    def create_ecr_repository(self, id: str, name: str) -> ecr.Repository:
        lifecycle_rule = ecr.LifecycleRule(
            description="Keep only one image.",
            max_image_count=1,
            rule_priority=1,
            tag_status=ecr.TagStatus.ANY,
        )
        return ecr.Repository(
            self,
            id,
            repository_name=name,
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[lifecycle_rule],
            image_scan_on_push=False,
        )

    def create_generate_dish_lambda(self) -> lambda_python.PythonFunction:
        lambda_function = lambda_python.PythonFunction(
            self,
            "GenerateDishLambda",
            entry="musabi_iac/lambda_handler",
            index="generate_dish.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            memory_size=256,
            timeout=Duration.minutes(3),
        )
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:ap-northeast-1:{self.account}:parameter/openai/musabi/*"
                ],
            )
        )
        return lambda_function

    def create_publish_image_lambda(self) -> lambda_python.PythonFunction:
        lambda_function = lambda_python.PythonFunction(
            self,
            "PublishImageLambda",
            entry="musabi_iac/lambda_handler",
            index="publish_image.py",
            handler="handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            memory_size=256,
            timeout=Duration.minutes(3),
            environment={
                "ImageBucket": self.output_bucket.bucket_name,
            },
        )
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject"],
                resources=[self.output_bucket.arn_for_objects("*")],
            )
        )
        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:ap-northeast-1:{self.account}:parameter/meta/musabi/*"
                ],
            )
        )
        return lambda_function

    def create_statemachine(self) -> sfn.StateMachine:
        generate_dish_step = self._create_generate_dish_lambda_task()
        preprocess_step = self._create_processing_task()
        publish_image_step = self._create_publish_image_lambda_task()
        success_step = sfn.Succeed(self, "Succeded")
        definition = (
            generate_dish_step.next(preprocess_step)
            .next(publish_image_step)
            .next(success_step)
        )
        return sfn.StateMachine(
            self,
            "MusabiStateMachine",
            state_machine_name="musabi-bot-statemachine",
            definition=definition,
            timeout=Duration.minutes(30),
            role=self._get_statemachine_role(),
        )

    def create_event(self) -> None:
        events.Rule(
            self,
            "MusabiEventsRule",
            schedule=events.Schedule.cron(hour="*/12", minute="0"),
            targets=[
                targets.SfnStateMachine(
                    self.state_machine,
                    input=events.RuleTargetInput.from_object(
                        {
                            "Comment": "Insert your JSON here",
                            "Prompt": ", ".join(
                                [
                                    "best quality",
                                    "ultra high res",
                                    "(photorealistic:1.4)",
                                    "a very delicious-looking cuisine",
                                    "a very delicious-looking dish",
                                ]
                            ),
                            "NegativePrompt": ", ".join(
                                [
                                    "paintings",
                                    "sketches",
                                    "(worst quality:2)",
                                    "(low quality:2)",
                                    "(normal quality:2)",
                                    "lowres",
                                    "normal quality",
                                    "((monochrome))",
                                    "((grayscale))",
                                ]
                            ),
                            "Width": "800",
                            "Height": "800",
                            "DryRun": False,
                        }
                    ),
                    max_event_age=Duration.minutes(15),
                    retry_attempts=0,
                )
            ],
        )

    def _create_processing_task(self) -> sfn.CustomState:
        return sfn.CustomState(
            self,
            "SagemakerProcessingTask",
            state_json=self._create_processing_job_state(),
        )

    def _create_generate_dish_lambda_task(self):
        return tasks.LambdaInvoke(
            self,
            "GenerateDish",
            lambda_function=self.generate_dish_function,
            integration_pattern=sfn.IntegrationPattern.REQUEST_RESPONSE,
            result_path="$.GenerateDishResults",
        )

    def _create_publish_image_lambda_task(self):
        return tasks.LambdaInvoke(
            self,
            "PublishImage",
            lambda_function=self.publish_image_function,
            payload=sfn.TaskInput.from_object(
                {
                    "ImageKey": sfn.JsonPath.format(
                        "{}/image_0.png", sfn.JsonPath.string_at("$$.Execution.Name")
                    ),
                    "DishName": sfn.JsonPath.string_at(
                        "$.GenerateDishResults.Payload.DishName"
                    ),
                    "Recipe": sfn.JsonPath.string_at(
                        "$.GenerateDishResults.Payload.Recipe"
                    ),
                    "DryRun": sfn.JsonPath.string_at("$.DryRun"),
                }
            ),
            integration_pattern=sfn.IntegrationPattern.REQUEST_RESPONSE,
        )

    def _create_processing_job_state(self) -> Dict[str, Any]:
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createProcessingJob.sync",
            "Parameters": {
                "AppSpecification": {
                    "ImageUri": self.generate_image_repository.repository_uri_for_tag(
                        "latest"
                    )
                },
                "Environment": {
                    "PROMPT.$": (
                        "States.Format('{}, {}',"
                        " $.GenerateDishResults.Payload.EngDishName, $.Prompt)"
                    ),
                    "NEGATIVE_PROMPT.$": "$.NegativePrompt",
                    "WIDTH.$": "$.Width",
                    "HEIGHT.$": "$.Height",
                    "DISH_NAME": "$.GenerateDishResults.Payload.DishName",
                },
                "ProcessingJobName.$": (
                    "States.Format('PreprocessingJob-{}', States.UUID())"
                ),
                "ProcessingResources": {
                    "ClusterConfig": {
                        "InstanceCount": 1,
                        "InstanceType": "ml.p3.2xlarge",
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
            "ResultPath": "$.PreprocessingResults",
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
