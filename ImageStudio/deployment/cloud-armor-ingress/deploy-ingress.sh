#!/usr/bin/env bash
# ==============================================================================
# Cloud Armor & Load Balancer Ingress Provisioning for Image Studio
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-gdc-ai-playground}"
REGION="${2:-us-central1}"
SERVICE_NAME="image-studio"
POLICY_NAME="${SERVICE_NAME}-cloud-armor-policy"
NEG_NAME="${SERVICE_NAME}-serverless-neg"
BACKEND_NAME="${SERVICE_NAME}-backend-service"
URLMAP_NAME="${SERVICE_NAME}-url-map"
IP_NAME="${SERVICE_NAME}-lb-ip"
PROXY_NAME="${SERVICE_NAME}-http-proxy"
FWD_RULE_NAME="${SERVICE_NAME}-http-forwarding-rule"

echo "================================================================="
echo "Provisioning Cloud Armor & Ingress for ${SERVICE_NAME}"
echo "Project: ${PROJECT_ID} | Region: ${REGION}"
echo "================================================================="

# 1. Create Cloud Armor Security Policy
echo "[1/7] Creating Cloud Armor Security Policy: ${POLICY_NAME}..."
gcloud compute security-policies create "${POLICY_NAME}" \
  --project="${PROJECT_ID}" \
  --description="Cloud Armor WAF and rate limiting policy for ${SERVICE_NAME}" || true

# 2. Add Adaptive DDoS Defense
echo "[2/7] Enabling Adaptive DDoS Protection..."
gcloud compute security-policies update "${POLICY_NAME}" \
  --project="${PROJECT_ID}" \
  --enable-layer7-ddos-defense || true

# 3. Add Rate Limiting Rule (120 req/min)
echo "[3/7] Adding Rate Limiting Rule (120 requests/minute)..."
gcloud compute security-policies rules create 1000 \
  --security-policy="${POLICY_NAME}" \
  --project="${PROJECT_ID}" \
  --expression="true" \
  --action="rate-based-ban" \
  --rate-limit-threshold-count=120 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=300 \
  --conform-action="allow" \
  --exceed-action="deny-429" \
  --enforce-on-key="IP" || true

# 4. Add OWASP Top 10 Core Rule Sets
echo "[4/7] Adding OWASP WAF Protection Rules (XSS, SQLi, Scanners)..."
gcloud compute security-policies rules create 2000 \
  --security-policy="${POLICY_NAME}" \
  --project="${PROJECT_ID}" \
  --expression="evaluatePreconfiguredExpr('xss-v33-stable')" \
  --action="deny-403" \
  --description="Block OWASP XSS" || true

gcloud compute security-policies rules create 2100 \
  --security-policy="${POLICY_NAME}" \
  --project="${PROJECT_ID}" \
  --expression="evaluatePreconfiguredExpr('sqli-v33-stable')" \
  --action="deny-403" \
  --description="Block SQLi" || true

gcloud compute security-policies rules create 2200 \
  --security-policy="${POLICY_NAME}" \
  --project="${PROJECT_ID}" \
  --expression="evaluatePreconfiguredExpr('scannerdetection-v33-stable')" \
  --action="deny-403" \
  --description="Block Vulnerability Scanners" || true

# 5. Create Serverless Network Endpoint Group (NEG)
echo "[5/7] Creating Serverless NEG for Cloud Run..."
gcloud compute network-endpoint-groups create "${NEG_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --network-endpoint-type=SERVERLESS \
  --cloud-run-service="${SERVICE_NAME}" || true

# 6. Create Global Backend Service and attach Cloud Armor Policy
echo "[6/7] Creating Backend Service and attaching Cloud Armor..."
gcloud compute backend-services create "${BACKEND_NAME}" \
  --global \
  --project="${PROJECT_ID}" \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --security-policy="${POLICY_NAME}" || true

gcloud compute backend-services add-backend "${BACKEND_NAME}" \
  --global \
  --project="${PROJECT_ID}" \
  --network-endpoint-group="${NEG_NAME}" \
  --network-endpoint-group-region="${REGION}" || true

# 7. Create URL Map, Static IP, Target Proxy, and Global Forwarding Rule
echo "[7/7] Creating Load Balancer Frontend & Routing..."
gcloud compute url-maps create "${URLMAP_NAME}" \
  --default-service="${BACKEND_NAME}" \
  --project="${PROJECT_ID}" \
  --global || true

gcloud compute addresses create "${IP_NAME}" \
  --global \
  --project="${PROJECT_ID}" || true

LB_IP=$(gcloud compute addresses describe "${IP_NAME}" --global --project="${PROJECT_ID}" --format="value(address)")

gcloud compute target-http-proxies create "${PROXY_NAME}" \
  --url-map="${URLMAP_NAME}" \
  --project="${PROJECT_ID}" \
  --global || true

gcloud compute forwarding-rules create "${FWD_RULE_NAME}" \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --network-tier=PREMIUM \
  --address="${LB_IP}" \
  --target-http-proxy="${PROXY_NAME}" \
  --global \
  --ports=80 \
  --project="${PROJECT_ID}" || true

# 8. Lock down Cloud Run to only accept traffic from Cloud Load Balancing
echo "Securing Cloud Run service to internal and load-balancer ingress only..."
gcloud run services update "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --ingress=internal-and-cloud-load-balancing || true

echo "================================================================="
echo "✅ Cloud Armor & Load Balancer Ingress Deployed Successfully!"
echo "Public Ingress IP: http://${LB_IP}"
echo "Security Policy:   ${POLICY_NAME}"
echo "================================================================="
