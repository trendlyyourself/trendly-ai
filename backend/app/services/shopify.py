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


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip()


def _truncate(value: str, limit: int) -> str:
    value = _clean_text(value)
    if len(value) <= limit:
        return value
    shortened = value[: limit + 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return shortened or value[:limit]


def build_recommendations(product: dict) -> list[dict]:
    seo = product.get("seo") or {}
    current_title = (seo.get("title") or "").strip()
    current_description = (seo.get("description") or "").strip()
    product_title = _clean_text(product.get("title") or "")
    source_description = _clean_text(product.get("description") or "")
    recommendations = []

    if not current_title:
        proposed = _truncate(product_title, 60)
        if proposed:
            recommendations.append({
                "type": "seo_title",
                "priority": "high",
                "reason": "The product has no SEO title.",
                "current": "",
                "proposed": proposed,
                "requires_approval": True,
            })
    elif len(current_title) > 60:
        recommendations.append({
            "type": "seo_title",
            "priority": "medium",
            "reason": "The current SEO title exceeds 60 characters.",
            "current": current_title,
            "proposed": _truncate(current_title, 60),
            "requires_approval": True,
        })

    if not current_description:
        proposed = _truncate(source_description, 160)
        if proposed:
            recommendations.append({
                "type": "seo_description",
                "priority": "high",
                "reason": "The product has no SEO description; the existing product description can supply one.",
                "current": "",
                "proposed": proposed,
                "requires_approval": True,
            })
    elif len(current_description) > 160:
        recommendations.append({
            "type": "seo_description",
            "priority": "medium",
            "reason": "The current SEO description exceeds 160 characters.",
            "current": current_description,
            "proposed": _truncate(current_description, 160),
            "requires_approval": True,
        })

    if product.get("missing_alt", 0) > 0:
        recommendations.append({
            "type": "image_alt_text",
            "priority": "medium",
            "reason": f"{product['missing_alt']} product image(s) have no alt text.",
            "current": None,
            "proposed": None,
            "requires_approval": True,
        })

    return recommendations


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
    result = {
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
    result["recommendations"] = build_recommendations(result | {"description": product.get("description", "")})
    return result


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
