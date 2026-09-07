import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.pagination import PageParams, get_page_params
from app.modules.crm.schemas import (
    CompanyCreate,
    CompanyOut,
    CompanyUpdate,
    ContactCreate,
    ContactOut,
    CustomerCreate,
    CustomerNoteCreate,
    CustomerNoteOut,
    CustomerOut,
    CustomerUpdate,
    TagAttach,
    TagCreate,
    TagOut,
)
from app.modules.crm.service import CompanyService, CustomerService, TagService
from app.modules.identity.deps import OrgContext, require_permission

router = APIRouter(tags=["crm"])


def get_customer_service(session: AsyncSession = Depends(get_session)) -> CustomerService:
    return CustomerService(session)


def get_tag_service(session: AsyncSession = Depends(get_session)) -> TagService:
    return TagService(session)


def get_company_service(session: AsyncSession = Depends(get_session)) -> CompanyService:
    return CompanyService(session)


@router.post("/customers", status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    context: OrgContext = Depends(require_permission("crm.customer.create")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[CustomerOut]:
    return Envelope(data=await service.create_customer(data, context))


@router.get("/customers")
async def list_customers(
    params: PageParams = Depends(get_page_params),
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = None,
    context: OrgContext = Depends(require_permission("crm.customer.read")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[list[CustomerOut]]:
    customers, total = await service.list_customers(
        params, context.scope, status=status_filter, term=q
    )
    return Envelope(
        data=customers,
        meta=pagination_meta(
            page=params.page, page_size=params.page_size, total_items=total
        ),
    )


@router.get("/customers/{customer_id}")
async def get_customer(
    customer_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.read")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[CustomerOut]:
    return Envelope(data=await service.get_customer(customer_id, context.scope))


@router.patch("/customers/{customer_id}")
async def update_customer(
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    context: OrgContext = Depends(require_permission("crm.customer.update")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[CustomerOut]:
    return Envelope(data=await service.update_customer(customer_id, data, context.scope))


@router.post("/customers/{customer_id}/archive")
async def archive_customer(
    customer_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.update")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[CustomerOut]:
    return Envelope(data=await service.archive(customer_id, context.scope))


@router.post("/customers/{customer_id}/restore")
async def restore_customer(
    customer_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.update")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[CustomerOut]:
    return Envelope(data=await service.restore(customer_id, context.scope))


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.delete")),
    service: CustomerService = Depends(get_customer_service),
) -> None:
    await service.delete_customer(customer_id, context.scope)


@router.post("/customers/{customer_id}/contacts", status_code=status.HTTP_201_CREATED)
async def add_contact(
    customer_id: uuid.UUID,
    data: ContactCreate,
    context: OrgContext = Depends(require_permission("crm.customer.create")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[ContactOut]:
    return Envelope(data=await service.add_contact(customer_id, data, context))


@router.get("/customers/{customer_id}/contacts")
async def list_contacts(
    customer_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.read")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[list[ContactOut]]:
    return Envelope(data=await service.list_contacts(customer_id, context.scope))


@router.delete(
    "/customers/{customer_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.delete")),
    service: CustomerService = Depends(get_customer_service),
) -> None:
    await service.delete_contact(contact_id, context.scope)


@router.post("/customers/{customer_id}/notes", status_code=status.HTTP_201_CREATED)
async def add_note(
    customer_id: uuid.UUID,
    data: CustomerNoteCreate,
    context: OrgContext = Depends(require_permission("crm.customer.create")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[CustomerNoteOut]:
    return Envelope(data=await service.add_note(customer_id, data, context))


@router.get("/customers/{customer_id}/notes")
async def list_notes(
    customer_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.read")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[list[CustomerNoteOut]]:
    return Envelope(data=await service.list_notes(customer_id, context.scope))


@router.delete(
    "/customers/{customer_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_note(
    customer_id: uuid.UUID,
    note_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.read")),
    service: CustomerService = Depends(get_customer_service),
) -> None:
    await service.delete_note(note_id, context)


@router.post("/customers/{customer_id}/tags")
async def attach_tag(
    customer_id: uuid.UUID,
    data: TagAttach,
    context: OrgContext = Depends(require_permission("crm.customer.update")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[CustomerOut]:
    return Envelope(data=await service.attach_tag(customer_id, data.tag_id, context))


@router.delete("/customers/{customer_id}/tags/{tag_id}")
async def detach_tag(
    customer_id: uuid.UUID,
    tag_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.update")),
    service: CustomerService = Depends(get_customer_service),
) -> Envelope[CustomerOut]:
    return Envelope(data=await service.detach_tag(customer_id, tag_id, context.scope))


@router.post("/tags", status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    context: OrgContext = Depends(require_permission("crm.customer.create")),
    service: TagService = Depends(get_tag_service),
) -> Envelope[TagOut]:
    return Envelope(data=await service.create_tag(data.name, context))


@router.get("/tags")
async def list_tags(
    context: OrgContext = Depends(require_permission("crm.customer.read")),
    service: TagService = Depends(get_tag_service),
) -> Envelope[list[TagOut]]:
    return Envelope(data=await service.list_tags(context.scope))


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.delete")),
    service: TagService = Depends(get_tag_service),
) -> None:
    await service.delete_tag(tag_id, context.scope)


@router.post("/companies", status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    context: OrgContext = Depends(require_permission("crm.customer.create")),
    service: CompanyService = Depends(get_company_service),
) -> Envelope[CompanyOut]:
    return Envelope(data=await service.create(data, context))


@router.get("/companies")
async def list_companies(
    params: PageParams = Depends(get_page_params),
    q: str | None = None,
    context: OrgContext = Depends(require_permission("crm.customer.read")),
    service: CompanyService = Depends(get_company_service),
) -> Envelope[list[CompanyOut]]:
    companies, total = await service.list(params, context.scope, q)
    return Envelope(
        data=companies,
        meta=pagination_meta(
            page=params.page, page_size=params.page_size, total_items=total
        ),
    )


@router.get("/companies/{company_id}")
async def get_company(
    company_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.read")),
    service: CompanyService = Depends(get_company_service),
) -> Envelope[CompanyOut]:
    return Envelope(data=await service.get(company_id, context.scope))


@router.patch("/companies/{company_id}")
async def update_company(
    company_id: uuid.UUID,
    data: CompanyUpdate,
    context: OrgContext = Depends(require_permission("crm.customer.update")),
    service: CompanyService = Depends(get_company_service),
) -> Envelope[CompanyOut]:
    return Envelope(data=await service.update(company_id, data, context.scope))


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("crm.customer.delete")),
    service: CompanyService = Depends(get_company_service),
) -> None:
    await service.delete(company_id, context.scope)
