# Ollama QA Testing GUI

A sophisticated desktop application for testing and validating Large Language Model (LLM) responses using Ollama. This tool provides a comprehensive environment for managing QA testing projects, with support for both manual and automated validation through OpenAI.

The core use-case is for painlessly tuning prompts for small local models to perform simple reasoning. This application enables rapid testing and benchmarking of prompts on a task, with an intuitive GUI.

## Features

### Project Management
- Create and manage multiple QA testing projects
- Organize prompts, test cases, and results by project
- Track project history and test runs
- Intuitive PyQt5-based graphical interface

### Testing Capabilities
- Integration with Ollama for LLM response generation
- Asynchronous batch processing of test cases
- Support for multiple data source formats:
  - JSON files with context arrays
  - Excel files (first column used as context)
- Detailed test run tracking and statistics

### Validation System
- Dual validation approaches:
  - Manual validation with status tracking
  - Automated validation using OpenAI
- Comprehensive validation statistics:
  - Success/failure rates
  - Progress tracking
  - Detailed validation reasons
- Skip functionality for manual validation

### Results Management
- Structured storage of test results
- Detailed statistics for each test run
- Historical test run tracking
- Export capabilities

## Requirements

- Python 3.x
- PyQt5 >= 5.15.0
- requests >= 2.25.0
- pandas >= 1.2.0 (for Excel file support)
- openpyxl >= 3.0.0 (for Excel file support)
- aiohttp >= 3.9.0 (for async HTTP requests)
- openai >= 1.0.0 (for OpenAI validation)
- Running Ollama instance (default: http://localhost:11434)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure OpenAI (optional, for automated validation):
   - Copy `config/openai_config.json` to `config/openai_config.local.json`
   - Add your OpenAI API key to the local config file

## Usage

1. Start the application:
```bash
python src/main.py
```

2. Create a New Project:
   - Click "Create New Project"
   - Enter a unique project name
   - Project will appear in the left panel

3. Add Test Data:
   - Import test data from JSON or Excel files
   - JSON format example:
   ```json
   {
     "contexts": [
       "Context text 1",
       "Context text 2",
       ...
     ]
   }
   ```
   - Excel format: First column contains context texts

4. Create and Run Tests:
   - Add prompts to your project
   - Select data sources
   - Run tests against Ollama
   - View results in real-time

5. Validate Results:
   - Use manual validation for direct assessment
   - Enable OpenAI validation for automated checking
   - Track validation progress and statistics

## Project Structure

```
├── config/
│   ├── openai_config.json         # OpenAI configuration template
│   └── openai_config.local.json   # Local OpenAI configuration
├── data/
│   ├── projects.json             # Project metadata
│   └── results/                  # Test results storage
├── examples/
│   ├── input.json               # Sample input data
│   └── sample_input.json        # Additional examples
└── src/
    ├── main.py                  # Application entry point
    ├── project_manager.py       # Project management
    ├── test_runner.py          # Test execution engine
    ├── openai_validator.py     # OpenAI validation
    ├── dialogs.py             # UI dialogs
    ├── views.py               # UI views
    └── validation_dialog.py   # Validation interface
```

## Key Components

- **TestRunner**: Manages test execution and result storage
- **ProjectManager**: Handles project creation and management
- **OpenAIValidator**: Provides automated validation using OpenAI
- **DataSourceHandler**: Processes input data from various formats
- **MainWindow**: Primary GUI interface

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]