import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ValidationError
from app.core.pagination import PageParams
from app.modules.crm.events import (
    publish_customer_archived,
    publish_customer_created,
    publish_customer_updated,
)
from app.modules.crm.models import Customer, CustomerNote
from app.modules.crm.repository import (
    CompanyRepository,
    ContactRepository,
    CustomerNoteRepository,
    CustomerRepository,
    TagRepository,
)
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
    CustomerSearchResult,
    CustomerUpdate,
    TagOut,
)
from app.modules.identity.deps import OrgContext
from app.modules.identity.service import IdentityService

CUSTOMER_STATUSES = ("lead", "active", "archived")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
NOTE_DELETE_PERMISSION = "crm.customer.delete"


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = CustomerRepository(session)
        self.company_repository = CompanyRepository(session)
        self.contact_repository = ContactRepository(session)
        self.note_repository = CustomerNoteRepository(session)
        self.tag_repository = TagRepository(session)
        self.identity_service = IdentityService(session)

    async def create_customer(
        self, data: CustomerCreate, context: OrgContext
    ) -> CustomerOut:
        self._validate_status(data.status)
        if data.company_id is not None:
            await self.company_repository.get(data.company_id, context.scope)
        customer = await self.repository.create(
            name=data.name,
            description=data.description,
            status=data.status,
            company_id=data.company_id,
            organization_id=context.organization_id,
        )
        await publish_customer_created(customer)
        return await self._to_out(customer)

    async def get_customer(
        self, customer_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> CustomerOut:
        customer = await self.repository.get(customer_id, scope)
        return await self._to_out(customer)

    async def get_model(self, customer_id: uuid.UUID, scope: uuid.UUID | None = None) -> Customer:
        return await self.repository.get(customer_id, scope)

    async def list_customers(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
        status: str | None = None,
        term: str | None = None,
    ) -> tuple[list[CustomerOut], int]:
        if status is not None:
            self._validate_status(status)
        customers, total = await self.repository.list_page(params, scope, status, term)
        return [await self._to_out(c) for c in customers], total

    async def update_customer(
        self, customer_id: uuid.UUID, data: CustomerUpdate, scope: uuid.UUID | None = None
    ) -> CustomerOut:
        customer = await self.repository.get(customer_id, scope)
        if data.status is not None:
            self._validate_status(data.status)
            customer.status = data.status
        if data.name is not None:
            customer.name = data.name
        if data.description is not None:
            customer.description = data.description
        if "company_id" in data.model_fields_set:
            if data.company_id is not None:
                await self.company_repository.get(data.company_id, scope)
            customer.company_id = data.company_id
        customer = await self.repository.save(customer)
        await publish_customer_updated(customer)
        return await self._to_out(customer)

    async def archive(self, customer_id: uuid.UUID, scope: uuid.UUID | None = None) -> CustomerOut:
        customer = await self.repository.get(customer_id, scope)
        customer.status = "archived"
        customer = await self.repository.save(customer)
        await publish_customer_archived(customer)
        return await self._to_out(customer)

    async def restore(self, customer_id: uuid.UUID, scope: uuid.UUID | None = None) -> CustomerOut:
        customer = await self.repository.get(customer_id, scope)
        customer.status = "active"
        customer = await self.repository.save(customer)
        await publish_customer_updated(customer)
        return await self._to_out(customer)

    async def delete_customer(self, customer_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        customer = await self.repository.get(customer_id, scope)
        await self.repository.soft_delete(customer)

    async def search(
        self, term: str, limit: int, scope: uuid.UUID | None = None
    ) -> list[CustomerSearchResult]:
        customers = await self.repository.search(term, limit, scope)
        return [CustomerSearchResult.model_validate(c) for c in customers]

    async def add_contact(
        self, customer_id: uuid.UUID, data: ContactCreate, context: OrgContext
    ) -> ContactOut:
        customer = await self.repository.get(customer_id, context.scope)
        self._validate_email(data.email)
        contact = await self.contact_repository.create(
            customer_id=customer.id,
            organization_id=customer.organization_id,
            name=data.name,
            email=data.email,
            phone=data.phone,
        )
        return ContactOut.model_validate(contact)

    async def list_contacts(
        self, customer_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> list[ContactOut]:
        await self.repository.get(customer_id, scope)
        contacts = await self.contact_repository.list_for_customer(customer_id, scope)
        return [ContactOut.model_validate(c) for c in contacts]

    async def delete_contact(
        self, contact_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> None:
        contact = await self.contact_repository.get(contact_id, scope)
        await self.contact_repository.soft_delete(contact)

    async def add_note(
        self, customer_id: uuid.UUID, data: CustomerNoteCreate, context: OrgContext
    ) -> CustomerNoteOut:
        customer = await self.repository.get(customer_id, context.scope)
        note = await self.note_repository.create(
            customer_id=customer.id,
            organization_id=customer.organization_id,
            author_id=context.user.id,
            body=data.body,
        )
        return await self._note_to_out(note)

    async def list_notes(
        self, customer_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> list[CustomerNoteOut]:
        await self.repository.get(customer_id, scope)
        notes = await self.note_repository.list_for_customer(customer_id, scope)
        author_ids = list({n.author_id for n in notes if n.author_id is not None})
        names = await self.identity_service.get_display_names(author_ids)
        outs: list[CustomerNoteOut] = []
        for note in notes:
            out = CustomerNoteOut.model_validate(note)
            if note.author_id is not None:
                out.author_name = names.get(note.author_id)
            outs.append(out)
        return outs

    async def delete_note(
        self, note_id: uuid.UUID, context: OrgContext
    ) -> None:
        note = await self.note_repository.get(note_id, context.scope)
        if note.author_id == context.user.id:
            await self.note_repository.soft_delete(note)
            return
        allowed = context.is_platform_admin or await context.rbac.check_user_permission(
            context.user.id, NOTE_DELETE_PERMISSION, note.organization_id
        )
        if not allowed:
            raise AppError(
                "Удалить заметку может только её автор или пользователь с правом удаления.",
                code="NOTE_DELETE_FORBIDDEN",
                status_code=403,
            )
        await self.note_repository.soft_delete(note)

    async def attach_tag(
        self, customer_id: uuid.UUID, tag_id: uuid.UUID, context: OrgContext
    ) -> CustomerOut:
        customer = await self.repository.get(customer_id, context.scope)
        await self.tag_repository.get(tag_id, context.scope)
        await self.tag_repository.attach(customer.id, tag_id)
        return await self._to_out(customer)

    async def detach_tag(
        self, customer_id: uuid.UUID, tag_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> CustomerOut:
        customer = await self.repository.get(customer_id, scope)
        await self.tag_repository.get(tag_id, scope)
        await self.tag_repository.detach(customer.id, tag_id)
        return await self._to_out(customer)

    async def _to_out(self, customer: Customer) -> CustomerOut:
        out = CustomerOut.model_validate(customer)
        if customer.company_id is not None:
            company = await self.company_repository.get_optional(customer.company_id)
            if company is not None:
                out.company = CompanyOut.model_validate(company)
                out.company_name = company.name
        tags = await self.tag_repository.tags_for_customer(customer.id)
        out.tags = [TagOut.model_validate(t) for t in tags]
        return out

    async def _note_to_out(self, note: CustomerNote) -> CustomerNoteOut:
        out = CustomerNoteOut.model_validate(note)
        if note.author_id is not None:
            names = await self.identity_service.get_display_names([note.author_id])
            out.author_name = names.get(note.author_id)
        return out

    def _validate_status(self, status: str) -> None:
        if status not in CUSTOMER_STATUSES:
            raise ValidationError(
                "Недопустимый статус клиента.",
                code="INVALID_STATUS",
            )

    def _validate_email(self, email: str | None) -> None:
        if email is not None and not EMAIL_PATTERN.match(email):
            raise ValidationError(
                "Некорректный формат email контакта.",
                code="INVALID_CONTACT_EMAIL",
            )


class TagService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = TagRepository(session)

    async def create_tag(self, name: str, context: OrgContext) -> TagOut:
        existing = await self.repository.find_by_name(name, context.organization_id)
        if existing is not None:
            raise AppError(
                "Тег с таким названием уже существует в организации.",
                code="TAG_NAME_EXISTS",
                status_code=409,
            )
        tag = await self.repository.create(name=name, organization_id=context.organization_id)
        return TagOut.model_validate(tag)

    async def list_tags(self, scope: uuid.UUID | None = None) -> list[TagOut]:
        tags = await self.repository.list_all(scope)
        return [TagOut.model_validate(t) for t in tags]

    async def delete_tag(self, tag_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        tag = await self.repository.get(tag_id, scope)
        await self.repository.delete(tag)


class CompanyService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = CompanyRepository(session)

    async def create(self, data: CompanyCreate, context: OrgContext) -> CompanyOut:
        company = await self.repository.create(data.name, context.organization_id)
        return CompanyOut.model_validate(company)

    async def list(
        self, params: PageParams, scope: uuid.UUID | None = None, term: str | None = None
    ) -> tuple[list[CompanyOut], int]:
        companies, total = await self.repository.list(params, scope, term)
        return [CompanyOut.model_validate(c) for c in companies], total

    async def get(self, company_id: uuid.UUID, scope: uuid.UUID | None = None) -> CompanyOut:
        company = await self.repository.get(company_id, scope)
        return CompanyOut.model_validate(company)

    async def update(
        self, company_id: uuid.UUID, data: CompanyUpdate, scope: uuid.UUID | None = None
    ) -> CompanyOut:
        company = await self.repository.get(company_id, scope)
        company = await self.repository.update(company, data.name)
        return CompanyOut.model_validate(company)

    async def delete(self, company_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        company = await self.repository.get(company_id, scope)
        await self.repository.soft_delete(company)
