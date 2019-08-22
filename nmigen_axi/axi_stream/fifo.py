from . import AxiStream, Direction
from nmigen import *
from nmigen.cli import main
from nmigen.lib.fifo import AsyncFIFO

class AxiStreamFifo(Elaboratable):
    def __init__(self, width, depth, cd_i='sync', cd_o='sync'):
        self.input = AxiStream(width, Direction.FANIN)
        self.output = AxiStream(width, Direction.FANOUT)
        self.width = width
        self.depth = depth
        self.cd_i = cd_i
        self.cd_o = cd_o

    def elaborate(self, platform):
        m = Module()
        cd_i = m.domain[self.cd_i]
        cd_o = m.domain[self.cd_o]
        comb = m.domain.comb

        fifo = m.submodules.fifo = DomainRenamer({"read": self.cd_i, "write": self.cd_o})(AsyncFIFO(width=self.width, depth=self.depth))

        cd_o += self.output.TDATA.eq(fifo.dout)
        comb += fifo.re.eq((~self.output.TVALID | self.output.accepted()) & fifo.readable)

        with m.If(fifo.re):
            cd_o += self.output.TVALID.eq(1)
        with m.Elif(self.output.accepted()):
            cd_o += self.output.TVALID.eq(0)

        comb += [fifo.din.eq(self.input.TDATA),
                 fifo.we.eq(self.input.accepted())]
        cd_i += self.input.TREADY.eq(fifo.writable)

        return m

if __name__ == '__main__':
    fifo = AxiStreamFifo(5, 16, cd_i='sync', cd_o='sync')
    ports = [fifo.input[f] for f in fifo.input.fields]
    ports += [fifo.output[f] for f in fifo.output.fields]
    main(fifo, ports=ports)

