# Excel MCP Server & Employee Classification Agent

An MCP (Model Context Protocol) server with an AI agent that automatically classifies employees in Excel files based on their experience, role, and other attributes.

## 🏗️ Architecture

This project consists of two main components:

1. **MCP Server** (`mcp_server/`): Exposes Excel operations as MCP tools
2. **AI Agent** (`agent/`): Uses OpenAI to make intelligent decisions about employee classifications

### How It Works

1. The agent connects to the MCP server via stdio
2. Scans ALL employee rows from Excel (comprehensive scanning)
3. Calculates/updates Experience_Years from DOJ automatically
4. Uses GPT-4o-mini to analyze each employee and decide:
   - **Department**: Web, AI, HR, Finance, or Operations
   - **Designation**: Intern, Junior, Senior, or Lead (auto-updates as experience grows)
   - **Salary_Band**: L1, L2, or L3
5. Fills empty cells and updates outdated values automatically
6. Applies decisions back to Excel with confidence scores and reasoning

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- Excel file with employee data

## 🚀 Setup

1. **Clone the repository**
   ```bash
   cd excel_mcp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Create .env file (if it doesn't exist)
   # Add your OPENAI_API_KEY:
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Configure settings (optional)**
   - Edit `config/config.yaml` to customize:
     - Excel file path
     - OpenAI model settings
     - Processing batch size
     - Logging level
     - Decision rules

5. **Prepare Excel file**
   - Place your Excel file at `data/employees_mcp.xlsx` (or path in config)
   - Ensure it has required columns (see `mcp_server/schema.py`)
   - The system will create backups automatically before updates

## 💻 Usage

### Run the Agent

Scan and process all employees (fills empty cells, updates outdated values):

```bash
python main.py
```

The agent will:
- Scan ALL employees (not just unprocessed)
- Calculate/update Experience_Years from DOJ
- Fill empty cells in any column
- Auto-update designations when experience changes (e.g., Junior → Senior)
- Update any outdated values

### Run MCP Server Standalone

For testing or integration with other MCP clients:

```bash
python -m mcp_server.server
```

## 📊 Decision Rules

The agent follows these rules:

### Designation (based on Experience_Years)
- **Intern**: < 2 years
- **Junior**: 2-4 years
- **Senior**: 5-7 years
- **Lead**: 8+ years

### Salary Band
- **L1**: Entry level (Intern, Junior with <3 years)
- **L2**: Mid level (Junior with 3-4 years, Senior)
- **L3**: Senior level (Lead, Senior with 7+ years)

### Department
- Inferred from employee's Role or existing Department
- Options: Web, AI, HR, Finance, Operations

## 🛠️ MCP Tools

The server exposes these tools:

1. **`fetch_unprocessed`**: Get all unprocessed employee rows
2. **`fetch_all_employees`**: Get ALL employee rows for comprehensive scanning
3. **`apply_employee_update`**: Update employee data with AI decisions
4. **`update_experience`**: Recalculate experience from DOJ (MCP tool, not a script)
5. **`reset_processed_flag`**: Reset processing flags for reprocessing

## 📁 Project Structure

```
excel_mcp/
├── mcp_server/          # MCP server implementation
│   ├── server.py       # MCP server with tool definitions
│   ├── tools.py        # Excel operations (read/write)
│   └── schema.py       # Data validation schemas
├── agent/              # AI agent (MCP client)
│   └── employee_agent.py  # Decision-making logic
├── utils/              # Utility modules
│   ├── logger.py       # Logging configuration
│   ├── config_loader.py # Configuration management
│   └── backup.py       # Backup functionality
├── config/             # Configuration files
│   └── config.yaml     # Main configuration
├── data/               # Excel data files
│   └── employees_mcp.xlsx
├── backups/            # Automatic backups (created automatically)
├── logs/               # Log files (created automatically)
├── main.py             # Entry point (runs agent)
└── requirements.txt    # Python dependencies
```

## 🔧 Configuration

### Configuration File
Edit `config/config.yaml` to customize:

- **Excel file path**: `excel_path`
- **OpenAI settings**: Model, temperature, retry settings
- **Processing settings**: Batch size, backup options
- **Logging**: Log level, file path
- **Decision rules**: Experience thresholds, salary band rules

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `EXCEL_PATH`: Override Excel file path (optional)
- `OPENAI_MODEL`: Override OpenAI model (optional)

### Example Configuration
```yaml
excel_path: "data/employees_mcp.xlsx"
openai:
  model: "gpt-4o-mini"
  temperature: 0
  max_retries: 3
processing:
  backup_before_update: true
  backup_directory: "backups"
logging:
  level: "INFO"
  file: "logs/mcp_server.log"
```

## 📝 Excel File Format

Required columns:
- `Emp_ID`: Employee ID
- `Name`: Employee name
- `DOJ`: Date of Joining
- `Experience_Years`: Years of experience (auto-calculated)
- `Role`: Employee role
- `Status`: Active/Inactive
- `Department`: Department (filled by agent)
- `Designation`: Designation (filled by agent)
- `Salary_Band`: Salary band (filled by agent)
- `Is_Processed`: Yes/No flag
- `AI_Decision_Reason`: Reasoning for decisions
- `Confidence_Score`: Confidence (0.0-1.0)
- `Last_Processed_On`: Timestamp

## ✨ Features

- ✅ **Automatic Backups**: Creates timestamped backups before updates
- ✅ **Comprehensive Logging**: File and console logging with rotation
- ✅ **Error Handling**: Retry logic for API calls, graceful error recovery
- ✅ **Progress Reporting**: Real-time progress and summary statistics
- ✅ **Configuration Management**: YAML-based configuration
- ✅ **Data Validation**: Enforces dropdown constraints
- ✅ **Unit Tests**: Test suite for core functionality

## ⚠️ Notes

- The agent scans ALL employees and updates any empty or outdated fields
- Automatically updates Experience_Years from DOJ on every run
- Auto-updates designations when experience changes (e.g., Junior → Senior)
- Automatic backups are created before updates (configurable)
- Data validation (dropdowns) is preserved after updates
- Experience is calculated as: `(Today - DOJ) / 365.25`
- Logs are written to `logs/` directory
- Backups are stored in `backups/` directory

## 🐛 Troubleshooting

### "Invalid row_id" error
- Ensure Excel file hasn't been manually edited
- Row IDs are positional (0-indexed)

### "Invalid value" error
- Check that values match allowed dropdown values in `schema.py`
- Agent should only use allowed values, but manual edits might cause issues

### API Key errors
- Ensure `.env` file exists with `OPENAI_API_KEY`
- Check API key is valid and has credits

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

