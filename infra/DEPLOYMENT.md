# AWS Hosting Deployment Guide

Carril Diamante on AWS: S3 + CloudFront + Route 53

## Architecture

```
Visitor → HTTPS → CloudFront (d3g1vwpy0d42gr.cloudfront.net)
                     ↓
                  S3 Bucket (carrildiamante-com-site)
                  Private, accessed via OAC only
```

## Prerequisites

- AWS CLI configured with `websites-admin` profile
- Access to `savio-websites` AWS account (847120607923)
- Registrar access for Domain nameserver update (currently on old registrar)
- ACM certificate requested and validated
- Route 53 hosted zone created

## Deployment Steps

### Phase 1: Pre-Flight Check

```bash
# Verify AWS credentials
aws sts get-caller-identity --profile websites-admin

# Check the project structure
ls -la infra/
  security-headers.json      # Security headers config ✓
  setup_hosting.py           # Phase 1 script ✓
  setup_cloudfront.py        # Phase 2 script ✓
  iam/carrildiamante-deployer-policy.json  # Deployer policy ✓
```

### Phase 2: Infrastructure Setup (Dry-Run)

Test what will be created without making actual changes:

```bash
python3 infra/setup_hosting.py --profile websites-admin --dry-run
```

**Output will show:**
- S3 bucket creation steps
- ACM certificate request
- Route 53 hosted zone creation
- OAC creation
- Security headers policy

### Phase 3: Infrastructure Setup (Production)

After reviewing dry-run output, execute:

```bash
python3 infra/setup_hosting.py --profile websites-admin
```

**This creates:**
- ✅ S3 bucket (carrildiamante-com-site)
  - Block Public Access: enabled
  - Encryption: SSE-S3
  - Versioning: disabled
  
- ✅ ACM Certificate (us-east-1)
  - Domains: carrildiamante.com + www.carrildiamante.com
  - Validation: DNS (requires Route 53 CNAME)
  
- ✅ Route 53 Hosted Zone
  - Nameservers: AWS-managed
  - **ACTION: Update registrar to these nameservers**
  
- ✅ CloudFront OAC (Origin Access Control)
  - S3 origin authentication
  - SigV4 signing
  
- ✅ Security Headers Policy
  - CSP: Strict, analytics-only
  - HSTS: 1 year
  - X-Content-Type-Options, X-Frame-Options
  - Referrer-Policy, Permissions-Policy

### Phase 4: ACM Certificate Validation

1. Go to AWS ACM Console → Carril Diamante certificate
2. Find the DNS CNAME records that need to be added
3. Add them to Route 53 hosted zone
4. Wait for validation (usually 5-15 minutes)
5. Verify status shows "Issued"

**Checkpoint:** `aws acm describe-certificate --certificate-arn <arn> --profile websites-admin`

### Phase 5: CloudFront Distribution Setup (Dry-Run)

```bash
# Get the ACM certificate ARN from Phase 4
# Get the OAC ID from Phase 3 output

python3 infra/setup_cloudfront.py \
  --profile websites-admin \
  --cert-arn arn:aws:acm:us-east-1:ACCOUNT:certificate/ID \
  --oac-id OACACCESS123 \
  --dry-run
```

### Phase 6: CloudFront Distribution Setup (Production)

```bash
python3 infra/setup_cloudfront.py \
  --profile websites-admin \
  --cert-arn arn:aws:acm:us-east-1:ACCOUNT:certificate/ID \
  --oac-id OACACCESS123
```

**This creates:**
- ✅ CloudFront distribution
  - Aliases: carrildiamante.com, www.carrildiamante.com
  - Default behavior → S3 origin
  - Security headers policy attached
  - Custom error responses (404/403 → /404.html)
  - HTTP/2 + IPv6 enabled
  - Price class: PriceClass_100 (North America/Europe)

### Phase 7: Route 53 DNS Records

Add Route 53 alias records pointing to CloudFront:

```bash
# Get CloudFront domain name
aws cloudfront list-distributions --profile websites-admin | grep DomainName

# Example: d3g1vwpy0d42gr.cloudfront.net
```

