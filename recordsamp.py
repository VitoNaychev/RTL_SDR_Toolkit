import numpy as np

class RecordSamp:
    def __init__(self, file_name):
        self.file_name = file_name
        self.data_queue = []

    def add_to_queue(self, samples):
        self.data_queue = np.concatinate(self.data_queue, samples)

    def save_to_file(self, file_name = ''):
        if not file_name:
            file_name = self.file_name
        np.save(file_name, self.data_queue)

    def load_from_file(self, file_name = ''):
        if not file_name:
            file_name = self.file_name
        self.data_queue = np.load(file_name)

    def append_from_file(self, file_name = ''):
        if not file_name:
            file_name = self.file_name
        self.data_queue = np.concatinate(self.data_queue, np.load(file_name))

    def append_to_file(self, file_name = ''):
        if not file_name:
            file_name = self.file_name
        prev_data = np.load(file_name)
        np.save(np.concatinate(prev_data, self.data_queue), file_name)
