from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq
import subprocess, pyautogui, json, re, time, os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

# 🔑 CONFIG - Load from environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8371709848:AAE7NmVzdQ3Ix7HI__WJUUhlyoLAtgOkHdo")
SKILLRACK_USERNAME = os.getenv("SKILLRACK_USERNAME", "")
SKILLRACK_PASSWORD = os.getenv("SKILLRACK_PASSWORD", "")
SKILLRACK_URL = "https://www.skillrack.com"
SKILLRACK_DCDT_URL = "https://www.skillrack.com/faces/candidate/dailychallenge.xhtml?k=DT"

client = Groq(api_key=GROQ_API_KEY)

# Global states for complex workflows
user_context = {}
browser_driver = None
is_logged_in = False


def capture_failure_screenshots(tag="error"):
    """Capture both browser and desktop screenshots for debugging failures."""
    try:
        base_dir = "C:/Users/jerol/SEC/projects/openclaw/Flowise/openclaw-master/debug_screens"
        os.makedirs(base_dir, exist_ok=True)
        ts = str(int(time.time()))
        safe_tag = re.sub(r"[^a-zA-Z0-9_-]", "_", str(tag))

        browser_path = f"{base_dir}/{safe_tag}_{ts}_browser.png"
        desktop_path = f"{base_dir}/{safe_tag}_{ts}_desktop.png"

        browser_msg = "browser screenshot skipped"
        desktop_msg = "desktop screenshot skipped"

        if browser_driver:
            try:
                browser_driver.save_screenshot(browser_path)
                browser_msg = browser_path
            except Exception as e:
                browser_msg = f"browser screenshot failed: {str(e)}"

        try:
            desktop_img = pyautogui.screenshot()
            desktop_img.save(desktop_path)
            desktop_msg = desktop_path
        except Exception as e:
            desktop_msg = f"desktop screenshot failed: {str(e)}"

        return f"📸 Browser: {browser_msg}\n📸 Desktop: {desktop_msg}"
    except Exception as e:
        return f"📸 Screenshot capture failed: {str(e)}"


def check_login_success():
    """Detect whether login has succeeded based on URL and page elements."""
    try:
        if not browser_driver:
            return False

        current_url = browser_driver.current_url.lower()
        if "candidate" in current_url or "profile.xhtml" in current_url:
            return True

        logout_links = browser_driver.find_elements(By.XPATH, "//a[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'logout')]")
        if logout_links:
            return True

        return False
    except Exception:
        return False


# 🧠 AI THINK FUNCTION
def think(task):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an automation agent for task execution. Break tasks into ordered steps.
Supported actions:
- open_skillrack: Open Skill Rack platform
- signin: Sign in with credentials from environment (no PIN needed)
- navigate_to: Navigate to page (input: page name like 'dc_dt', 'dashboard')
- wait: Wait for time (input: time in seconds like '2s', '3.5s')
- click: Click element (input: element selector/name)
- type: Type text (input: text to type)
- execute_dcdt: Execute DC DT workflow with provided code
- press: Press key (input: key name like 'Enter', 'Tab')
- close_browser: Close browser window
- inspect_page: Get current page structure info
- screenshot: Take browser screenshot

IMPORTANT: Use signin action once with credentials from env - it handles everything.
Do NOT use enter_password or request_pin actions - signin includes password entry.
Only include navigate_to for dc_dt after signin in the sequence.

