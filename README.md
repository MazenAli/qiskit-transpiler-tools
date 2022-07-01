# Qiskit Transpiler Tools

[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

Qiskit tools to streamline transpilation

## Installation

Package not yet available through PyPI.
Clone the main branch to your local repository.
Then, install with `poetry` in editable mode by running

```bash
$ poetry install
```

in the root directory, for usage and/or development.
Or simply include the root directory in your `python` search path.

## Usage

At the moment, there is only one transpiler class implementing the simple
pipeline: gate translation -> layout optimization -> noise aware mapping
(mapomatic) -> dynamic decoupling.

Import the class:

```python
from qiskit iskit_transpiler_tools.transpiler import TranspilerSabreMapomaticDD
```

Construct a circuit `qc` or a list of circuits `qc_list`, load your `backend`.
Apply different transpiler configurations:

```python
transpiler_default = TranspilerSabreMapomaticDD(backend) # default options
transpiler1        = TranspilerSabreMapomaticDD(backend,
                                                optimization_level=3,
                                                num_transpilations=10) # layout
optimization
transpiler2        = TranspilerSabreMapomaticDD(backend,
                                                optimization_level=3,
                                                num_transpilations=10,
                                                apply_mapomatic=True,
                                                apply_dd=True) # add noise
aware transpilation and dynamic decoupling

qc_trans       = transpiler_default.transpile(qc)
qc_list_trans1 = transpiler1.transpile(qc_list)
qc_list_trans2 = transpiler2.transpile(qc_list + [qc])
```

## Contributing

Fork the repository and use basic `GitFlow`.
Further rules will be specified if the need arises.

## License

`qiskit_transpilation_tools` was created by Mazen Ali.
It is licensed under the terms of the MIT license.
