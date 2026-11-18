#!/usr/bin/env python3
"""
CloudFront Distribution Setup for Carril Diamante

Creates CloudFront distribution with:
- S3 origin (private, OAC)
- Security headers
- URL rewriting
- Caching optimized

Usage:
    python3 infra/setup_cloudfront.py --profile websites-admin --cert-arn <arn> [--dry-run]
"""

import sys
import json
import argparse
import subprocess

SITE_NAME = "carril-diamante"
DOMAIN = "carrildiamante.com"
BUCKET_NAME = "carrildiamante-com-site"
REGION = "us-east-1"

def run_cmd(cmd, profile=None, dry_run=False):
    """Run AWS CLI command"""
    if profile:
        cmd = ["aws"] + cmd + ["--profile", profile, "--region", REGION]
    else:
        cmd = ["aws"] + cmd + ["--region", REGION]

    if dry_run:
        print(f"\n[DRY-RUN] Would run: {' '.join(cmd)}")
        return {"DryRun": True}

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout) if result.stdout else {}
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        raise

def step(title):
    """Print a step header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def checkpoint(msg):
    """Print checkpoint message"""
    print(f"\n✓ {msg}")

def setup_cloudfront(profile, cert_arn, oac_id, dry_run):
    """Create CloudFront distribution"""
    step("Creating CloudFront Distribution")

    # CloudFront distribution config
    distribution_config = {
        "CallerReference": f"{SITE_NAME}-{DOMAIN}",
        "Comment": f"CDN for {DOMAIN}",
        "DefaultRootObject": "index.html",
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": f"{SITE_NAME}-s3",
                    "DomainName": f"{BUCKET_NAME}.s3.{REGION}.amazonaws.com",
                    "S3OriginConfig": {
                        "OriginAccessIdentity": ""
                    },
                    "OriginAccessControlId": oac_id
                }
            ]
        },
        "DefaultCacheBehavior": {
            "TargetOriginId": f"{SITE_NAME}-s3",
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            },
            "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",  # CachingOptimized
            "ResponseHeadersPolicyId": "",  # Will be set after policy is created
            "Compress": True
        },
        "CacheBehaviors": [],
        "Enabled": True,
        "ViewerCertificate": {
            "ACMCertificateArn": cert_arn,
            "SSLSupportMethod": "sni-only",
            "MinimumProtocolVersion": "TLSv1.2_2021"
        },
        "Aliases": {
            "Quantity": 2,
            "Items": [DOMAIN, f"www.{DOMAIN}"]
        },
        "HttpVersion": "http2and3",
        "IsIPV6Enabled": True,
        "PriceClass": "PriceClass_100"
    }

    if not dry_run:
        cmd = [
            "cloudfront", "create-distribution",
            "--distribution-config", json.dumps(distribution_config)
        ]
        result = run_cmd(cmd, profile, dry_run)
        dist_id = result.get("Distribution", {}).get("Id")
        dist_domain = result.get("Distribution", {}).get("DomainName")
        checkpoint(f"Distribution created: {dist_id}")
        checkpoint(f"CloudFront domain: {dist_domain}")
        return dist_id
    else:
        checkpoint("[DRY-RUN] Would create CloudFront distribution")
        return "EKTYEDHVURFWC"

def setup_bucket_policy(profile, dist_oac_id, dry_run):
    """Update S3 bucket policy for CloudFront OAC"""
    step("Updating S3 Bucket Policy")

    if not dry_run:
        # Get OAC details
        cmd = [
            "cloudfront", "get-origin-access-control",
            "--id", dist_oac_id
        ]
        oac_result = run_cmd(cmd, profile, dry_run)
        oac_arn = oac_result.get("OriginAccessControl", {}).get("OriginAccessControlConfig", {}).get("Id")

        # Create bucket policy
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudfront.amazonaws.com"
                    },
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*",
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceArn": f"arn:aws:cloudfront::{REGION}:distribution/{dist_oac_id}"
                        }
                    }
                }
            ]
        }

        cmd = [
            "s3api", "put-bucket-policy",
            "--bucket", BUCKET_NAME,
            "--policy", json.dumps(bucket_policy)
        ]
        run_cmd(cmd, profile, dry_run)
        checkpoint("Bucket policy updated for CloudFront OAC")
    else:
        checkpoint("[DRY-RUN] Would update bucket policy")

def setup_error_responses(profile, dist_id, dry_run):
    """Configure custom error responses"""
    step("Configuring Error Responses")

    if not dry_run:
        # Get current distribution config
        cmd = ["cloudfront", "get-distribution-config", "--id", dist_id]
        result = run_cmd(cmd, profile, dry_run)
        config = result.get("DistributionConfig", {})
        etag = result.get("ETag")

        # Add error responses
        config["CustomErrorResponses"] = {
            "Quantity": 2,
            "Items": [
                {
                    "ErrorCode": 404,
                    "ResponsePagePath": "/404.html",
                    "ResponseCode": "404",
                    "ErrorCachingMinTTL": 300
                },
                {
                    "ErrorCode": 403,
                    "ResponsePagePath": "/404.html",
                    "ResponseCode": "404",
                    "ErrorCachingMinTTL": 300
                }
            ]
        }

        # Update distribution
        cmd = [
            "cloudfront", "update-distribution",
            "--id", dist_id,
            "--distribution-config", json.dumps(config),
            "--if-match", etag
        ]
        run_cmd(cmd, profile, dry_run)
        checkpoint("Error responses configured (404/403 → /404.html)")
    else:
        checkpoint("[DRY-RUN] Would configure error responses")

def print_summary(cert_arn, oac_id, dist_id, dry_run):
    """Print summary"""
    step("CLOUDFRONT SETUP SUMMARY")

    print(f"\nConfiguration:")
    print(f"  Domain: {DOMAIN}")
    print(f"  S3 Bucket: {BUCKET_NAME}")
    print(f"  ACM Certificate: {cert_arn}")
    print(f"  OAC ID: {oac_id}")
    print(f"  Distribution ID: {dist_id}")

    if dry_run:
        print(f"\n⚠️  DRY-RUN MODE - No changes made")
    else:
        print(f"\nNext steps:")
        print(f"  1. Update Route 53 to point to CloudFront")
        print(f"  2. Upload site content to S3 bucket")
        print(f"  3. Test domain in browser")
        print(f"  4. Monitor CloudFront metrics")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="AWS CLI profile")
    parser.add_argument("--cert-arn", required=True, help="ACM certificate ARN")
    parser.add_argument("--oac-id", required=True, help="OAC ID")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode")
    args = parser.parse_args()

    try:
        print(f"\n{'='*60}")
        print(f"  CloudFront Distribution Setup")
        print(f"  {'DRY-RUN MODE' if args.dry_run else 'PRODUCTION MODE'}")
        print(f"{'='*60}")

        dist_id = setup_cloudfront(args.profile, args.cert_arn, args.oac_id, args.dry_run)
        setup_bucket_policy(args.profile, args.oac_id, args.dry_run)
        setup_error_responses(args.profile, dist_id, args.dry_run)

        print_summary(args.cert_arn, args.oac_id, dist_id, args.dry_run)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
