# 🤖 Telegram AI Automation Agent

Advanced automation agent that uses Groq AI to break down complex tasks into executable steps. Supports Skill Rack platform integration with PIN verification and DC DT workflows.

## 🚀 Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download ChromeDriver
- Download from: https://chromedriver.chromium.org/
- Place in your system PATH or project folder

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

**Required Environment Variables:**
- `BOT_TOKEN` - Your Telegram Bot Token (from @BotFather)
- `GROQ_API_KEY` - Your Groq API key
- `SKILLRACK_USERNAME` - Your Skill Rack username
- `SKILLRACK_PASSWORD` - Your Skill Rack password

## 📋 Supported Actions

| Action | Input | Description |
|--------|-------|-------------|
| `open_skillrack` | - | Open Skill Rack platform |
| `signin` | - | Sign in with saved credentials |
| `enter_password` | - | Enter saved password in field |
| `request_pin` | - | Ask user for PIN via Telegram |
| `navigate_to` | `dc_dt` / `dashboard` | Navigate to platform sections |
| `wait` | `2s` or selector | Wait for time or element |
| `click` | xpath selector | Click element |
| `type` | text | Type text in focused field |
| `press` | key name | Press key (enter, tab, etc) |
| `execute_dcdt` | code | Execute custom DC DT code |
| `close_browser` | - | Close browser window |

## 💬 Usage Examples

### Example 1: Simple Skill Rack Login
```
"Open Skill Rack and sign in"
```

AI will generate:
```json
[
  {"action": "open_skillrack"},
  {"action": "wait", "input": "2s"},
  {"action": "signin"},
  {"action": "wait", "input": "2s"}
]
```

### Example 2: Navigate to DC DT with PIN
```
"Open Skill Rack, sign in, ask for PIN, and go to DC DT"
```

AI will generate:
```json
[
  {"action": "open_skillrack"},
  {"action": "signin"},
  {"action": "request_pin"},
  {"action": "navigate_to", "input": "dc_dt"}
]
```

When `request_pin` is hit, bot asks Telegram user for PIN, waits for response, then continues.

## 🎯 DC DT Custom Code

You can provide custom DC DT logic. Available variables in DC DT code context:
- `browser` - Selenium WebDriver instance
- `wait()` - Sleep function
- `click()` - Click element function
- `WebDriverWait` - Selenium WebDriverWait
- `By` - Selenium By locators
- `EC` - Selenium expected conditions

### Example DC DT Code Template
```python
# Available: browser, WebDriverWait, By, EC, click, wait

# Find and click DC DT table
table = WebDriverWait(browser, 10).until(
    EC.presence_of_element_located((By.ID, "dcdt_table"))
)

# Click cells to input data
cell1 = table.find_element(By.XPATH, "//td[1]")
cell1.click()
pyautogui.write("100", interval=0.05)

# Navigate to next
browser.find_element(By.XPATH, "//button[@id='next']").click()
wait(1)
```

Send to bot:
```
"Execute this DC DT workflow: [your code here]"
```

## 🔐 Security Notes

⚠️ **Important:**
- Never commit `.env` file to git
- Use strong passwords
- Credentials stored in environment variables, not in code
- Consider using a password manager for Skill Rack credentials
- Bot API tokens should be rotated periodically

## 🛠️ Troubleshooting

### ChromeDriver Issues
```bash
# Check Chrome version
google-chrome --version

# Download matching ChromeDriver version
# https://chromedriver.chromium.org/downloads
```

### Selenium Element Not Found
- Increase wait time: `"wait": "5s"`
- Verify XPath selectors using browser DevTools
- Use full page screenshots for debugging

### Groq API Errors
- Verify API key in .env
- Check Groq rate limits

## 📝 Workflow Example: Complete Skill Rack Process

User sends: `"Open Skill Rack, log me in, verify my PIN, and put my DC DT scores"`

Agent generates:
```json
[
  {"action": "open_skillrack"},
  {"action": "wait", "input": "2s"},
  {"action": "signin"},
  {"action": "wait", "input": "1s"},
  {"action": "request_pin"},
  {"action": "navigate_to", "input": "dc_dt"},
  {"action": "wait", "input": "2s"},
  {"action": "execute_dcdt", "input": "[your DC DT code]"}
]
```

Process:
1. ✅ Opens Skill Rack
2. ✅ Waits 2 seconds
3. ✅ Signs in with saved password
4. ✅ Waits 1 second
5. 🔐 Sends Telegram: "Please enter your PIN"
6. ⏳ Waits for user to respond in Telegram
7. ✅ After PIN received, navigates to DC DT
8. ✅ Waits 2 seconds for page load
9. ✅ Executes your custom DC DT code

## 🚀 Run Bot

```bash
# With activated virtual environment
python telegram_agent.py

# Output:
# 🚀 Telegram AI Agent Running...
# ✅ Supported actions: open_skillrack, signin, enter_password, ...
```

Then message your Telegram bot with tasks!

## 📚 AI Prompt Engineering Tips

Give clear, specific instructions:
- ❌ "Fix this" 
- ✅ "Open Skill Rack, log in with saved password, ask for PIN, then navigate to DC DT section"

The AI will break it into proper action steps automatically.
