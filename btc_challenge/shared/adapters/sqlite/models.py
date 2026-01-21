from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass


class BaseORM(MappedAsDataclass, DeclarativeBase):
    pass
