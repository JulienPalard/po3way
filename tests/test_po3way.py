from po3way import simple_merge, merge_header


def test_merge_header():
    conflict = """
msgid ""
<<<<<<< /tmp/tmp2g34f2cz/local.po
msgstr ""
"Project-Id-Version: Python 3\n"
"POT-Creation-Date: 2022-06-22 23:13+0200\n"
"PO-Revision-Date: 2022-05-23 00:52+0200\n"
"Last-Translator: The old one\n"
||||||| /tmp/tmp2g34f2cz/base.po
msgstr ""
"Project-Id-Version: Python 3\n"
"POT-Creation-Date: 2022-05-22 23:13+0200\n"
"PO-Revision-Date: 2022-05-23 00:52+0200\n"
"Last-Translator: The old one\n"
=======
msgstr ""
"Project-Id-Version: Python 3\n"
"POT-Creation-Date: 2022-05-22 23:13+0200\n"
"PO-Revision-Date: 2022-06-23 00:52+0200\n"
"Last-Translator: The new one\n"
>>>>>>> /tmp/tmp2g34f2cz/remote.po
"""
    has_merged, merged = merge_header(conflict)
    assert (
        merged
        == """
msgid ""
msgstr ""
"Project-Id-Version: Python 3\n"
"POT-Creation-Date: 2022-06-22 23:13+0200\n"
"PO-Revision-Date: 2022-06-23 00:52+0200\n"
"Last-Translator: The new one\n"
"""
    )


def test_simple_merge():
    conflict = """
<<<<<<< /tmp/tmp2g34f2cz/local.po
#: library/exceptions.rst:732
#, fuzzy
||||||| /tmp/tmp2g34f2cz/base.po
#: library/exceptions.rst:724
#, fuzzy
=======
#: library/exceptions.rst:724
>>>>>>> /tmp/tmp2g34f2cz/remote.po
"""

    resolved, qty = simple_merge(conflict, True)
    assert qty == 1
    assert resolved == "\n#: library/exceptions.rst:732\n"


def test_simple_merge2():
    conflict = """
<<<<<<< /tmp/tmp5inugbk_/local.po
#: library/csv.rst:479
#, fuzzy
||||||| /tmp/tmp5inugbk_/base.po
#: library/csv.rst:475
#, fuzzy
=======
#: library/csv.rst:475
>>>>>>> /tmp/tmp5inugbk_/remote.po
"""
    resolved, qty = simple_merge(conflict, True)
    assert qty == 1
    assert resolved == "\n#: library/csv.rst:479\n"
