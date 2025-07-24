"""
This is a CDK app that creates an ECS Fargate service with an ALB and a Streamlit app.
"""

from typing import Any

import aws_cdk as cdk
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedFargateService
from constructs import Construct


class StreamlitStack(cdk.Stack):
    """
    This class creates an ECS Fargate service with an ALB and a Streamlit app.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create ECS Fargate service with ALB
        _fargate_service: ApplicationLoadBalancedFargateService = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "StreamlitService",
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset("."),
                container_port=8501,
            ),
            memory_limit_mib=1024,
            cpu=512,
            desired_count=1,
            public_load_balancer=True,
        )


app = cdk.App()
StreamlitStack(app, "StreamlitStack", env=cdk.Environment(
    account="611255759732",
    region="us-east-1"
))

app.synth()