Reply ONLY valid JSON array format like:
[{"action":"open_skillrack"},{"action":"wait","input":"2s"},{"action":"signin"},{"action":"navigate_to","input":"dc_dt"}]"""
            },
            {"role": "user", "content": task}
        ]
    )
    return response.choices[0].message.content


# ⚙️ EXECUTION ENGINE
def init_browser():
    """Initialize Selenium Chrome driver"""
    global browser_driver
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        browser_driver = webdriver.Chrome(options=options)
        return "✅ Browser initialized"
    except Exception as e:
        return f"❌ Browser init failed: {str(e)}"


def close_browser():
    """Close browser safely"""
    global browser_driver
    try:
        if browser_driver:
            browser_driver.quit()
            browser_driver = None
        return "✅ Browser closed"
    except Exception as e:
        return f"❌ Close browser error: {str(e)}"


def open_skillrack():
    """Open Skill Rack platform"""
    global browser_driver, is_logged_in
    try:
        if not browser_driver:
            init_browser()
        browser_driver.get(SKILLRACK_URL)
        is_logged_in = False
        time.sleep(2)
        return "✅ Opened Skill Rack"
    except Exception as e:
        return f"❌ Open Skill Rack failed: {str(e)}"


def signin():
    """Sign in to Skill Rack with saved credentials"""
    global is_logged_in
    try:
        if not browser_driver:
            init_browser()

        if not SKILLRACK_USERNAME or not SKILLRACK_PASSWORD:
            return "❌ Missing SKILLRACK_USERNAME or SKILLRACK_PASSWORD in .env"

        wait_time = WebDriverWait(browser_driver, 10)
        
        # Step 1: Click the Login button on homepage to show form
        print("🔍 Looking for Login button...")
        login_btn_selectors = [
            (By.LINK_TEXT, "Login"),
            (By.XPATH, "//a[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
        ]
        
        login_clicked = False
        for selector_type, selector_value in login_btn_selectors:
            try:
                login_btn = wait_time.until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                print(f"✅ Found Login button: {selector_type}")
                browser_driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
                login_btn.click()
                login_clicked = True
                time.sleep(2)
                break
            except:
                continue
        
        # Step 2: Find Login Id input - use placeholder as primary selector
        print("🔍 Looking for Login Id field...")
        username_field = None
        username_selectors = [
            (By.XPATH, "//input[@placeholder='Login Id']"),
            (By.XPATH, "//input[@placeholder='login id']"),
            (By.CSS_SELECTOR, "input[placeholder*='Login']"),
            (By.XPATH, "//input[1]"),  # First input field
            (By.NAME, "username"),
            (By.ID, "username"),
        ]
        
        for selector_type, selector_value in username_selectors:
            try:
                username_field = wait_time.until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                print(f"✅ Found Login Id field: {selector_type}")
                break
            except:
                continue
        
        if not username_field:
            print("❌ Could not find Login Id field")
            return "❌ Could not find Login Id field. Try 'inspect page' command."
        
        # Enter username
        username_field.click()
        time.sleep(0.3)
        username_field.clear()
        username_field.send_keys(SKILLRACK_USERNAME)
        print(f"✅ Entered Login Id: {SKILLRACK_USERNAME[:3]}***")
        time.sleep(0.5)
        
        # Step 3: Find Password input field
        print("🔍 Looking for Password field...")
        password_field = None
        password_selectors = [
            (By.XPATH, "//input[@placeholder='Password']"),
            (By.XPATH, "//input[@placeholder='password']"),
            (By.CSS_SELECTOR, "input[placeholder*='Password']"),
            (By.XPATH, "//input[2]"),  # Second input field
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.NAME, "password"),
        ]
        
        for selector_type, selector_value in password_selectors:
            try:
                password_field = wait_time.until(
                    EC.presence_of_element_located((selector_type, selector_value))
                )
                print(f"✅ Found Password field: {selector_type}")
                break
            except:
                continue
        
        if not password_field:
            print("❌ Could not find Password field")
            return "❌ Could not find Password field. Try 'inspect page' command."
        
        # Enter password
        password_field.click()
        time.sleep(0.3)
        password_field.clear()
        password_field.send_keys(SKILLRACK_PASSWORD)
        print(f"✅ Entered Password")
        time.sleep(0.5)
        
        # Step 4: Find and click Login button
        print("🔍 Looking for Login button to submit...")
        login_submit_btn = None
        submit_selectors = [
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[1]"),
            (By.ID, "login"),
            (By.NAME, "login"),
        ]
        
        for selector_type, selector_value in submit_selectors:
            try:
                login_submit_btn = wait_time.until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                print(f"✅ Found Login button to submit: {selector_type}")
                break
            except:
                continue
        
        if not login_submit_btn:
            print("⚠️ Login button not found, pressing Enter...")
            password_field.send_keys("\n")
            time.sleep(4)
            is_logged_in = check_login_success()
            if is_logged_in:
                return "✅ Successfully signed in (used Enter key)!"

            shot_info = capture_failure_screenshots("signin_enter_not_verified")
            return f"❌ Login Enter key was sent but success not verified. URL: {browser_driver.current_url}\n{shot_info}"
        
        # Click login button
        login_submit_btn.click()
        print("✅ Clicked Login button")
        time.sleep(4)

        is_logged_in = check_login_success()
        if is_logged_in:
            return "✅ Successfully signed in!"

        shot_info = capture_failure_screenshots("signin_not_verified")
        return f"❌ Login submit was done but success not verified. URL: {browser_driver.current_url}\n{shot_info}"
    except Exception as e:
        is_logged_in = False
        print(f"❌ Sign in error: {str(e)}")
        shot_info = capture_failure_screenshots("signin_exception")
        return f"❌ Sign in failed: {str(e)}\n{shot_info}"


def navigate_to(location):
    """Navigate to different sections of the platform"""
    global is_logged_in
    try:
        if not browser_driver:
            return "❌ Browser is not initialized"

        # Re-check in case login happened in a previous step.
        is_logged_in = check_login_success() if not is_logged_in else is_logged_in

        if not is_logged_in:
            shot_info = capture_failure_screenshots("navigate_without_login")
            return f"❌ Navigation blocked: Login is not successful yet.\n{shot_info}"

        location = location.lower()
        
        if location in ["dc_dt", "dcdt"]:
            browser_driver.get(SKILLRACK_DCDT_URL)
            time.sleep(2)
            return f"✅ Navigated to DC DT: {SKILLRACK_DCDT_URL}"
        
        elif location == "dashboard":
            browser_driver.get(f"{SKILLRACK_URL}/dashboard")
            time.sleep(2)
            return "✅ Navigated to Dashboard"
        
        else:
            return f"❌ Unknown location: {location}"
            
    except Exception as e:
        return f"❌ Navigation failed: {str(e)}"


def inspect_page():
    """Inspect current page and return HTML structure info for debugging"""
    try:
        # Get page title
        title = browser_driver.title
        
        # Get all input fields
        inputs = browser_driver.find_elements(By.TAG_NAME, "input")
        input_info = []
        for inp in inputs:
            inp_type = inp.get_attribute("type")
            inp_id = inp.get_attribute("id")
            inp_name = inp.get_attribute("name")
            inp_placeholder = inp.get_attribute("placeholder")
            input_info.append(f"  - type={inp_type}, id={inp_id}, name={inp_name}, placeholder={inp_placeholder}")
        
        # Get all buttons
        buttons = browser_driver.find_elements(By.TAG_NAME, "button")
        button_info = []
        for btn in buttons[:5]:  # Only first 5
            btn_text = btn.text[:50]
            btn_type = btn.get_attribute("type")
            button_info.append(f"  - text='{btn_text}', type={btn_type}")
        
        info = f"""
