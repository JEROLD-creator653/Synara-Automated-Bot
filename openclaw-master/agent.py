from groq import Groq
import json, subprocess, pyautogui

client = Groq(api_key="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")

def think(task):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
           {"role": "system", "content": 
"Reply ONLY JSON with actions: open, type, press. Example: {\"action\":\"open\",\"input\":\"notepad\"}"},
            {"role": "user", "content": task}
        ]
    )
    return response.choices[0].message.content

def execute(action, data):
    if action in ["open", "open_notepad"]:
        subprocess.Popen("notepad")

    elif action == "type":
        pyautogui.write(data)

    elif action == "press":
        pyautogui.press(data)

    return "done"

while True:
    task = input(">>> ")
    decision = think(task)
    print("AI:", decision)
    try:
        d = json.loads(decision)
        print(execute(d["action"], d["input"]))
    except:
        print("Error parsing:", decision)