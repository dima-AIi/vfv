"""CRM domain event contracts (10_Event_Architecture.md, MVP CRM Events).

Published after the business transaction commits, through the shared
in-process dispatcher.
"""

from app.core.events import build_event, publish_event
from app.modules.crm.models import Customer

SOURCE_MODULE = "CRM"


def _payload(customer: Customer) -> dict[str, object]:
    return {
        "customerId": str(customer.id),
        "organizationId": (
            str(customer.organization_id) if customer.organization_id is not None else None
        ),
        "status": customer.status,
        "name": customer.name,
    }


async def publish_customer_created(customer: Customer) -> None:
    await publish_event(
        build_event(
            event_type="CustomerCreated",
            organization_id=customer.organization_id,
            aggregate_id=customer.id,
            payload=_payload(customer),
            source_module=SOURCE_MODULE,
        ),
    )


async def publish_customer_updated(customer: Customer) -> None:
    await publish_event(
        build_event(
            event_type="CustomerUpdated",
            organization_id=customer.organization_id,
            aggregate_id=customer.id,
            payload=_payload(customer),
            source_module=SOURCE_MODULE,
        ),
    )


async def publish_customer_archived(customer: Customer) -> None:
    await publish_event(
        build_event(
            event_type="CustomerArchived",
            organization_id=customer.organization_id,
            aggregate_id=customer.id,
            payload=_payload(customer),
            source_module=SOURCE_MODULE,
        ),
    )
