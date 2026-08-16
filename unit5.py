import asyncio
from dataclasses import dataclass

import aiohttp
from sqlalchemy import (
    create_engine,
    String,
    Integer,
    Float,
    Text,
    ForeignKey,
    select
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker
)

DATABASE_URL = "sqlite:///products.db"

engine = create_engine(
    DATABASE_URL,
    echo=False
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    products: Mapped[list["Product"]] = relationship(
        back_populates="brand"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    products: Mapped[list["Product"]] = relationship(
        back_populates="category"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        Text
    )

    price: Mapped[float] = mapped_column(
        Float
    )

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id")
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id")
    )

    brand: Mapped["Brand"] = relationship(
        back_populates="products"
    )

    category: Mapped["Category"] = relationship(
        back_populates="products"
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    rating: Mapped[int] = mapped_column(
        Integer
    )

    comment: Mapped[str] = mapped_column(
        Text
    )

    reviewer_name: Mapped[str] = mapped_column(
        String(255)
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )

    product: Mapped["Product"] = relationship(
        back_populates="reviews"
    )



@dataclass
class ProductDTO:
    id: int
    title: str
    description: str
    price: float
    brand: str
    category: str


async def get_products_from_dummyjson():

    url = "https://dummyjson.com/products?limit=0"

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as response:

            response.raise_for_status()

            data = await response.json()

            return data["products"]



async def save_data_to_database():

    products_data = await get_products_from_dummyjson()

    with SessionLocal() as session:

        for item in products_data:



            brand = session.execute(
                select(Brand).where(
                    brand_name = item.get("brand", "Без бренда")

                    brand = session.execute(
                        select(Brand).where(
                            Brand.name == brand_name
                        )
                    ).scalar_one_or_none()

                    if brand is None:
                        brand = Brand(
                            name=brand_name
                        )

                        session.add(brand)
                        session.flush()
                )
            ).scalar_one_or_none()

            if brand is None:

                brand = Brand(
                    name=item["brand"]
                )

                session.add(brand)

                session.flush()



            category = session.execute(
                select(Category).where(

                    category_name = item.get("category", "Без категории")

                    category = session.execute(
                        select(Category).where(
                            Category.name == category_name
                        )
                    ).scalar_one_or_none()

                    if category is None:
                        category = Category(
                            name=category_name
                        )

                        session.add(category)
                        session.flush()
                )
            ).scalar_one_or_none()

            if category is None:

                category = Category(
                    name=item["category"]
                )

                session.add(category)

                session.flush()


            existing_product = session.get(
                Product,
                item["id"]
            )

            if existing_product is not None:
                continue



            product = Product(
                id=item["id"],
                title=item["title"],
                description=item["description"],
                price=item["price"],
                brand_id=brand.id,
                category_id=category.id
            )

            session.add(product)

            session.flush()



            for review_data in item.get("reviews", []):

                review = Review(
                    rating=review_data["rating"],
                    comment=review_data["comment"],
                    reviewer_name=review_data["reviewerName"],
                    product_id=product.id
                )

                session.add(review)


        session.commit()

    print("Данные успешно сохранены в базу данных!")



def get_products_from_database():

    with SessionLocal() as session:

        products = session.execute(
            select(Product)
        ).scalars().all()

        print("\n")
        print("=" * 70)
        print("ТОВАРЫ ИЗ БАЗЫ ДАННЫХ")
        print("=" * 70)

        for product in products:

            print(f"ID: {product.id}")
            print(f"Название: {product.title}")
            print(f"Цена: {product.price}")
            print(f"Бренд: {product.brand.name}")
            print(f"Категория: {product.category.name}")

            print(
                f"Количество отзывов: "
                f"{len(product.reviews)}"
            )

            print("-" * 70)




def product_to_dto(product: Product) -> ProductDTO:

    return ProductDTO(
        id=product.id,
        title=product.title,
        description=product.description,
        price=product.price,
        brand=product.brand.name,
        category=product.category.name
    )



def get_products_as_dto():

    with SessionLocal() as session:

        products = session.execute(
            select(Product)
        ).scalars().all()

        dto_list = []

        for product in products:

            dto = product_to_dto(product)

            dto_list.append(dto)

        return dto_list



def print_dto():

    products = get_products_as_dto()

    print("\n")
    print("=" * 70)
    print("PRODUCT DTO")
    print("=" * 70)

    for product in products:

        print(f"ID: {product.id}")
        print(f"Название: {product.title}")
        print(f"Описание: {product.description}")
        print(f"Цена: {product.price}")
        print(f"Бренд: {product.brand}")
        print(f"Категория: {product.category}")

        print("-" * 70)


def create_tables():

    Base.metadata.create_all(engine)

    print("Таблицы базы данных созданы!")



async def main():


    create_tables()

    await save_data_to_database()

    get_products_from_database()

    print_dto()


if __name__ == "__main__":
    asyncio.run(main())