import subprocess
import sys
import os
import re
import time
import threading

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from providers.gemeni import GemeniWorker
from utils.constant_prompts import *

# ── ANSI styles ────────────────────────────────────────────────────────────────
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
RED     = "\033[31m"

def term_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80

def separator():
    print(f"{DIM}{'─' * term_width()}{RESET}")

def render_bold(text):
    """Convert **markdown bold** to ANSI bold."""
    return re.sub(r'\*\*(.*?)\*\*', lambda m: f"{BOLD}{m.group(1)}{RESET}", text, flags=re.DOTALL)

def print_response(name, text):
    print(f"\n  {BOLD}{MAGENTA}◆ {name}{RESET}\n")
    rendered = render_bold(text)
    for line in rendered.splitlines():
        print(f"  {line}")


# ── Spinner ────────────────────────────────────────────────────────────────────
class Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message, color=CYAN):
        self.message = message
        self.color = color
        self._running = False
        self._thread = None

    def _run(self):
        i = 0
        while self._running:
            f = self.FRAMES[i % len(self.FRAMES)]
            print(f"\r  {self.color}{f}{RESET} {self.message}   ", end="", flush=True)
            time.sleep(0.08)
            i += 1

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, success=True):
        self._running = False
        if self._thread:
            self._thread.join()
        icon = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
        print(f"\r  {icon} {self.message}   ")


def animate_summary():
    frames = ["◐", "◓", "◑", "◒"]
    for i in range(24):
        f = frames[i % len(frames)]
        print(f"\r  {MAGENTA}{f}{RESET} Compiling summary...", end="", flush=True)
        time.sleep(0.055)
    print(f"\r  {GREEN}●{RESET} Done                        \n")


def get_response(agent, prompt):
    whole = ""
    for chunk in agent.generate_content_stream(prompt):
        whole += chunk
    return whole


# ── Main loop ──────────────────────────────────────────────────────────────────
agent     = None
running   = True
iterations = 0
incommand = False
command_q = []

while running:
    if iterations == 0:
        separator()
        print(f"\n  {BOLD}{CYAN}✦  GenieCLI{RESET}")
        print(f"  {DIM}Enter agent name and model separated by a space{RESET}")
        print(f"  {DIM}e.g.  BOB gemini-2.5-flash-lite{RESET}\n")
        separator()

    if not incommand:
        print(f"\n{BOLD}{BLUE}❯{RESET} ", end="")
        inp = input()
        if not inp.strip():
            continue
        print()
        separator()

    if inp.lower() in ("q", "quit"):
        if iterations != 0:
            agent.clear_history()
        print(f"\n  {DIM}Goodbye.{RESET}\n")
        running = False
        continue

    if iterations == 0:
        parts = inp.split()
        agent = GemeniWorker(parts[0], parts[1])
        print(f"\n  {GREEN}✓{RESET} Agent {BOLD}{parts[0]}{RESET} ready · model {BOLD}{parts[1]}{RESET}\n")
        separator()

    elif not incommand:
        spinner = Spinner("Thinking...", color=CYAN)
        spinner.start()
        response = get_response(agent, inp)
        spinner.stop()

        match = re.search(r'\[CMD\](.*?)\[/CMD\]', response, re.DOTALL)
        if match:
            incommand = True
            command_q.append(match.group(1).strip())
        else:
            print_response(agent.name, response)

    elif incommand:
        cmd = command_q[-1]
        cmd_preview = cmd.split('\n')[0][:72]

        spinner = Spinner(f"Executing: {BOLD}{cmd_preview}{RESET}", color=YELLOW)
        spinner.start()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                shell=True
            )
            spinner.stop(success=True)
            agent.read("Success:\n" + result.stdout)

        except subprocess.CalledProcessError as e:
            spinner.stop(success=False)
            agent.read(f"Command failed with exit code: {e.returncode}\nError output:\n{e.stderr}")

        except FileNotFoundError as e:
            spinner.stop(success=False)
            agent.read(f"The specified program or command could not be found: {e}")

        thinking = Spinner("Thinking...", color=CYAN)
        thinking.start()
        response = get_response(agent, CONTINUATION_PROMPT)
        thinking.stop()

        match = re.search(r'\[CMD\](.*?)\[/CMD\]', response, re.DOTALL)
        if match:
            incommand = True
            command_q.append(match.group(1).strip())
        else:
            incommand = False
            animate_summary()
            print_response(agent.name, response)

    print()
    separator()
    iterations += 1
