# Contributing to DEBUSSY

Thank you for considering contributing to DEBUSSY. We welcome bug reports,
feature requests, documentation improvements, and code contributions.

## Getting help

If you have a usage question rather than a bug — which parameter answers your
design question, why a value came back `None`, how to report a result in a
manuscript — start with the
[documentation site](https://hyeonjoong.github.io/debussy/), then ask on the
issue tracker.

GitHub Discussions is not enabled on this repository, so questions and bug
reports share one tracker and are told apart by label. Open an
[issue](https://github.com/hyeonjoong/debussy/issues/new) and say in the first
line that it is a usage question; a maintainer will apply the `question` label.
You will not be able to set that label yourself unless you have triage rights,
so please do not let a missing label stop you from asking.

Questions are welcome. If the answer turns out to be "the documentation should
have told you that", we treat it as a documentation bug and fix it.

## Reporting issues

Use this route when something is wrong or missing — not for usage questions,
which are covered above.

- Search [existing issues](https://github.com/hyeonjoong/debussy/issues) before
  filing a new one.
- For bugs, include: Python version, OS, DEBUSSY version (`debussy.__version__`),
  a minimal reproducer (audio snippet if relevant), expected vs actual output.
- For feature requests, describe the autonomic-arousal use case so we can keep
  the package focused on its scope.

## Development setup

```bash
git clone https://github.com/hyeonjoong/debussy.git
cd debussy
pip install -e ".[dev]"
pytest
```

We use `ruff` for linting:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Submitting a pull request

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/<short-name>`).
3. Make your changes, add or update tests, and run `pytest` locally.
4. Update `CHANGELOG.md` under `[Unreleased]`.
5. Open a PR against `main`. Describe what the change does and why.

## Code style

- Type hints on all public functions.
- Numpy-style docstrings.
- Keep functions in the appropriate family module (`level`, `envelope`,
  `spectral`, `tonal`, `psychoacoustic`).
- The `analyze_audio()` orchestration entry point should remain stable; if a
  parameter must be added, version-bump the schema and add it as optional.

## What we will and will not accept

**Yes:**
- Bug fixes
- New parameters that are directly relevant to autonomic-arousal stimulus
  characterisation, with literature citation in the docstring
- Performance improvements (with a benchmark)
- Documentation improvements
- Validation runs on additional public datasets

**Generally not:**
- ML-only features (DEBUSSY is a reporting toolbox; ML feature-extraction is
  better served by `essentia` or `librosa` directly)
- Breaking changes to the `Result` schema without a deprecation cycle
- Adding heavy native dependencies

## Code of conduct

Be respectful. Disagreements about science are welcome; personal attacks are
not. We follow the [Contributor Covenant](https://www.contributor-covenant.org/).
