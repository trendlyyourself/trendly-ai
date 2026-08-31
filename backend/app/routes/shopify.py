from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps.auth import get_current_user
from app.services.shopify import ShopifyAPIError, ShopifyClient, ShopifyConfigurationError
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db.sqlite import get_db
from app.deps.auth import get_current_user
from app.services.shopify import decrypt_token, encrypt_token, normalize_shop_domain, graphql, scan_products

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
class ConnectRequest(BaseModel):
    workspace_id: int
    shop_domain: str = Field(min_length=1, max_length=255)
    access_token: str = Field(min_length=10, max_length=500)


def _owned_workspace(conn, workspace_id: int, user_id: int):
    return conn.execute(
        "SELECT id FROM workspaces WHERE id = ? AND user_id = ?",
        (workspace_id, user_id),
    ).fetchone()


@router.get("/connection")
def get_connection(workspace_id: int, current_user=Depends(get_current_user)):
    with get_db() as conn:
        if not _owned_workspace(conn, workspace_id, current_user["id"]):
            raise HTTPException(status_code=404, detail="Workspace not found")
        row = conn.execute(
            "SELECT shop_domain, created_at, updated_at FROM shopify_connections WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
    if not row:
        return {"connected": False}
    return {
        "connected": True,
        "shop_domain": row["shop_domain"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.post("/connection")
async def connect(payload: ConnectRequest, current_user=Depends(get_current_user)):
    try:
        shop_domain = normalize_shop_domain(payload.shop_domain)
        encrypted = encrypt_token(payload.access_token.strip())
        await graphql(shop_domain, payload.access_token.strip(), "query { shop { name } }")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Shopify connection failed: {exc}")

    with get_db() as conn:
        if not _owned_workspace(conn, payload.workspace_id, current_user["id"]):
            raise HTTPException(status_code=404, detail="Workspace not found")
        conn.execute(
            """
            INSERT INTO shopify_connections (workspace_id, shop_domain, access_token_encrypted)
            VALUES (?, ?, ?)
            ON CONFLICT(workspace_id) DO UPDATE SET
                shop_domain = excluded.shop_domain,
                access_token_encrypted = excluded.access_token_encrypted,
                updated_at = CURRENT_TIMESTAMP
            """,
            (payload.workspace_id, shop_domain, encrypted),
        )
        conn.commit()
    return {"connected": True, "shop_domain": shop_domain}


@router.delete("/connection")
def disconnect(workspace_id: int, current_user=Depends(get_current_user)):
    with get_db() as conn:
        if not _owned_workspace(conn, workspace_id, current_user["id"]):
            raise HTTPException(status_code=404, detail="Workspace not found")
        conn.execute("DELETE FROM shopify_connections WHERE workspace_id = ?", (workspace_id,))
        conn.commit()
    return {"connected": False}


@router.post("/scan")
async def scan(workspace_id: int, current_user=Depends(get_current_user)):
    with get_db() as conn:
        if not _owned_workspace(conn, workspace_id, current_user["id"]):
            raise HTTPException(status_code=404, detail="Workspace not found")
        row = conn.execute(
            "SELECT shop_domain, access_token_encrypted FROM shopify_connections WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=409, detail="Connect a Shopify store before scanning")

    try:
        products = await scan_products(row["shop_domain"], decrypt_token(row["access_token_encrypted"]))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Shopify scan failed: {exc}")

    issue_count = sum(len(product["issues"]) for product in products)
    average_score = round(sum(p["score"] for p in products) / len(products)) if products else 100
    return {
        "shop_domain": row["shop_domain"],
        "product_count": len(products),
        "issue_count": issue_count,
        "average_score": average_score,
        "products": products,
    }
