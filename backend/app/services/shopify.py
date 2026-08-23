from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


class ShopifyConfigurationError(RuntimeError):
    pass


class ShopifyAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class ShopifyConfig:
    store_domain: str
    access_token: str
    api_version: str = "2026-07"

    @classmethod
    def from_env(cls) -> "ShopifyConfig":
        domain = os.getenv("SHOPIFY_STORE_DOMAIN", "").strip()
        token = os.getenv("SHOPIFY_ACCESS_TOKEN", "").strip()
        version = os.getenv("SHOPIFY_API_VERSION", "2026-07").strip() or "2026-07"
        if not domain or not token:
            raise ShopifyConfigurationError(
                "SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN must be configured"
            )
        domain = domain.removeprefix("https://").removeprefix("http://").rstrip("/")
        if not domain.endswith(".myshopify.com"):
            raise ShopifyConfigurationError("SHOPIFY_STORE_DOMAIN must be a *.myshopify.com domain")
        return cls(domain, token, version)


PRODUCT_QUERY = """
query Products($first: Int!, $after: String) {
  products(first: $first, after: $after) {
    edges {
      cursor
      node {
        id
        title
        handle
        status
        vendor
        productType
        seo {
          title
          description
        }
        featuredImage {
          id
          altText
        }
        totalInventory
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""


class ShopifyClient:
    def __init__(self, config: ShopifyConfig | None = None) -> None:
        self.config = config or ShopifyConfig.from_env()
        self.url = (
            f"https://{self.config.store_domain}/admin/api/"
            f"{self.config.api_version}/graphql.json"
        )

    async def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.config.access_token,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    self.url,
                    headers=headers,
                    json={"query": query, "variables": variables},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ShopifyAPIError("Shopify API request failed") from exc

        if payload.get("errors"):
            raise ShopifyAPIError(str(payload["errors"]))
        if not payload.get("data"):
            raise ShopifyAPIError("Shopify API returned no data")
        return payload["data"]

    async def list_products(self, first: int = 50) -> dict[str, Any]:
        first = max(1, min(first, 50))
        return await self._graphql(PRODUCT_QUERY, {"first": first, "after": None})
