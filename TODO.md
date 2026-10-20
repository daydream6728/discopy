# TODO

> *"i mean discopy/discopy-next issues should get fixed in discopy-next without asking me"*
> (toumix, 2026-10-19, toumix/desire#167)

Fix #21, the oldest open bug that needs no decision: the stale-payload half was fixed by
discopy/discopy#641, the guard still fails without saying which call failed or why.

- [ ] every failing call of the guard names itself in an `::error::` annotation
- [ ] a mutation that leaves `isDraft` in the wrong state says what it found
- [ ] `CHANGELOG.md`