📄 Page: {title}
🔍 Input Fields: {len(inputs)}
{chr(10).join(input_info)}
🔘 Buttons: {len(buttons)}
{chr(10).join(button_info)}
"""
        return info
    except Exception as e:
        return f"❌ Inspection failed: {str(e)}"


def take_screenshot(filename="screenshot.png"):
    """Take screenshot of current page for debugging"""
    try:
        full_path = f"C:/Users/jerol/SEC/projects/openclaw/Flowise/openclaw-master/{filename}"
        browser_driver.save_screenshot(full_path)
        return f"✅ Screenshot saved: {full_path}"
    except Exception as e:
        return f"❌ Screenshot failed: {str(e)}"


def wait_for(duration):
    """Wait for specified time or element"""
    try:
        # If it's a number or time format like "2s", "3.5s", etc.
        if isinstance(duration, str):
            if duration.endswith('s'):
                duration = float(duration.rstrip('s'))
            else:
                duration = float(duration)
        time.sleep(float(duration))
        return f"✅ Waited {duration}s"
    except Exception as e:
        return f"❌ Wait failed: {str(e)}"


def click_element(selector):
    """Click on element by selector"""
    try:
        element = WebDriverWait(browser_driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, selector))
        )
        element.click()
        time.sleep(1)
        return f"✅ Clicked: {selector}"
    except Exception as e:
        return f"❌ Click failed: {str(e)}"


def execute_dcdt(code):
    """Execute DC DT code (placeholder for custom DC DT logic)"""
    try:
        # This is a placeholder - user will provide the actual DC DT code
        # For now, we'll execute it as a function
        exec_globals = {
            'browser': browser_driver,
            'wait': lambda s: time.sleep(s),
            'click': click_element,
            'WebDriverWait': WebDriverWait,
            'By': By,
            'EC': EC,
        }
        exec(code, exec_globals)
        return "✅ DC DT code executed"
    except Exception as e:
        return f"❌ DC DT execution failed: {str(e)}"


def execute(action, data):
    """Main execution dispatcher"""
    action = action.lower().strip()

    try:
        if action in ["open", "open_notepad", "launch", "start"]:
            subprocess.Popen("notepad")
            return "✅ Opened Notepad"

        elif action == "open_skillrack":
            return open_skillrack()

        elif action == "signin":
            return signin()

        elif action == "inspect_page":
            return inspect_page()

        elif action == "screenshot":
            return take_screenshot(data if data else "screenshot.png")

        elif action == "navigate_to":
            return navigate_to(data)

        elif action == "wait":
            return wait_for(data)

        elif action == "click":
            return click_element(data)

        elif action == "type":
            pyautogui.write(data, interval=0.05)
            return f"✅ Typed: {data}"

        elif action == "press":
            pyautogui.press(data)
            return f"✅ Pressed: {data}"

        elif action == "execute_dcdt":
            return execute_dcdt(data)

        elif action == "close_browser":
            return close_browser()

        else:
            return f"❌ Unknown action: {action}"

    except Exception as e:
        shot_info = capture_failure_screenshots(f"execute_{action}")
        return f"⚠️ Execution error [{action}]: {str(e)}\n{shot_info}"


# 📱 TELEGRAM HANDLERS
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main message handler for automation requests"""
    task = update.message.text
    user_id = update.message.from_user.id

    print(f"📨 Task from {user_id}: {task}")
    
    # Get AI response
    decision = think(task)
    print("🤖 AI Response:", decision)

    try:
        # Extract JSON array from response
        match = re.search(r'\[.*\]', decision, re.DOTALL)

        if match:
            actions = json.loads(match.group())
            print(f"📋 Action sequence: {len(actions)} steps")
            
            results = []
            
            # Execute each action in sequence
            for idx, act in enumerate(actions):
                action_name = act.get("action", "").lower().strip()
                action_input = act.get("input", "")
                
                print(f"  Step {idx+1}/{len(actions)}: {action_name}")
                result = execute(action_name, action_input)
                results.append(result)
                print(f"    Result: {result[:80]}")

                if result.startswith("❌") or result.startswith("⚠️"):
                    if "📸" not in result:
                        results.append(capture_failure_screenshots(f"step_{idx+1}_{action_name}"))
                    break

            # Send all results to user
            final_result = "\n".join(results)
            await update.message.reply_text(final_result)

        else:
            await update.message.reply_text("❌ Invalid AI response format")

    except json.JSONDecodeError as e:
        await update.message.reply_text(f"⚠️ JSON Parse Error: {str(e)[:100]}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)[:200]}")


# 🚀 START BOT
app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .job_queue(None)
    .persistence(None)
    .build()
)

# Add simple message handler
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("🚀 Telegram AI Agent Running...")
print("✅ Supported actions: open_skillrack, signin, navigate_to, wait, click, type, press, inspect_page, screenshot, execute_dcdt")
print("📝 Send a task like: 'Open Skill Rack, sign in, go to DC DT'")
print("⏳ Waiting for messages...")
app.run_polling()