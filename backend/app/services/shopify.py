import re
from urllib.parse import urlparse

import httpx
from cryptography.fernet import Fernet

from app.core.config import get_settings

settings = get_settings()
API_VERSION = "2026-07"

PRODUCT_QUERY = """
query ProductAudit($after: String) {
  products(first: 100, after: $after) {
    nodes {
      id
      title
      handle
      description
      status
      seo { title description }
      media(first: 50) {
        nodes {
          mediaContentType
          ... on MediaImage {
            image { altText }
          }
        }
      }
      variants(first: 100) {
        nodes { inventoryQuantity }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


def _fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        raise RuntimeError("ENCRYPTION_KEY is required")
    return Fernet(key.encode())


def encrypt_token(token: str) -> str:
    return _fernet().encrypt(token.encode()).decode()


def decrypt_token(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def normalize_shop_domain(value: str) -> str:
    value = value.strip()
    if "://" not in value:
        value = f"https://{value}"
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower().strip(".")
    if not host or not host.endswith(".myshopify.com"):
        raise ValueError("Shopify store must use a *.myshopify.com domain")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*\.myshopify\.com", host):
        raise ValueError("Invalid Shopify store domain")
    return host


def _endpoint(shop_domain: str) -> str:
    return f"https://{shop_domain}/admin/api/{API_VERSION}/graphql.json"


async def graphql(shop_domain: str, access_token: str, query: str, variables: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            _endpoint(shop_domain),
            headers={"Content-Type": "application/json", "X-Shopify-Access-Token": access_token},
            json={"query": query, "variables": variables or {}},
        )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "Shopify GraphQL request failed"))
    return payload["data"]


def audit_product(product: dict) -> dict:
    seo = product.get("seo") or {}
    images = [
        n for n in (product.get("media", {}).get("nodes") or [])
        if n.get("mediaContentType") == "IMAGE"
    ]
    missing_alt = sum(1 for n in images if not ((n.get("image") or {}).get("altText") or "").strip())
    title = (seo.get("title") or "").strip()
    description = (seo.get("description") or "").strip()
    reasons = []
    if not title:
        reasons.append("Missing SEO title")
    elif len(title) > 60:
        reasons.append("SEO title is longer than 60 characters")
    if not description:
        reasons.append("Missing SEO description")
    elif len(description) > 160:
        reasons.append("SEO description is longer than 160 characters")
    if images and missing_alt:
        reasons.append(f"{missing_alt} image(s) missing alt text")
    inventory = sum((v.get("inventoryQuantity") or 0) for v in (product.get("variants", {}).get("nodes") or []))
    if inventory <= 0:
        reasons.append("No positive inventory across variants")
    score = max(0, 100 - len(reasons) * 20)
    return {
        "id": product["id"],
        "title": product["title"],
        "handle": product["handle"],
        "status": product["status"],
        "seo_title": title,
        "seo_description": description,
        "inventory": inventory,
        "image_count": len(images),
        "missing_alt": missing_alt,
        "score": score,
        "issues": reasons,
    }


async def scan_products(shop_domain: str, access_token: str) -> list[dict]:
    products = []
    cursor = None
    while True:
        data = await graphql(shop_domain, access_token, PRODUCT_QUERY, {"after": cursor})
        connection = data["products"]
        products.extend(audit_product(node) for node in connection["nodes"])
        if not connection["pageInfo"]["hasNextPage"]:
            break
        cursor = connection["pageInfo"]["endCursor"]
    return products
