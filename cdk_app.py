"""
This is a CDK app that creates an ECS Fargate service with an ALB and a Streamlit app.
Uses DNS delegation - domain stays at GoDaddy but DNS is managed by Route53.
"""

from typing import Any

import aws_cdk as cdk
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_cognito as cognito
import aws_cdk.aws_dynamodb as dynamodb
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecs_patterns
import aws_cdk.aws_route53 as route53
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedFargateService
from aws_cdk.aws_iam import PolicyStatement
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

        # Cognito User Pool for authentication
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your email for Cooling Loads",
                email_body="Thanks for signing up! Your verification code is {####}",
                email_style=cognito.VerificationEmailStyle.CODE,
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=False,
            ),
        )

        # Client for the user pool
        user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=user_pool,
            auth_flows=cognito.AuthFlow(user_password=True),
        )

        # DynamoDB table for projects
        project_table = dynamodb.Table(
            self,
            "CoolingProjectsTable",
            partition_key=dynamodb.Attribute(
                name="username", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="project_name", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # Create ECS Fargate service with ALB
        _fargate_service: ApplicationLoadBalancedFargateService = (
            ecs_patterns.ApplicationLoadBalancedFargateService(
                self,
                "StreamlitService",
                task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                    image=ecs.ContainerImage.from_asset("."),
                    container_port=8501,
                    # Add environment variables for configuration
                    environment={
                        "STREAMLIT_SERVER_PORT": "8501",
                        "STREAMLIT_SERVER_ADDRESS": "0.0.0.0",
                        "STREAMLIT_SERVER_HEADLESS": "true",
                        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
                        # AWS service configurations
                        "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
                        "COGNITO_CLIENT_ID": user_pool_client.user_pool_client_id,
                        "DYNAMODB_TABLE_NAME": project_table.table_name,
                    },
                    # Enable logging
                    enable_logging=True,
                    log_driver=ecs.LogDrivers.aws_logs(
                        stream_prefix="Streamlit",
                        mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                    ),
                ),
                memory_limit_mib=1024,
                cpu=512,
                desired_count=1,
                public_load_balancer=True,
                # Add health check configuration
                health_check_grace_period=cdk.Duration.seconds(60),
                # Domain configuration
                domain_name=domain_name,
                domain_zone=hosted_zone,
                certificate=certificate,
                redirect_http=True,  # Redirect HTTP to HTTPS
            )
        )

        # Grant ECS task role access to DynamoDB
        project_table.grant_read_write_data(_fargate_service.task_definition.task_role)

        # Grant access to Cognito
        _fargate_service.task_definition.task_role.add_to_principal_policy(
            PolicyStatement(
                actions=[
                    "cognito-idp:SignUp",
                    "cognito-idp:ConfirmSignUp",
                    "cognito-idp:InitiateAuth",
                ],
                resources=[user_pool.user_pool_arn],
            )
        )

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

        # Output Cognito details
        cdk.CfnOutput(
            self,
            "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID",
        )
        cdk.CfnOutput(
            self,
            "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID",
        )
        cdk.CfnOutput(
            self,
            "DynamoDBTableName",
            value=project_table.table_name,
            description="DynamoDB Table for Projects",
        )


app = cdk.App()
StreamlitStack(
    app,
    "StreamlitStack",
    env=cdk.Environment(account="611255759732", region="us-east-1"),
)

app.synth()
