class Commands:
    def __init__(self, provider):
        self.provider = provider
    
    def detect_command(self, command):
        if command[0] != '/':
            return False
        
        if command[1:] == "clear":
            self.provider.clear_history()
        
        if command[1:] == "compact":
            self.provider.clear_history
            self.provider.read(self.provider.compact())
        
        if command[1:] == "exit":
            self.provider.clear_history
            self.provider = None
            
            