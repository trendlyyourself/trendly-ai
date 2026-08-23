from fastapi import APIRouter, HTTPException, Query

from app.services.shopify import ShopifyAPIError, ShopifyClient, ShopifyConfigurationError

router = APIRouter(prefix="/shopify", tags=["shopify"])


@router.get("/products")
async def get_shopify_products(first: int = Query(default=50, ge=1, le=50)):
    """Read-only Shopify product catalog access for the first SEO scanner milestone."""
    try:
        data = await ShopifyClient().list_products(first=first)
    except ShopifyConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ShopifyAPIError as exc:
        raise HTTPException(status_code=502, detail="Shopify API request failed") from exc
    return data
