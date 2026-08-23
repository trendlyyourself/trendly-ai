from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps.auth import get_current_user
from app.services.shopify import ShopifyAPIError, ShopifyClient, ShopifyConfigurationError

router = APIRouter(prefix="/shopify", tags=["shopify"])


@router.get("/products")
async def get_shopify_products(
    first: int = Query(default=50, ge=1, le=50),
    current_user=Depends(get_current_user),
):
    """Read-only Shopify product catalog access for the first SEO scanner milestone."""
    del current_user
    try:
        data = await ShopifyClient().list_products(first=first)
    except ShopifyConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ShopifyAPIError as exc:
        raise HTTPException(status_code=502, detail="Shopify API request failed") from exc
    return data
