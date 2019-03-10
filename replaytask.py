from transmittask import TransmitTask

class ReplayTask(TransmitTask):
    def execute(self):
        if self.pos >= len(self.read_samp.data_queue):
            return False

        data = self.read_samp.data_queue[self.f_pos:self.pos + self.samp_rate]
        self.pos += self.samp_rate

        return data
