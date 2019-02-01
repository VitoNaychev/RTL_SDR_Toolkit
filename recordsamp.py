import numpy as np

class RecordSamp:
    def __init__(self, file_name):
        self.file_name = file_name
        self.data_queue = np.array([])

    def is_queue_empty(self):
        return not self.data_queue.any()

    def empty_queue(self):
        self.data_queue = np.array([])
    
    def add_to_queue(self, samples):
        self.data_queue = np.concatenate((self.data_queue, samples))

    def save_to_file(self, file_name = ''):
        if not file_name:
            file_name = self.file_name
        np.save(file_name, self.data_queue)

    def load_from_file(self, file_name = ''):
        if not file_name:
            file_name = self.file_name
        self.data_queue = np.load(file_name)
        return self.data_queue

    def append_from_file(self, file_name = ''):
        if not file_name:
            file_name = self.file_name
        self.data_queue = np.concatenate((self.data_queue, np.load(file_name)))
        return self.data_queue

    def append_to_file(self, file_name = ''):
        if not file_name:
            file_name = self.file_name
        prev_data = np.load(file_name)
        np.save(np.concatenate((prev_data, self.data_queue)), file_name)
