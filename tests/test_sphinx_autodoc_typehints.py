import pathlib
import pytest
import re
import sys
import textwrap
from typing import (
    Any, AnyStr, Callable, Dict, Generic, Mapping, NewType, Optional, Pattern,
    Tuple, TypeVar, Union, Type)

from typing_extensions import Protocol

from sphinx_autodoc_typehints import format_annotation, process_docstring

try:
    from typing import ClassVar  # not available prior to Python 3.5.3
except ImportError:
    ClassVar = None

try:
    from typing import NoReturn  # not available prior to Python 3.6.5
except ImportError:
    NoReturn = None

T = TypeVar('T')
U = TypeVar('U', covariant=True)
V = TypeVar('V', contravariant=True)
W = NewType('W', str)


class A:
    def get_type(self):
        return type(self)


class B(Generic[T]):
    pass


class C(B[str]):
    pass


class D(Protocol):
    pass


class E(Protocol[T]):
    pass


class Slotted:
    __slots__ = ()


class Metaclass(type):
    pass


@pytest.mark.parametrize('annotation, expected_result', [
    (str,                           ':py:class:`str`'),
    (int,                           ':py:class:`int`'),
    (type(None),                    '``None``'),
    (type,                          ':py:class:`type`'),
    pytest.param(NoReturn,          ':py:data:`~typing.NoReturn`',
                 marks=[pytest.mark.skipif(NoReturn is None,
                                           reason='typing.NoReturn is not available')]),
    pytest.param(ClassVar[str],      ':py:data:`~typing.ClassVar`\\[:py:class:`str`]',
                 marks=[pytest.mark.skipif(ClassVar is None,
                                           reason='typing.ClassVar is not available')]),
    (Any,                           ':py:data:`~typing.Any`'),
    (AnyStr,                        ':py:data:`~typing.AnyStr`'),
    (Generic[T],                    ':py:class:`~typing.Generic`\\[\\~T]'),
    (Mapping,                       ':py:class:`~typing.Mapping`\\[\\~KT, \\+VT_co]'),
    (Mapping[T, int],               ':py:class:`~typing.Mapping`\\[\\~T, :py:class:`int`]'),
    (Mapping[str, V],               ':py:class:`~typing.Mapping`\\[:py:class:`str`, \\-V]'),
    (Mapping[T, U],                 ':py:class:`~typing.Mapping`\\[\\~T, \\+U]'),
    (Mapping[str, bool],            ':py:class:`~typing.Mapping`\\[:py:class:`str`, '
                                    ':py:class:`bool`]'),
    (Dict,                          ':py:class:`~typing.Dict`\\[\\~KT, \\~VT]'),
    (Dict[T, int],                  ':py:class:`~typing.Dict`\\[\\~T, :py:class:`int`]'),
    (Dict[str, V],                  ':py:class:`~typing.Dict`\\[:py:class:`str`, \\-V]'),
    (Dict[T, U],                    ':py:class:`~typing.Dict`\\[\\~T, \\+U]'),
    (Dict[str, bool],               ':py:class:`~typing.Dict`\\[:py:class:`str`, '
                                    ':py:class:`bool`]'),
    (Tuple,                         ':py:data:`~typing.Tuple`'),
    (Tuple[str, bool],              ':py:data:`~typing.Tuple`\\[:py:class:`str`, '
                                    ':py:class:`bool`]'),
    (Tuple[int, int, int],          ':py:data:`~typing.Tuple`\\[:py:class:`int`, '
                                    ':py:class:`int`, :py:class:`int`]'),
    (Tuple[str, ...],               ':py:data:`~typing.Tuple`\\[:py:class:`str`, ...]'),
    (Union,                         ':py:data:`~typing.Union`'),
    (Union[str, bool],              ':py:data:`~typing.Union`\\[:py:class:`str`, '
                                    ':py:class:`bool`]'),
    pytest.param(Union[str, Any],   ':py:data:`~typing.Union`\\[:py:class:`str`, '
                                    ':py:data:`~typing.Any`]',
                 marks=pytest.mark.skipif((3, 5, 0) <= sys.version_info[:3] <= (3, 5, 2),
                                          reason='Union erases the str on 3.5.0 -> 3.5.2')),
    (Optional[str],                 ':py:data:`~typing.Optional`\\[:py:class:`str`]'),
    (Callable,                      ':py:data:`~typing.Callable`'),
    (Callable[..., int],            ':py:data:`~typing.Callable`\\[..., :py:class:`int`]'),
    (Callable[[int], int],          ':py:data:`~typing.Callable`\\[\\[:py:class:`int`], '
                                    ':py:class:`int`]'),
    (Callable[[int, str], bool],    ':py:data:`~typing.Callable`\\[\\[:py:class:`int`, '
                                    ':py:class:`str`], :py:class:`bool`]'),
    (Callable[[int, str], None],    ':py:data:`~typing.Callable`\\[\\[:py:class:`int`, '
                                    ':py:class:`str`], ``None``]'),
    (Callable[[T], T],              ':py:data:`~typing.Callable`\\[\\[\\~T], \\~T]'),
    (Pattern,                       ':py:class:`~typing.Pattern`\\[:py:data:`~typing.AnyStr`]'),
    (Pattern[str],                  ':py:class:`~typing.Pattern`\\[:py:class:`str`]'),
    (Metaclass,                     ':py:class:`~%s.Metaclass`' % __name__),
    (A,                             ':py:class:`~%s.A`' % __name__),
    (B,                             ':py:class:`~%s.B`\\[\\~T]' % __name__),
    (B[int],                        ':py:class:`~%s.B`\\[:py:class:`int`]' % __name__),
    (C,                             ':py:class:`~%s.C`' % __name__),
    (D,                             ':py:class:`~%s.D`' % __name__),
    (E,                             ':py:class:`~%s.E`\\[\\~T]' % __name__),
    (E[int],                        ':py:class:`~%s.E`\\[:py:class:`int`]' % __name__),
    (W,                             ':py:func:`~typing.NewType`\\(:py:data:`~W`, :py:class:`str`)')
])
def test_format_annotation(inv, annotation, expected_result):
    result = format_annotation(annotation)
    assert result == expected_result

    # Test with the "fully_qualified" flag turned on
    if 'typing' in expected_result or __name__ in expected_result:
        expected_result = expected_result.replace('~typing', 'typing')
        expected_result = expected_result.replace('~' + __name__, __name__)
        assert format_annotation(annotation, fully_qualified=True) == expected_result

    # Test for the correct role (class vs data) using the official Sphinx inventory
    if 'typing' in expected_result:
        m = re.match('^:py:(?P<role>class|data|func):`~(?P<name>[^`]+)`', result)
        assert m, 'No match'
        name = m.group('name')
        role = next((o.role for o in inv.objects if o.name == name), None)
        if name in {'typing.Pattern', 'typing.Match', 'typing.NoReturn'}:
            if sys.version_info < (3, 6):
                assert role is None, 'No entry in Python 3.5’s objects.inv'
                return

        assert role is not None, 'Name {} not found'.format(name)
        assert m.group('role') == 'func' if role == 'function' else role


