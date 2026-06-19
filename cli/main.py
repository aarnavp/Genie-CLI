import subprocess
import sys
import os
import re

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

from providers.gemeni import GemeniWorker
from utils.constant_prompts import *

agent = None
running = True
iterations = 0
incommand = False
command_q = []
while running:
    print("incommand? ")
    print(incommand)
    if iterations == 0:
        print("Write name of agent then exact model seperated by one singular space (the name shouldn't have any spaces) ex: BOB gemeni-3.5-flash")
    
    if not incommand:
        inp = input()
    if inp.lower() == "q" or inp.lower() == "quit":
        if iterations != 0:
            agent.clear_history()
        running = False
    
    if iterations == 0:
        agent = GemeniWorker(inp.split()[0], inp.split()[1])
    elif not incommand:
        whole_command = ""
        for chunk in agent.generate_content_stream(inp):
            print(chunk, end="", flush=True)
            whole_command += chunk
        
        match = re.search(r'\[CMD\](.*?)\[/CMD\]', whole_command, re.DOTALL)
        if match:
            incommand = True
            command_q.append(match.group(1).strip())
    elif incommand:
        
        cmd = command_q[-1]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                shell=True
            )
            agent.read("Success:\n" + result.stdout)

        except subprocess.CalledProcessError as e:
            agent.read(f"Command failed with exit code: {e.returncode}\nError output:\n{e.stderr}")

        except FileNotFoundError as e:
            agent.read(f"The specified program or command could not be found: {e}")
        
        print("FLAG 1")

        whole_command = ""
        for chunk in agent.generate_content_stream(CONTINUATION_PROMPT):
            print(chunk, end="", flush=True)
            whole_command += chunk
        
        print("FLAG 2")

        match = re.search(r'\[CMD\](.*?)\[/CMD\]', whole_command, re.DOTALL)
        if match:
            print("inside result for CONTINUATION_PROMPT")
            incommand = True
            command_q.append(match.group(1).strip())
        else:
            incommand = False
        
        
        
        

    
    print()
    iterations += 1


#BOB gemini-2.5-flash-lite