"""Small HTML presenters used by HTMX fragment responses."""

from html import escape

from app.models import Donation, Shelter


def render_shelter_card(shelter: Shelter) -> str:
    badge_class = {
        "Open": "bg-success",
        "Full": "bg-danger",
    }.get(shelter.status, "bg-secondary")
    return f"""
    <div class="card mb-2">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h5 class="card-title mb-1">{escape(shelter.name)}</h5>
                    <p class="card-text text-muted mb-1">Location: {escape(shelter.location or 'N/A')}</p>
                    <p class="card-text mb-1">Capacity: <strong>{shelter.capacity_available}</strong> / {shelter.capacity_total} beds available</p>
                    <p class="card-text mb-1">Facilities: {escape(shelter.facilities or 'N/A')}</p>
                    <p class="card-text mb-0">Food Stock: {escape(shelter.food_stock or 'N/A')}</p>
                    <small class="text-muted">Contact: {escape(shelter.contact_details or 'N/A')}</small>
                </div>
                <div class="text-end"><span class="badge {badge_class}">{escape(shelter.status)}</span></div>
            </div>
            <form hx-post="/shelters/update" hx-target="closest .card" hx-swap="outerHTML" class="mt-2">
                <input type="hidden" name="shelter_id" value="{shelter.id}">
                <div class="input-group input-group-sm">
                    <span class="input-group-text">Beds</span>
                    <input type="number" class="form-control" name="capacity_available" value="{shelter.capacity_available}" min="0" max="{shelter.capacity_total}">
                    <button class="btn btn-outline-primary" type="submit">Update</button>
                </div>
            </form>
        </div>
    </div>
    """


def render_donation_card(donation: Donation) -> str:
    title = donation.item_name or donation.item_type or "Donation"
    return f"""
    <div class="card mb-2">
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h5 class="card-title mb-1">{escape(title)}</h5>
                    <p class="card-text text-muted mb-1">{donation.quantity} {escape(donation.unit or '')}</p>
                    <p class="card-text mb-0">Donor: {escape(donation.donor_name)}</p>
                    <small class="text-muted">Location: {escape(donation.location or 'N/A')}</small>
                </div>
                <div><span class="badge bg-info">{escape(donation.status)}</span></div>
            </div>
        </div>
    </div>
    """