Create alias records:

```bash
# Record 1: carrildiamante.com → CloudFront
# Record 2: www.carrildiamante.com → CloudFront
# Record 3: (keep existing) MX records for email
# Record 4: (keep existing) SPF, DKIM, DMARC records
```

**Verification:**
```bash
dig carrildiamante.com @ns-123.awsdns-45.com +short
dig www.carrildiamante.com @ns-123.awsdns-45.com +short
# Should resolve to CloudFront domain
```

### Phase 8: Update Registrar

1. Go to domain registrar
2. Update nameservers to Route 53:
   - ns-123.awsdns-45.com
   - ns-456.awsdns-78.net
   - etc. (from Route 53 hosted zone)
3. TTL: 24-48 hours for full propagation

**Verification:**
```bash
dig carrildiamante.com +short
# Should resolve to CloudFront IP address
```

### Phase 9: Deploy Site Content

```bash
# Navigate to site directory
cd /Users/hector/Developer/Websites/Carril_Diamante

# Upload site files to S3
aws s3 sync site/ s3://carrildiamante-com-site/ \
  --profile carrildiamante-deployer \
  --delete
```

### Phase 10: Invalidate Cache

```bash
# After uploading, invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*" \
  --profile carrildiamante-deployer
```

### Phase 11: Verification Checklist

```bash
# 1. HTTPS works
curl -I https://carrildiamante.com
# Should return 200 OK

# 2. Security headers present
curl -I https://carrildiamante.com | grep -E "Strict-Transport|Content-Security-Policy"

# 3. Homepage loads
curl https://www.carrildiamante.com | head -20

# 4. 404 page works
curl https://www.carrildiamante.com/nonexistent

# 5. Bilingual pages
curl https://carrildiamante.com/en/

# 6. DNS propagated globally
dig carrildiamante.com +short
dig www.carrildiamante.com +short
```

## Important Files

| File | Purpose |
|------|---------|
| `infra/setup_hosting.py` | Phase 1-2: Infrastructure |
| `infra/setup_cloudfront.py` | Phase 3-4: CDN & Distribution |
| `infra/security-headers.json` | Security headers policy |
| `infra/iam/carrildiamante-deployer-policy.json` | Deployer IAM permissions |
| `site/` | Deployment root (HTML, CSS, images, video) |

## Rollback Plan

Each script saves configuration before changes:

```bash
# Backup current configs
mkdir -p .local/backups-$(date +%Y%m%d)
aws s3api get-bucket-policy --bucket carrildiamante-com-site > backup-bucket-policy.json
aws cloudfront get-distribution-config --id DIST_ID > backup-distribution.json
```

## Troubleshooting

### "Certificate not in us-east-1"
CloudFront requires ACM certificates in `us-east-1`. Re-request if in different region.

### "AccessDenied" on S3
Check IAM deployer policy has `s3:PutObject` on `carrildiamante-com-site/*`

### "Missing page returns XML 403"
Custom error response not configured. Run `setup_cloudfront.py` to fix.

### "Old CSS shows in browser"
CloudFront cache not invalidated. Run `create-invalidation` for changed paths.

### "Email records not working"
Ensure MX records are in Route 53 (copy from old DNS). Add DMARC record.

## Costs (Estimated)

| Service | Cost |
|---------|------|
| Route 53 | $0.50/month (hosted zone) |
| S3 | < $1/month (storage) + requests |
| CloudFront | $5-20/month (depends on traffic) |
| ACM | Free |
| **Total** | **$5-25/month** |

## Next Steps

1. ✅ Run dry-run on Phase 1
2. ✅ Review output with Hector
3. ✅ Execute Phase 1 (infrastructure)
4. ✅ Validate ACM certificate
5. ✅ Execute Phase 2 (CloudFront)
6. ✅ Add Route 53 DNS records
7. ✅ Update registrar nameservers
8. ✅ Deploy site content
9. ✅ Run verification checklist
10. ✅ Monitor CloudFront metrics

---

**Reference:** See `../CLAUDE.md` for account setup and credentials guidance.