@pytest.mark.parametrize('type_param, expected_result', [
    (None, ':py:class:`~typing.Type`\\[\\+CT'),
    (A, ':py:class:`~typing.Type`\\[:py:class:`~%s.A`]' % __name__)
])
def test_format_annotation_type(type_param, expected_result):
    annotation = Type[type_param] if type_param else Type
    result = format_annotation(annotation)
    assert result.startswith(expected_result)


def test_process_docstring_slot_wrapper():
    lines = []
    process_docstring(None, 'class', 'SlotWrapper', Slotted, None, lines)
    assert not lines


@pytest.mark.parametrize('always_document_param_types', [True, False])
@pytest.mark.sphinx('text', testroot='dummy')
def test_sphinx_output(app, status, warning, always_document_param_types):
    test_path = pathlib.Path(__file__).parent

    # Add test directory to sys.path to allow imports of dummy module.
    if str(test_path) not in sys.path:
        sys.path.insert(0, str(test_path))

    app.config.always_document_param_types = always_document_param_types
    app.build()

    assert 'build succeeded' in status.getvalue()  # Build succeeded

    # There should be a warning about an unresolved forward reference
    warnings = warning.getvalue().strip()
    assert 'Cannot resolve forward reference in type annotations of ' in warnings, warnings

    if always_document_param_types:
        undoc_params = '''

           Parameters:
              **x** ("int") --'''

    else:
        undoc_params = ""

    text_path = pathlib.Path(app.srcdir) / '_build' / 'text' / 'index.txt'
    with text_path.open('r') as f:
        text_contents = f.read().replace('–', '--')
        expected_contents = textwrap.dedent('''\
        Dummy Module
        ************

        class dummy_module.Class(x, y, z=None)

           Initializer docstring.

           Parameters:
              * **x** ("bool") – foo

              * **y** ("int") – bar

              * **z** ("Optional"["str"]) – baz

           class InnerClass

              Inner class.

              _InnerClass__dunder_inner_method(x)

                 Dunder inner method.

                 Parameters:
                    **x** ("bool") -- foo

                 Return type:
                    "str"

              inner_method(x)

                 Inner method.

                 Parameters:
                    **x** ("bool") -- foo

                 Return type:
                    "str"

           _Class__dunder_method(x)

              Dunder method docstring.

              Parameters:
                 **x** ("str") -- foo

              Return type:
                 "str"

           __magic_custom_method__(x)

              Magic dunder method docstring.

              Parameters:
                 **x** ("str") -- foo

              Return type:
                 "str"

           _private_method(x)

              Private method docstring.

              Parameters:
                 **x** ("str") -- foo

              Return type:
                 "str"

           classmethod a_classmethod(x, y, z=None)

              Classmethod docstring.

              Parameters:
                 * **x** ("bool") – foo

                 * **y** ("int") – bar

                 * **z** ("Optional"["str"]) – baz

              Return type:
                 "str"

           a_method(x, y, z=None)

              Method docstring.

              Parameters:
                 * **x** ("bool") – foo

                 * **y** ("int") – bar

                 * **z** ("Optional"["str"]) – baz

              Return type:
                 "str"

           property a_property

              Property docstring

              Return type:
                 "str"

           static a_staticmethod(x, y, z=None)

              Staticmethod docstring.

              Parameters:
                 * **x** ("bool") – foo

                 * **y** ("int") – bar

                 * **z** ("Optional"["str"]) – baz

              Return type:
                 "str"

           locally_defined_callable_field() -> str

              Wrapper

              Return type:
                 "str"

        exception dummy_module.DummyException(message)

           Exception docstring

           Parameters:
              **message** ("str") – blah

        dummy_module.function(x, y, z_=None)

           Function docstring.

           Parameters:
              * **x** ("bool") – foo

              * **y** ("int") – bar

              * **z_** ("Optional"["str"]) – baz

           Returns:
              something

           Return type:
              bytes

        dummy_module.function_with_escaped_default(x='\\x08')

           Function docstring.

           Parameters:
              **x** ("str") – foo

        dummy_module.function_with_unresolvable_annotation(x)

           Function docstring.

           Parameters:
              **x** (*a.b.c*) – foo

        dummy_module.function_with_typehint_comment(x, y)

           Function docstring.

           Parameters:
              * **x** ("int") – foo

              * **y** ("str") – bar

           Return type:
              "None"

        class dummy_module.ClassWithTypehints(x)

           Class docstring.

           Parameters:
              **x** ("int") -- foo

           foo(x)

              Method docstring.

              Parameters:
                 **x** ("str") -- foo

              Return type:
                 "int"

        dummy_module.function_with_typehint_comment_not_inline(x=None, *y, z, **kwargs)

           Function docstring.

           Parameters:
              * **x** ("Union"["str", "bytes", "None"]) -- foo

              * **y** ("str") -- bar

              * **z** ("bytes") -- baz

              * **kwargs** ("int") -- some kwargs

           Return type:
              "None"

        class dummy_module.ClassWithTypehintsNotInline(x=None)

           Class docstring.

           Parameters:
              **x** ("Optional"["Callable"[["int", "bytes"], "int"]]) -- foo

           foo(x=1)

              Method docstring.

              Parameters:
                 **x** ("Callable"[["int", "bytes"], "int"]) -- foo

              Return type:
                 "int"

           classmethod mk(x=None)

              Method docstring.

              Parameters:
                 **x** (*Callable**[**[**int**, **bytes**]**, **int**]*) --
                 foo

              Return type:
                 ClassWithTypehintsNotInline

        dummy_module.undocumented_function(x)

           Hi{undoc_params}

           Return type:
              "str"

        class dummy_module.DataClass

           Class docstring.

           __init__()
        '''.format(undoc_params=undoc_params)).replace('–', '--')

        if sys.version_info < (3, 6):
            expected_contents += '''
      Initialize self.  See help(type(self)) for accurate signature.
'''
        else:
            expected_contents += '''
      Return type:
         "None"
'''

        assert text_contents == expected_contents
