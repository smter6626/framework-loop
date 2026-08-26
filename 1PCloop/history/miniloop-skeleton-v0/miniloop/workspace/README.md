# Authorized Executor workspace

This directory is the only host path mounted read/write at `/workspace` in the generic Linux Executor sandbox. Governance (`docs/`) and control state (`control/`) are siblings and are not mounted.

Bounded implementation tasks may create source, tests, Git state, and evidence here. The first skeleton deliberately keeps this directory nearly empty until a Reviewer issues such a task.
