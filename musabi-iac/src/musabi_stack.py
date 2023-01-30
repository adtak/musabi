from aws_cdk import core
from aws_cdk.aws_applicationautoscaling import Schedule
from aws_cdk.aws_ecs import ContainerImage, LogDriver, Secret
from aws_cdk.aws_ecs_patterns import (
    ScheduledFargateTask, ScheduledFargateTaskImageOptions
)
from aws_cdk.aws_ecr import Repository, LifecycleRule, TagStatus
from aws_cdk.aws_logs import LogGroup, RetentionDays
from aws_cdk.aws_ssm import StringParameter
from aws_cdk.core import RemovalPolicy


class MusabiStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create ECR
        lifecycle_rule = LifecycleRule(
            description="Keep only one image.",
            max_image_count=1,
            rule_priority=1,
            tag_status=TagStatus.ANY,
        )
        repository = Repository(
            self,
            "musabiRepository",
            image_scan_on_push=False,
            lifecycle_rules=[lifecycle_rule],
            removal_policy=core.RemovalPolicy.DESTROY,
            repository_name="musabi",
        )

        # Create Fargate Task
        schedule = Schedule.cron(hour="3", minute="0")

        image = ContainerImage.from_ecr_repository(
            repository,
            tag="latest",
        )
        log_driver = LogDriver.aws_logs(
            stream_prefix="musabi",
            log_group=LogGroup(
                self,
                "musabiLogGroup",
                log_group_name="musabi",
                removal_policy=RemovalPolicy.DESTROY,
                retention=RetentionDays.ONE_WEEK,
            ),
        )
        insta_user_secrets = Secret.from_ssm_parameter(
            StringParameter.from_secure_string_parameter_attributes(
                self,
                "musabiInstaUser",
                parameter_name="insta_user",
                version=1
            )
        )
        insta_pass_secrets = Secret.from_ssm_parameter(
            StringParameter.from_secure_string_parameter_attributes(
                self,
                "musabiInstaPass",
                parameter_name="insta_password",
                version=1
            )
        )
        image_option = ScheduledFargateTaskImageOptions(
            image=image,
            environment={},
            log_driver=log_driver,
            cpu=2048,
            secrets={
                "INSTA_USER": insta_user_secrets,
                "INSTA_PASSWORD": insta_pass_secrets,
            },
            memory_limit_mib=4096,
        )
        ScheduledFargateTask(
            self,
            "musabiScheduledTask",
            schedule=schedule,
            scheduled_fargate_task_image_options=image_option,
        )
