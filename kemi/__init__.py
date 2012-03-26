import re

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.ext.declarative import DeclarativeMeta as BaseDeclarativeMeta
from sqlalchemy.orm.properties import RelationshipProperty


def camel_case_to_name(text):
    """
      >>> camel_case_to_name('FooBar')
      'foo_bar'
      >>> camel_case_to_name('TXTFile')
      'txt_file'
      >>> camel_case_to_name ('MyTXTFile')
      'my_txt_file'
      >>> camel_case_to_name('froBOZ')
      'fro_boz'
      >>> camel_case_to_name('f')
      'f'
    """
    return re.sub(
        r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r'_\1', text).lower()


class DeclarativeMeta(BaseDeclarativeMeta):
    features = (
        'id_column',
        'tablename',
        'foreign_key_columns',
        'primaryjoins',
        )

    def __new__(meta, classname, bases, classdict):
        if '_decl_class_registry' not in classdict:  # skip Base itself
            for featurename in meta.features:
                getattr(meta, featurename)(meta, classname, bases, classdict)
        return type.__new__(meta, classname, bases, classdict)

    @staticmethod
    def _get_relationships(classdict):
        return [(name, prop) for (name, prop) in classdict.items()
                if isinstance(prop, RelationshipProperty)]

    @staticmethod
    def _get_names(class_or_string):
        if hasattr(class_or_string, '__name__'):
            return class_or_string.__name__, class_or_string.__tablename__
        else:
            # XXX Here is a very messy assumption; if we only have the
            #     class name and not the class itself, we assume that
            #     the table name uses our own convention.  This will
            #     break when we refer to classes by their 'Name' in
            #     e.g. relationships and then use a custom table name.
            return class_or_string, camel_case_to_name(class_or_string) + 's'

    @staticmethod
    def id_column(meta, classname, bases, classdict):
        for value in classdict.values():
            if isinstance(value, Column) and value.primary_key:
                return
        classdict['id'] = Column(Integer, primary_key=True)

    @staticmethod
    def tablename(meta, classname, bases, classdict):
        if '__tablename__' not in classdict:
            classdict['__tablename__'] = camel_case_to_name(classname) + 's'

    @staticmethod
    def foreign_key_columns(meta, classname, bases, classdict):
        foreign_key_cols = [col for col in classdict.values()
                            if isinstance(col, Column) and col.foreign_keys]
        if foreign_key_cols:
            return  # there's foreign key columns already, do nothing

        relationships = meta._get_relationships(classdict)
        for name, prop in relationships:
            if prop.primaryjoin is not None or prop.secondary is not None:
                continue
            other_classname, other_tablename = meta._get_names(prop.argument)
            fk_colname = '{0}_id'.format(name)
            classdict[fk_colname] = Column(
                fk_colname,
                Integer,
                ForeignKey('{0}.id'.format(other_tablename)),
                )

    @staticmethod
    def primaryjoins(meta, classname, bases, classdict):
        relationships = meta._get_relationships(classdict)
        for name, prop in relationships:
            if prop.primaryjoin is not None or prop.secondary is not None:
                continue
            other_classname, other_tablename = meta._get_names(prop.argument)
            fk_colname = '{0}_id'.format(name)
            column = classdict.get(fk_colname)
            if column is not None:
                prop.primaryjoin = '{0}.id == {1}.{2}'.format(
                    other_classname, classname, fk_colname)
