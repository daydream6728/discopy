> cubic on #436: "P2: The eager import only catches `ImportError`. A module that fails with any other exception now aborts collection of its whole directory, not just that file." "P3: `ROOT` is not resolved, but `module_name` resolves the collected path. If the checkout sits behind a symlink, `is_relative_to` is false and the import is silently skipped. Resolve `ROOT` as well."

- [x] catch any `Exception` in the eager import: pytest's own import of the file then reports it, for that file alone
- [x] resolve `ROOT`
