from nmigen import *
from nmigen.hdl.rec import Direction

class AxiStream(Record):
    def __init__(self, width, direction, name=None, *,fields=None):
        if direction == Direction.FANOUT:
            layout = [('TDATA', width, Direction.FANOUT),
                      ('TVALID', 1, Direction.FANOUT),
                      ('TREADY', 1, Direction.FANIN),
                      ('TLAST', 1, Direction.FANOUT)]

        elif direction == Direction.FANIN:
            layout = [('TDATA', width, Direction.FANIN),
                      ('TVALID', 1, Direction.FANIN),
                      ('TREADY', 1, Direction.FANOUT),
                      ('TLAST', 1, Direction.FANIN)]
        else:
            raise ValueError('direction must be FANIN or FANOUT')
        Record.__init__(self, layout, name=name, fields=fields)

    def accepted(self):
        return (self.TVALID == 1) & (self.TREADY == 1)
