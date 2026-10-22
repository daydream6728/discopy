# TODO

Prompt (toumix, 🌤️ Daylight 2026-10-22, verbatim), during which the bug was found:

> You have a $200 modal budget to make some improvement to our parser (English/Dutch/French/trilingual) you're free to try any techniques you can think of, the more abstract the better. First merge all of the generic parser code from lambek to discopy-next.

Fixes #278: `normal_form` raises on a term whose head is a constant.

- [WIP] @session_01KbBG77r4dz5RennpDkce2y-2026-10-22 19:40 The constants of a term are free variables of its Böhm tree, in scope before its
  free variables, so that a constant can be the head of a spine
