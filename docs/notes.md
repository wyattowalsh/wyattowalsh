# Dev Notes

- Use the [`Makefile`](https://github.com/wyattowalsh/wyattowalsh/tree/main/Makefile) for most project commands.

```zsh
make help
```

---

- Use [`uv`](/stack#uv-python-package-manager) to run [`Python`](/stack#python-programming-language) scripts.

```zsh
uv run python scripts/cli.py
```
or

```zsh
uv run pytest tests/test_banner.py
```

---

- Use the [`CLI`](https://github.com/wyattowalsh/wyattowalsh/tree/main/scripts/cli.py) as the unified interface for the project's [scripts](https://github.com/wyattowalsh/wyattowalsh/tree/main/scripts).

```zsh
uv run readme --help
```