from abc import ABC, abstractmethod


class Provider(ABC):

    def __init__(self, name, model):
        self.name = name
        self.model = model

    def change_model(self, new_model):
        self.model = new_model

    @abstractmethod
    def generate_content_stream(self, prompt):
        """ Streams output, used as a generator """
        pass
    
    @abstractmethod
    def read(self, prompt):
        """ Reads for context, doesn't print or yeild/return anything """
        pass

    @abstractmethod
    def clear_history(self):
        """ Clears chat history """
        pass

    @abstractmethod
    def compact(self):
        """ Compacts the coversation, returns compacted version as a string, no side effects """
        pass

    
    