# next#250 — `docs/notebooks/optyx/channel_error.ipynb` is a 0-byte notebook

Prompt (daydream6728, scheduled, 2026-10-27):

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

[#250](https://github.com/rel-int/discopy-next/issues/250) leaves two ways out
— restore the notebook's content from history, or delete it — and the history
settles it rather than a taste: the file was **added empty** by `0e6c24bd`
(2025-10-07, optyx#136), does not exist in that commit's parent `faf053c9`,
and no commit has touched it since. There is nothing to restore.

- [ ] measure: the file's whole history, and every reference to it in the repo
- [ ] delete the file
- [ ] `CHANGELOG.md`
