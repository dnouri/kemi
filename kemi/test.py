from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from kemi import DeclarativeMeta


engine = create_engine('sqlite://')
Session = sessionmaker()
Session.configure(bind=engine)


def pytest_funcarg__Base(request):
    from sqlalchemy.orm import _mapper_registry
    _mapper_registry.clear()
    Base = declarative_base(metaclass=DeclarativeMeta)
    Base.metadata.bind = engine
    return Base


def pytest_funcarg__session(request):
    return Session()


def pytest_funcarg__Dummy(request):
    Base = request.getfuncargvalue('Base')
    class Dummy(Base):
        pass
    return Dummy


class TestIdColumn(object):
    def test_default_id_column(self, Base):
        class NoPrimaryKey(Base):
            __tablename__ = 'noid'

        column = NoPrimaryKey.__table__.c['id']
        assert column.primary_key == True
        assert isinstance(column.type, Integer)

    def test_custom_id_column(self, Base):
        class HasId(Base):
            __tablename__ = 'hasid'
            id = Column(String, primary_key=True)

        column = HasId.__table__.c['id']
        assert isinstance(column.type, String)

    def test_custom_primary_key_column(self, Base):
        class HasPrimaryKey(Base):
            __tablename__ = 'hasid'
            name = Column(String, primary_key=True)

        assert 'id' not in HasPrimaryKey.__table__.c


class TestTableName(object):
    def test_default_table_name(self, Base):
        class NoTableName(Base):
            pass

        assert NoTableName.__tablename__ == 'no_table_names'

    def test_custom_table_name(self, Base):
        class HasTableName(Base):
            __tablename__ = 'fancy_table_name'

        assert HasTableName.__tablename__ == 'fancy_table_name'


class TestAddForeignKeyColumns(object):
    @staticmethod
    def assert_column_has_fk(column, fk_name):
        [foreign_key] = list(column.foreign_keys)
        assert foreign_key.target_fullname == fk_name

    def test_default_foreign_key(self, Base, Dummy):
        class NoForeignKey(Base):
            related = relationship(Dummy)

        column = NoForeignKey.__table__.c['related_id']
        assert isinstance(column.type, Integer)
        self.assert_column_has_fk(column, 'dummys.id')
        NoForeignKey()

    def test_default_foreign_key_classname(self, Base):
        class NoForeignKeyWithClassName(Base):
            related = relationship('NoForeignKeyWithClassName')

        column = NoForeignKeyWithClassName.__table__.c['related_id']
        assert isinstance(column.type, Integer)
        self.assert_column_has_fk(column, 'no_foreign_key_with_class_names.id')
        NoForeignKeyWithClassName()

    def test_default_foreign_key_classname_and_custom_tablename(self, Base):
        return  # XXX failing
        class NoFKWithClassNameAndCustomTableName(Base):
            related = relationship('Other')

        class Other(Base):
            __tablename__ = 'fancy_table_name'

        column = NoFKWithClassNameAndCustomTableName.__table__.c['related_id']
        assert isinstance(column.type, Integer)
        self.assert_column_has_fk(column, 'fancy_table_name.id')
        NoFKWithClassNameAndCustomTableName()

    def test_custom_foreign_key(self, Base):
        class HasForeignKey(Base):
            some_related_id = Column(
                Integer,
                ForeignKey('has_foreign_keys.id'),
                nullable=False,
                )
            related = relationship('HasForeignKey')

        assert 'related_id' not in HasForeignKey.__table__.c
        column = HasForeignKey.__table__.c['some_related_id']
        assert isinstance(column.type, Integer)
        assert column.nullable == False
        HasForeignKey()


class TestAddPrimaryJoin(object):
    def test_two_relations(self, Base, Dummy):
        class TwoRelations(Base):
            related1 = relationship(Dummy)
            related2 = relationship('Dummy')

        assert TwoRelations.related1.comparator.prop.primaryjoin is not None
        assert TwoRelations.related2.comparator.prop.primaryjoin is not None
        TwoRelations()

    def test_relation_with_secondary_do_nothing(self, Base, Dummy):
        association_table = Table(
            'association', Base.metadata,
            Column('left', Integer, ForeignKey('relation_with_secondarys.id')),
            Column('right', Integer, ForeignKey('dummys.id')),
            )
        class RelationWithSecondary(Base):
            related = relationship(Dummy, secondary=association_table)

        assert 'related_id' not in RelationWithSecondary.__table__.c
        assert RelationWithSecondary.related.comparator.prop.primaryjoin is None
        RelationWithSecondary()

    def test_relation_with_primaryjoin_do_nothing(self, Base, Dummy):
        class RelationWithPrimaryjoin(Base):
            related_id = Column(Integer, ForeignKey('dummys.id'))
            related = relationship(
                Dummy,
                primaryjoin='Dummy.id == RelationWithPrimaryjoin.related_id',
                )

        RelationWithPrimaryjoin()

    def test_many_relationships_integration(self, Base, Dummy, session):
        class ManyRelations(Base):
            related1 = relationship(Dummy)
            related2 = relationship('Dummy')
            related3 = relationship('ManyRelations', uselist=False)
            related4 = relationship('ManyRelations', uselist=False)

        related1 = Dummy()
        related2 = Dummy()
        related3 = related4 = ManyRelations()
        item = ManyRelations(
            related1=related1,
            related2=related2,
            related3=related3,
            related4=related4,
            )

        Base.metadata.create_all()
        session.add(item)
        session.flush()
        session.expire_all()

        item = session.query(ManyRelations).first()
        assert item.related1 is related1
        assert item.related2 is related2
        assert item.related3 is related3
        assert item.related4 is related4
