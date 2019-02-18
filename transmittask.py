import subprocess
import tempfile
import os
from recordsamp import RecordSamp

class TransmitTask:
    def __init__(self, samp_rate, in_file):
        self.samp_rate = samp_rate
        self.in_file = in_file
        self.read_samp = RecordSamp(self.in_file)
        self.read_samp.load_from_file()
        # position in file
        self.pos = 0
        # shitty naming - must fix


    def execute(self):
        pass

    async def run(self, freq):
       # Read chunks of data from file with size samp_size until EOF
       # Move sendiq to cur directory
        data = self.execute()
        while not data:
            data = self.execute()
            f= tempfile.NamedTemporaryFile(mode = 'w+b', prefix = 'tmp', delete = False)
            file_name = f.name

            data.tofile(file_name)
            subprocess.run(['sendiq', '-s ' + str(self.samp_rate), 
                    '-f ' + str(freq), '-t ' + 'double', '-i ' + file_name])
            os.unlink(f.name)
            
            data = self.execute()

