# Contributing Guidelines

Thank you for your interest in contributing to the **OVRO–LWA SK Pipeline**.

At this stage, the repository is a **personal development space**, but the
following guidelines can help keep contributions focused and manageable.

## How to Propose Changes

1. **Open an Issue (optional but recommended).**  
   Describe the feature, bug, or idea. Include enough context to understand
   how it relates to the OVRO–LWA SK pipeline or `pyGSK` integration.

2. **Create a Branch.**  
   Use descriptive names such as:
   - `dev/ovro-lwa-io-improvements`
   - `dev/notebook-cleanup`
   - `dev/threshold-sweep-examples`

3. **Implement Your Changes.**  
   - Keep commits small and focused.
   - Add or update documentation where appropriate (README, docs/, notebooks).
   - Add tests or simple verification scripts when possible.

4. **Run Checks (if available).**  
   If the project later includes automated tests or linting, run them before
   opening a pull request.

5. **Open a Pull Request.**  
   - Clearly describe what you changed and why.
   - Reference related issues or discussions.
   - Be open to feedback and iterative refinement.

## Code Style

- Prefer clear, readable Python over overly clever constructs.
- Use type hints where they improve clarity.
- Follow PEP8-style conventions unless there is a compelling reason not to.
- Keep dependencies minimal and justified, especially for core functionality.

## Documentation and Notebooks

- Notebooks in `notebooks/` should aim to be **reproducible demonstrations**
  of the pipeline, not just scratchpads.
- Consider adding short markdown cells explaining important steps,
  especially where `pyGSK` APIs are used.
- For more permanent prose, use markdown files in `docs/` rather than
  long text blocks inside notebooks.

## Data

- Do **not** commit large data files or proprietary OVRO–LWA data directly
  to the repository.
- Use `data/README.md` to document expected formats, example file names, and
  how to obtain data (e.g., paths on internal systems or public archives).

## Code of Conduct

By participating in this project, you agree to abide by the
[`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md). Please treat all participants
with respect and professionalism.
