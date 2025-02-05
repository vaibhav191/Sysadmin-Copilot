# SysAdmin Copilot

A safety-first sysadmin assistant with Gmail integration, powered by Claude 3.5 Sonnet.

## Features

- Safe command execution on AWS EC2 instances via SSM
- Gmail integration for email management
- Modern dark-themed UI with rounded corners
- Command safety evaluation
- Threaded message handling

## Prerequisites

- Python 3.8+
- AWS account with SSM access
- Gmail API credentials
- Anthropic API key

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/syspilot.git
cd syspilot
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```
ANTHROPIC_API_KEY=your_api_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
REGION_NAME=your_aws_region
INSTANCE_ID=your_instance_id
```

5. Set up Gmail API:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials and save as `credentials.json` in project root

## Usage

Run the application:
```bash
python main.py
```

The chat interface will appear. You can:
- Send system commands that will be executed on your EC2 instance
- Perform Gmail operations
- Interact with the AI assistant for help

## Safety Features

- Command evaluation before execution
- Blocked unsafe patterns (wget, curl, unset)
- SSM-based command execution
- Thread isolation

## Project Structure

```
syspilot/
├── main.py              # Entry point
├── requirements.txt     # Dependencies
├── credentials.json     # Gmail API credentials
├── token.json          # Gmail API token
├── .env                # Environment variables
└── src/
    ├── agent/          # LLM and tools setup
    ├── tools/          # AWS and Gmail tools
    └── ui/             # Chat interface
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License 
