from typing import Any

import aws_cdk.aws_ecr as ecr
from aws_cdk import Stack, RemovalPolicy
from constructs import Construct


class MusabiStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs: Any) -> None:
        super().__init__(scope, id, **kwargs)
        
        self.create_ecr_repository()

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
            repository_name="musabi-bot",
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[lifecycle_rule],
            image_scan_on_push=False,
        )
