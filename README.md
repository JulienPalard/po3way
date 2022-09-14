# po3way

Three way merger for gettext po file that can act as a git merge driver.

## Why a specific git merge driver for po files?

I give you an example:

```po
msgid ""
"This is an example "
"which span on multiple lines."
msgstr ""
```

In one branch, someone translate it, so it become:

```po
msgid ""
"This is an example "
"which span on multiple lines."
msgstr ""
"C'est un exemple "
"qui s'étend sur plusieurs lignes."
```

In another branch it gets updated, so it become:

```po
msgid ""
"This is an updated example "
"which span on multiple lines."
msgstr ""
```

If we run a 3-way merge on this, we'll get no conflict because those
are two distinct modifications ("shielded" by the `msgstr ""` line),
so it become:

```po
msgid ""
"This is an update example "
"which span on multiple lines."
msgstr ""
"C'est un exemple "
"qui s'étend sur plusieurs lignes."
```

Which is particularily bad for a `po` file, it would clearly need a
`fuzzy` flag and some human intervention, but no, it gets merged
silently.

Let alone this very specific case, `po3way` often provide very clean
and understandable conflicts which are easier to merge than "normal"
conflicts, like:

![](https://user-images.githubusercontent.com/239510/190021277-2660f7e5-e642-4287-90f8-d68664512a31.png)

where the base was fuzzy, remote fixed it, but local updated again!


## How it works

There's no magic, `po3way` works using the following steps:

- Rewrite the `.po` file such that it's easier and safer to diff. This
  step is a bit like using `msgcat --no-wrap` but in a way we can undo
  deterministically.
- Use `git merge-file` to actually do the 3-way merge, I don't want to
  rewrite it from scratch.
- Undo the first step to get your original wrapping back.
- Automatically solve easy conflicts like updated `POT-Creation-Date`
  / `PO-Revision-Date` while we're here.


## How to install

From pypi:

`python -m pip install po3way`

From sources:

`python -m pip install .`


## How to use

The arguments are the same than `diff3`, so:

`po3way local.po base.po remote.po`


## How to use as a git merge driver

There's two things to do, first configure git to learn about the
`po3way` tool, either in your `~/.gitconfig` or in your `.git/config`:

```ini
[merge "po3way"]
    name = po file merge driver
    driver = po3way --git-merge-driver -- %A %O %B
```

Then in your project add a `.gitattributes` file telling that `po`
files should be merged using `po3way`:

    *.po merge=po3way


## Contributing

There's a `--debug` argument to make po3way keep its intermediate
files so you can take a look at them. Just `ls -lahtr /tmp` to find
them, they should be hanging around in a directory prefixed by `tmp`.
