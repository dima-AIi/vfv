import uuid

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.models import utcnow
from app.core.pagination import PageParams
from app.core.search import LIKE_ESCAPE, like_contains
from app.modules.crm.models import Company, Contact, Customer, CustomerNote, CustomerTag, Tag


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, organization_id: uuid.UUID | None) -> Company:
        company = Company(name=name, organization_id=organization_id)
        self._session.add(company)
        await self._session.commit()
        await self._session.refresh(company)
        return company

    async def get(self, company_id: uuid.UUID, scope: uuid.UUID | None = None) -> Company:
        query = select(Company).where(Company.id == company_id, Company.deleted_at.is_(None))
        if scope is not None:
            query = query.where(Company.organization_id == scope)
        result = await self._session.execute(query)
        company = result.scalar_one_or_none()
        if company is None:
            raise NotFoundError("Компания не найдена.", code="COMPANY_NOT_FOUND")
        return company

    async def get_optional(self, company_id: uuid.UUID) -> Company | None:
        return await self._session.get(Company, company_id)

    async def list(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
        term: str | None = None,
    ) -> tuple[list[Company], int]:
        from app.core.search import LIKE_ESCAPE, like_contains

        active = Company.deleted_at.is_(None)
        query: Select[tuple[Company]] = (
            select(Company).where(active).order_by(Company.created_at.desc())
        )
        count_query = select(func.count()).select_from(Company).where(active)
        if scope is not None:
            query = query.where(Company.organization_id == scope)
            count_query = count_query.where(Company.organization_id == scope)
        if term is not None:
            pattern = like_contains(term)
            query = query.where(func.lower(Company.name).like(pattern, escape=LIKE_ESCAPE))
            count_query = count_query.where(
                func.lower(Company.name).like(pattern, escape=LIKE_ESCAPE)
            )
        query = query.limit(params.page_size).offset(params.offset)
        items = await self._session.execute(query)
        total = await self._session.execute(count_query)
        return list(items.scalars().all()), int(total.scalar_one())

    async def update(self, company: Company, name: str) -> Company:
        company.name = name
        await self._session.commit()
        await self._session.refresh(company)
        return company

    async def soft_delete(self, company: Company) -> None:
        company.deleted_at = utcnow()
        await self._session.commit()


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        description: str,
        status: str,
        company_id: uuid.UUID | None,
        organization_id: uuid.UUID | None,
    ) -> Customer:
        customer = Customer(
            name=name,
            description=description,
            status=status,
            company_id=company_id,
            organization_id=organization_id,
        )
        self._session.add(customer)
        await self._session.commit()
        await self._session.refresh(customer)
        return customer

    async def get(self, customer_id: uuid.UUID, scope: uuid.UUID | None = None) -> Customer:
        query = select(Customer).where(
            Customer.id == customer_id, Customer.deleted_at.is_(None)
        )
        if scope is not None:
            query = query.where(Customer.organization_id == scope)
        result = await self._session.execute(query)
        customer = result.scalar_one_or_none()
        if customer is None:
            raise NotFoundError("Клиент не найден.", code="CUSTOMER_NOT_FOUND")
        return customer

    async def list_page(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
        status: str | None = None,
        term: str | None = None,
    ) -> tuple[list[Customer], int]:
        active = Customer.deleted_at.is_(None)
        query: Select[tuple[Customer]] = select(Customer).where(active)
        count_query = select(func.count()).select_from(Customer).where(active)
        if scope is not None:
            query = query.where(Customer.organization_id == scope)
            count_query = count_query.where(Customer.organization_id == scope)
        if status is not None:
            query = query.where(Customer.status == status)
            count_query = count_query.where(Customer.status == status)
        if term is not None:
            pattern = like_contains(term)
            clause = or_(
                func.lower(Customer.name).like(pattern, escape=LIKE_ESCAPE),
                func.lower(Customer.description).like(pattern, escape=LIKE_ESCAPE),
            )
            query = query.where(clause)
            count_query = count_query.where(clause)
        order = Customer.created_at.desc() if params.descending else Customer.created_at.asc()
        query = query.order_by(order).limit(params.page_size).offset(params.offset)
        items = await self._session.execute(query)
        total = await self._session.execute(count_query)
        return list(items.scalars().all()), int(total.scalar_one())

    async def search(
        self, term: str, limit: int, scope: uuid.UUID | None = None
    ) -> list[Customer]:
        pattern = like_contains(term)
        clause = or_(
            func.lower(Customer.name).like(pattern, escape=LIKE_ESCAPE),
            func.lower(Customer.description).like(pattern, escape=LIKE_ESCAPE),
        )
        query = (
            select(Customer)
            .where(Customer.deleted_at.is_(None), clause)
            .order_by(Customer.created_at.desc())
            .limit(limit)
        )
        if scope is not None:
            query = query.where(Customer.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, customer: Customer) -> None:
        customer.deleted_at = utcnow()
        await self._session.commit()

    async def save(self, customer: Customer) -> Customer:
        await self._session.commit()
        await self._session.refresh(customer)
        return customer


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        customer_id: uuid.UUID,
        organization_id: uuid.UUID | None,
        name: str,
        email: str | None,
        phone: str | None,
    ) -> Contact:
        contact = Contact(
            customer_id=customer_id,
            organization_id=organization_id,
            name=name,
            email=email,
            phone=phone,
        )
        self._session.add(contact)
        await self._session.commit()
        await self._session.refresh(contact)
        return contact

    async def get(self, contact_id: uuid.UUID, scope: uuid.UUID | None = None) -> Contact:
        query = select(Contact).where(Contact.id == contact_id, Contact.deleted_at.is_(None))
        if scope is not None:
            query = query.where(Contact.organization_id == scope)
        result = await self._session.execute(query)
        contact = result.scalar_one_or_none()
        if contact is None:
            raise NotFoundError("Контакт не найден.", code="CONTACT_NOT_FOUND")
        return contact

    async def list_for_customer(
        self, customer_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> list[Contact]:
        query = (
            select(Contact)
            .where(Contact.customer_id == customer_id, Contact.deleted_at.is_(None))
            .order_by(Contact.created_at.asc())
        )
        if scope is not None:
            query = query.where(Contact.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, contact: Contact) -> None:
        contact.deleted_at = utcnow()
        await self._session.commit()


class CustomerNoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        customer_id: uuid.UUID,
        organization_id: uuid.UUID | None,
        author_id: uuid.UUID | None,
        body: str,
    ) -> CustomerNote:
        note = CustomerNote(
            customer_id=customer_id,
            organization_id=organization_id,
            author_id=author_id,
            body=body,
        )
        self._session.add(note)
        await self._session.commit()
        await self._session.refresh(note)
        return note

    async def get(
        self, note_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> CustomerNote:
        query = select(CustomerNote).where(
            CustomerNote.id == note_id, CustomerNote.deleted_at.is_(None)
        )
        if scope is not None:
            query = query.where(CustomerNote.organization_id == scope)
        result = await self._session.execute(query)
        note = result.scalar_one_or_none()
        if note is None:
            raise NotFoundError("Заметка не найдена.", code="NOTE_NOT_FOUND")
        return note

    async def list_for_customer(
        self, customer_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> list[CustomerNote]:
        query = (
            select(CustomerNote)
            .where(CustomerNote.customer_id == customer_id, CustomerNote.deleted_at.is_(None))
            .order_by(CustomerNote.created_at.asc())
        )
        if scope is not None:
            query = query.where(CustomerNote.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, note: CustomerNote) -> None:
        note.deleted_at = utcnow()
        await self._session.commit()


class TagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, name: str, organization_id: uuid.UUID | None) -> Tag:
        tag = Tag(name=name, organization_id=organization_id)
        self._session.add(tag)
        await self._session.commit()
        await self._session.refresh(tag)
        return tag

    async def get(self, tag_id: uuid.UUID, scope: uuid.UUID | None = None) -> Tag:
        query = select(Tag).where(Tag.id == tag_id)
        if scope is not None:
            query = query.where(Tag.organization_id == scope)
        result = await self._session.execute(query)
        tag = result.scalar_one_or_none()
        if tag is None:
            raise NotFoundError("Тег не найден.", code="TAG_NOT_FOUND")
        return tag

    async def find_by_name(
        self, name: str, organization_id: uuid.UUID | None
    ) -> Tag | None:
        query = select(Tag).where(Tag.name == name)
        if organization_id is not None:
            query = query.where(Tag.organization_id == organization_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self, scope: uuid.UUID | None = None) -> list[Tag]:
        query = select(Tag).order_by(Tag.name.asc())
        if scope is not None:
            query = query.where(Tag.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def delete(self, tag: Tag) -> None:
        await self._session.delete(tag)
        await self._session.commit()

    async def attach(self, customer_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        exists = await self._session.execute(
            select(CustomerTag).where(
                CustomerTag.customer_id == customer_id, CustomerTag.tag_id == tag_id
            )
        )
        if exists.scalar_one_or_none() is None:
            self._session.add(CustomerTag(customer_id=customer_id, tag_id=tag_id))
            await self._session.commit()

    async def detach(self, customer_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(CustomerTag).where(
                CustomerTag.customer_id == customer_id, CustomerTag.tag_id == tag_id
            )
        )
        await self._session.commit()

    async def tags_for_customer(self, customer_id: uuid.UUID) -> list[Tag]:
        result = await self._session.execute(
            select(Tag)
            .join(CustomerTag, CustomerTag.tag_id == Tag.id)
            .where(CustomerTag.customer_id == customer_id)
            .order_by(Tag.name.asc())
        )
        return list(result.scalars().all())
