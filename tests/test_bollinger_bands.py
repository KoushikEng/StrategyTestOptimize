from strategies.Base import Base
from collections import namedtuple
import numpy as np


rng = np.random.default_rng()

BBresults = namedtuple('BBresults', 'middle upper lower')

def bbands(values: np.ndarray) -> BBresults:
    return BBresults(1 + values, 2 + values, 3 + values)

class BBStrategy(Base):
    def init(self):
        val = rng.random(size=10)
        print(val)
        self.bb = self.I(bbands, val)
        
    def next(self):
        print(f"{self.bb.middle[-1]},\t {self.bb.upper[-1]},\t {self.bb.lower[-1]}")
    
    def get_optimization_params():
        pass
    
    def validate_params(self):
        pass
    
if __name__ == '__main__':
    ndarray1 = rng.integers(10, 100, size=10)
    ndarray2 = 10 * rng.random(size=10)
    data = ('SBIN', ndarray1, ndarray2, ndarray2, ndarray2, ndarray2, ndarray1)
    BBStrategy().process(data)
    
    