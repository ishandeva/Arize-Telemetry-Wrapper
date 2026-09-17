# Versioning and release process

The package follows Semantic Versioning.

- Patch releases fix defects without changing the public API or required-field
  meaning.
- Minor releases add backward-compatible helpers or optional attributes.
- Major releases remove/rename public APIs or change the semantics of a
  required attribute.

## Release checklist

1. Update `version` in `pyproject.toml` and `arize_wrapper.__version__`.
2. Update the required-attribute table when the organizational standard has
   changed, including a migration note for consumers.
3. Run unit tests and build the distribution:

   ```bash
   python -m pip install -e ".[test,dev]"
   python -m pytest
   python -m build
   ```

4. Inspect `dist/` and run `python -m twine check dist/*`.
5. Publish `dist/*` to the organization's approved repository using its
   approved CI/CD credential mechanism. Do not put repository credentials in
   `pyproject.toml`, source code, examples, or shell history.
6. Verify installation from that repository in a clean environment, run the
   LLM example with a non-production project, and confirm all six LLM fields
   in the Arize trace detail.
7. Tag the source release as `v<version>` and publish release notes covering
   compatibility, dependency changes, and configuration changes.

The approved package index URL and publication identity are intentionally not
guessed by this repository. Add them in protected CI configuration after the
organization confirms the publishing target.
