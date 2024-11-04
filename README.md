# Elastos Supernode Monitor Bot

A Telegram bot that monitors the Elastos DPoS Supernode network and reports changes in real-time. The bot tracks voting changes, position changes, state changes, and blockchain status.

## Features

- 🔍 Monitors voting changes with configurable thresholds
- 📊 Tracks and reports position changes in supernode rankings
- 🔄 Detects state changes of existing supernodes
- 🆕 Identifies and announces new supernodes
- ⛓️ Monitors blockchain health and reports if chain gets stuck
- 📱 Delivers all notifications through Telegram

## Project Structure

- `elaBotMain.py` - Main bot logic and monitoring functions
- `posting2.py` - Telegram messaging functionality
- `config.py` - Configuration settings
- `telegram.ini` - Telegram bot credentials
- `requirements.txt` - Project dependencies

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/elastos-supernode-monitor-bot.git
cd elastos-supernode-monitor-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
   - Copy `telegram.ini.example` to `telegram.ini`
   - Add your Telegram bot token
   - Copy `config.py.example` to `config.py`
   - Update configuration values in `config.py`

## Configuration Files

### telegram.ini
```ini
[Telegram]
token = YOUR_BOT_TOKEN_HERE
channel_dpos = YOUR_CHANNEL_ID_HERE
```

### config.py
```python
TELEGRAM_BOT_TOKEN = 'your_bot_token'
ELASTOS_ELA_USER = "your_ela_user"
ELASTOS_ELA_PASS = "your_ela_password"
ELASTOS_ELA_URL = 'http://localhost:20336/'

# Telegram channels
ELASTOS_SCANDINAVIA = your_channel_id
ELASTOS_SN_NOTIFYER = your_channel_id
ELASTOS_TESTCHANNEL = 'your_test_channel_id'
```

## Usage

Run the bot:
```bash
python elaBotMain.py
```

## Monitoring Features

- **Voting Changes**: Monitors significant voting changes above configurable threshold
- **Position Changes**: Tracks when supernodes change positions in rankings
- **State Changes**: Reports when supernodes change their operational state
- **New Supernodes**: Detects and announces new supernode entries
- **Blockchain Status**: Monitors for chain stalls and reports recovery

## Requirements

- Python 3.8+
- python-telegram-bot
- pandas
- requests
- Other dependencies listed in requirements.txt

## Security Notes

- Never commit `telegram.ini` or `config.py` with real credentials
- Use `.gitignore` to exclude sensitive configuration files
- Keep your bot token and API credentials secure

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).
```
