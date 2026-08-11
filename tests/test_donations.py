import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Donation, SupplyInventory

@pytest.mark.asyncio
async def test_donate_medicine_updates_inventory():
    transport = ASGITransport(app=app)
    
    # 1. Check initial inventory count for Medical Kits
    async with SessionLocal() as db:
        res = await db.execute(select(SupplyInventory).where(SupplyInventory.item_name == "Medical Kits"))
        item = res.scalars().first()
        initial_qty = item.quantity if item else 0
        
    form_data = {
        "donor_name": "Test NGO Union",
        "item_type": "Medicine",
        "quantity": "250"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/resources/donate", data=form_data)
        
    assert response.status_code == 303
    
    # 2. Check donation database log
    async with SessionLocal() as db:
        res = await db.execute(select(Donation).where(Donation.donor_name == "Test NGO Union"))
        don = res.scalars().first()
        assert don is not None
        assert don.item_type == "Medicine"
        assert don.quantity == 250
        
        # Check that supply inventory was incremented by 250
        res_inv = await db.execute(select(SupplyInventory).where(SupplyInventory.item_name == "Medical Kits"))
        item_new = res_inv.scalars().first()
        assert item_new is not None
        assert item_new.quantity == initial_qty + 250

@pytest.mark.asyncio
async def test_donate_water_updates_inventory():
    transport = ASGITransport(app=app)
    
    async with SessionLocal() as db:
        res = await db.execute(select(SupplyInventory).where(SupplyInventory.item_name == "Drinking Water"))
        item = res.scalars().first()
        initial_qty = item.quantity if item else 0
        
    form_data = {
        "donor_name": "Water Coalition",
        "item_type": "Water",
        "quantity": "1000"
    }
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/resources/donate", data=form_data)
        
    assert response.status_code == 303
    
    async with SessionLocal() as db:
        res_inv = await db.execute(select(SupplyInventory).where(SupplyInventory.item_name == "Drinking Water"))
        item_new = res_inv.scalars().first()
        assert item_new.quantity == initial_qty + 1000
