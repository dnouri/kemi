kemi
====

Kemi is an add-on for SQLAlchemy_ that aims to make defining relations
with declarative style classes easier.

Consider this example from the SQLAlchemy docs::

  class Customer(Base):
      __tablename__ = 'customer'
      id = Column(Integer, primary_key=True)
      name = Column(String)

      billing_address_id = Column(Integer, ForeignKey("address.id"))
      shipping_address_id = Column(Integer, ForeignKey("address.id"))

      billing_address = relationship("Address",
                      primaryjoin="Address.id==Customer.billing_address_id")
      shipping_address = relationship("Address",
                      primaryjoin="Address.id==Customer.shipping_address_id")

Using kemi, this can be written as::

  class Customer(Base):
      name = Column(String)
      billing_address = relationship("Address")
      shipping_address = relationship("Address")

Things that kemi currently does:

* adds a ``__tablename__`` if none is explicitely set on the class
* adds an ``id`` column if no primary key column is present
* adds foreign key columns for relationships if no foreign key columns
  are present
* adds ``primaryjoins`` to relationships if they're not set

To use kemi, you need to use its DeclarativeMeta class when you make a
call to ``declarative_base``::

  from sqlalchemy.ext.declarative import declarative_base
  from kemi import DeclarativeMeta

  Base = declarative_base(metaclass=DeclarativeMeta)  

  class Customer(Base):
      name = Column(String)
      billing_address = relationship("Address")
      shipping_address = relationship("Address")


.. _SQLAlchemy: http://www.sqlalchemy.org/
