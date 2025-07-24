"""
This is a CDK app that creates an ECS Fargate service with an ALB and a Streamlit app.
Uses DNS delegation - domain stays at GoDaddy but DNS is managed by Route53.
"""

from typing import Any

import aws_cdk as cdk
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_route53 as route53

from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedFargateService
from constructs import Construct


class StreamlitStack(cdk.Stack):
    """
    This class creates an ECS Fargate service with an ALB and a Streamlit app.
    Uses DNS delegation for optimal AWS integration while keeping domain at GoDaddy.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Domain configuration
        domain_name = "loadestimator.com"

        # Create Route53 hosted zone (for DNS delegation)
        hosted_zone = route53.HostedZone(
            self,
            "HostedZone",
            zone_name=domain_name,
            comment="Hosted zone for loadestimator.com - delegated from GoDaddy",
        )

        # Create certificate with automatic DNS validation
        certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=domain_name,
            subject_alternative_names=[f"www.{domain_name}"],
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # Create ECS Fargate service with ALB
        _fargate_service: ApplicationLoadBalancedFargateService = (
            ecs_patterns.ApplicationLoadBalancedFargateService(
                self,
                "StreamlitService",
                task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                    image=ecs.ContainerImage.from_asset("."),
                    container_port=8501,
                    # Add environment variables for better configuration
                    environment={
                        "STREAMLIT_SERVER_PORT": "8501",
                        "STREAMLIT_SERVER_ADDRESS": "0.0.0.0",
                        "STREAMLIT_SERVER_HEADLESS": "true",
                        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
                    },
                    # Enable logging
                    enable_logging=True,
                ),
                memory_limit_mib=1024,
                cpu=512,
                desired_count=1,
                public_load_balancer=True,
                # Add health check configuration
                health_check_grace_period=cdk.Duration.seconds(60),
                # Configure ARM64 architecture to match local build
                platform_version=ecs.FargatePlatformVersion.VERSION1_4,
                # Domain configuration
                domain_name=domain_name,
                domain_zone=hosted_zone,
                certificate=certificate,
                redirect_http=True,  # Redirect HTTP to HTTPS
            )
        )

        # Note: Docker image will be built for x86_64 architecture to match ECS Fargate default

        # Configure health check on the target group
        _fargate_service.target_group.configure_health_check(
            enabled=True,
            healthy_http_codes="200",
            path="/",
            interval=cdk.Duration.seconds(30),
            timeout=cdk.Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=5,
        )

        # Note: ApplicationLoadBalancedFargateService automatically creates both
        # root domain and www records when certificate includes subject_alternative_names

        # Output the nameservers for GoDaddy configuration
        cdk.CfnOutput(
            self,
            "NameServers",
            value=cdk.Fn.join(", ", hosted_zone.hosted_zone_name_servers or []),
            description="Add these nameservers to your GoDaddy domain settings",
        )

        # Output the certificate ARN for reference
        cdk.CfnOutput(
            self,
            "CertificateArn",
            value=certificate.certificate_arn,
            description="SSL Certificate ARN",
        )

        # Output the hosted zone ID for reference
        cdk.CfnOutput(
            self,
            "HostedZoneId",
            value=hosted_zone.hosted_zone_id,
            description="Route53 Hosted Zone ID",
        )


app = cdk.App()
StreamlitStack(
    app,
    "StreamlitStack",
    env=cdk.Environment(account="611255759732", region="us-east-1"),
)

app.synth()
