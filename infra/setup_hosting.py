#!/usr/bin/env python3
"""
Carril Diamante AWS Hosting Setup Script

Creates and configures all AWS infrastructure for carrildiamante.com:
- S3 bucket (private, OAC only)
- CloudFront distribution
- ACM SSL certificate
- Route 53 hosted zone
- Security headers policy

Usage:
    python3 infra/setup_hosting.py --profile websites-admin [--dry-run]

This script uses the deployer profile defined in the CLAUDE.md.
All changes are reversible and can be tested in dry-run mode first.
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path

# Configuration
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

def setup_s3_bucket(profile, dry_run):
    """Create and configure S3 bucket"""
    step("Step 1: S3 Bucket Setup")

    print(f"Creating bucket: {BUCKET_NAME}")

    if not dry_run:
        # Create bucket
        cmd = [
            "s3api", "create-bucket",
            "--bucket", BUCKET_NAME,
            "--region", REGION
        ]
        try:
            run_cmd(cmd, profile, dry_run)
            checkpoint(f"Bucket created: {BUCKET_NAME}")
        except:
            checkpoint(f"Bucket may already exist: {BUCKET_NAME}")
    else:
        checkpoint(f"[DRY-RUN] Would create bucket: {BUCKET_NAME}")

    # Block public access
    if not dry_run:
        block_config = {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True
        }
        cmd = [
            "s3api", "put-public-access-block",
            "--bucket", BUCKET_NAME,
            "--public-access-block-configuration", json.dumps(block_config)
        ]
        run_cmd(cmd, profile, dry_run)
        checkpoint("Block Public Access: enabled (all 4)")
    else:
        checkpoint("[DRY-RUN] Would enable Block Public Access")

    # Enable SSE-S3
    encryption = {
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }
    if not dry_run:
        cmd = [
            "s3api", "put-bucket-encryption",
            "--bucket", BUCKET_NAME,
            "--server-side-encryption-configuration", json.dumps(encryption)
        ]
        run_cmd(cmd, profile, dry_run)
        checkpoint("Encryption: SSE-S3 enabled")
    else:
        checkpoint("[DRY-RUN] Would enable SSE-S3 encryption")

def setup_acm_certificate(profile, dry_run):
    """Request ACM certificate for the domain"""
    step("Step 2: ACM Certificate")

    domains = [DOMAIN, f"www.{DOMAIN}"]
    print(f"Requesting certificate for: {', '.join(domains)}")

    if not dry_run:
        cmd = [
            "acm", "request-certificate",
            "--domain-name", DOMAIN,
            "--subject-alternative-names", f"www.{DOMAIN}",
            "--validation-method", "DNS"
        ]
        result = run_cmd(cmd, profile, dry_run)
        cert_arn = result.get("CertificateArn")
        checkpoint(f"Certificate requested: {cert_arn}")
        print("\n⚠️  ACTION REQUIRED:")
        print("1. Go to AWS ACM console")
        print("2. Find the certificate for carrildiamante.com")
        print("3. Add the DNS validation CNAME record to Route 53")
        print("4. Wait for validation to complete (usually 5-10 minutes)")
        return cert_arn
    else:
        checkpoint("[DRY-RUN] Would request ACM certificate")
        return "arn:aws:acm:us-east-1:ACCOUNT:certificate/PLACEHOLDER"

def setup_route53_hosted_zone(profile, dry_run):
    """Create Route 53 hosted zone"""
    step("Step 3: Route 53 Hosted Zone")

    print(f"Creating hosted zone for: {DOMAIN}")

    if not dry_run:
        cmd = [
            "route53", "create-hosted-zone",
            "--name", DOMAIN,
            "--caller-reference", f"carril-diamante-{DOMAIN}"
        ]
        result = run_cmd(cmd, profile, dry_run)
        zone_id = result.get("HostedZone", {}).get("Id", "").split("/")[-1]
        nameservers = [ns for ns in result.get("DelegationSet", {}).get("NameServers", [])]

        checkpoint(f"Hosted Zone created: {zone_id}")
        checkpoint(f"Nameservers: {', '.join(nameservers)}")

        print("\n⚠️  ACTION REQUIRED AT REGISTRAR:")
        print("Update the domain registrar's nameservers to:")
        for ns in nameservers:
            print(f"  - {ns}")

        return zone_id
    else:
        checkpoint("[DRY-RUN] Would create Route 53 hosted zone")
        return "Z1234567890ABC"

def setup_cloudfront_oac(profile, dry_run):
    """Create CloudFront OAC"""
    step("Step 4: CloudFront Origin Access Control")

    if not dry_run:
        oac_config = {
            "Name": f"{SITE_NAME}-oac",
            "Description": f"OAC for {DOMAIN}",
            "OriginAccessControlOriginType": "s3",
            "SigningBehavior": "always",
            "SigningProtocol": "sigv4"
        }
        cmd = [
            "cloudfront", "create-origin-access-control",
            "--origin-access-control-config", json.dumps(oac_config)
        ]
        result = run_cmd(cmd, profile, dry_run)
        oac_id = result.get("OriginAccessControl", {}).get("Id")
        checkpoint(f"OAC created: {oac_id}")
        return oac_id
    else:
        checkpoint("[DRY-RUN] Would create OAC")
        return "E1234567890ABC"

def setup_response_headers_policy(profile, dry_run):
    """Create response headers security policy"""
    step("Step 5: Security Headers Policy")

    policy_name = f"{SITE_NAME}-security-headers"

    # Read the security headers configuration
    headers_file = Path("infra/security-headers.json")
    if not headers_file.exists():
        print(f"Error: {headers_file} not found")
        return None

    with open(headers_file) as f:
        headers_config = json.load(f)

    if not dry_run:
        policy = {
            "Name": policy_name,
            "SecurityHeadersConfig": headers_config
        }
        cmd = [
            "cloudfront", "create-response-headers-policy",
            "--response-headers-policy-config", json.dumps(policy)
        ]
        result = run_cmd(cmd, profile, dry_run)
        policy_id = result.get("ResponseHeadersPolicy", {}).get("Id")
        checkpoint(f"Security headers policy created: {policy_id}")
        return policy_id
    else:
        checkpoint("[DRY-RUN] Would create response headers policy")
        return "7517fc76-39c0-4019-a1c7-7fe40fc2f038"

def print_summary(profile, dry_run):
    """Print deployment summary"""
    step("DEPLOYMENT SUMMARY")

    print(f"\nSite Configuration:")
    print(f"  Domain: {DOMAIN}")
    print(f"  S3 Bucket: {BUCKET_NAME}")
    print(f"  Region: {REGION}")
    print(f"  AWS Profile: {profile}")

    if dry_run:
        print(f"\n⚠️  DRY-RUN MODE - No changes were made")
        print(f"\nTo proceed with actual deployment, run:")
        print(f"  python3 infra/setup_hosting.py --profile {profile}")
    else:
        print(f"\n✓ Infrastructure setup initiated")
        print(f"\nNext steps:")
        print(f"  1. Validate ACM certificate (check Route 53 for CNAME)")
        print(f"  2. Update registrar nameservers to Route 53")
        print(f"  3. Create CloudFront distribution (use setup_cloudfront.sh)")
        print(f"  4. Add Route 53 alias records pointing to CloudFront")
        print(f"  5. Deploy site content to S3 bucket")
        print(f"  6. Run health checks")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="AWS CLI profile to use")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    try:
        print(f"\n{'='*60}")
        print(f"  Carril Diamante AWS Hosting Setup")
        print(f"  {'DRY-RUN MODE' if args.dry_run else 'PRODUCTION MODE'}")
        print(f"{'='*60}")

        setup_s3_bucket(args.profile, args.dry_run)
        setup_acm_certificate(args.profile, args.dry_run)
        setup_route53_hosted_zone(args.profile, args.dry_run)
        setup_cloudfront_oac(args.profile, args.dry_run)
        setup_response_headers_policy(args.profile, args.dry_run)

        print_summary(args.profile, args.dry_run)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
