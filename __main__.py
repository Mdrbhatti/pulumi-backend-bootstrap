import json
import pulumi
import pulumi_aws as aws

# create S3 bucket for storing pulumi state
pulumi_backend_state_bucket = aws.s3.Bucket(
    "pulumi-backend-state-bucket",
    acl="private",
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="AES256"
            )
        )
    ),
)

# block all public access for the bucket
aws.s3.BucketPublicAccessBlock(
    "pulumi-backend-state-bucket-public-access-block",
    bucket=pulumi_backend_state_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)


aws_account_id = aws.get_caller_identity().account_id
pulumi_secrets_provider_encryption_key = aws.kms.Key(
    "pulumi-secrets-provider-encryption-key",
    deletion_window_in_days=10,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                # policy which gives the AWS account that owns the KMS key full access to the KMS key
                {
                    "Sid": "Enable IAM policies",
                    "Effect": "Allow",
                    "Action": "kms:*",
                    "Principal": {"AWS": [f"arn:aws:iam::{aws_account_id}:root"]},
                    "Resource": "*",
                },
            ],
        }
    ),
)

pulumi.export(
    "PULUMI_BACKEND_URL", pulumi_backend_state_bucket.id.apply(lambda v: f"s3://{v}")
)
pulumi.export(
    "Pulumi Backend Login Command",
    pulumi_backend_state_bucket.id.apply(lambda v: f"pulumi login s3://{v}"),
)

pulumi.export(
    "PULUMI_SECRETS_PROVIDER",
    pulumi_secrets_provider_encryption_key.key_id.apply(lambda v: f"awskms:///{v}"),
)
pulumi.export(
    "Pulumi Stack Init Command",
    pulumi_secrets_provider_encryption_key.key_id.apply(
        lambda v: f"pulumi stack init --secrets-provider='awskms:///{v}' <project-name>.<stack-name>"
    ),
)
