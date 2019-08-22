from . import AxiStream, Direction
from nmigen import *
from nmigen.cli import main

class PipelineStage(Elaboratable):
    def __init__(self, input_width, func=lambda x:x):
        self.width = input_width
        self.input = AxiStream(input_width, Direction.FANIN, name='input')
        output_width = len(func(self.input.TDATA))
        self.output = AxiStream(output_width, Direction.FANOUT, name='output')
        self.func = func

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        sync = m.d.sync
        with m.If(self.input.accepted()):
            data = self.func(self.input.TDATA)
            sync += self.output.TDATA.eq(data)
            sync += self.output.TVALID.eq(1)
            sync += self.output.TLAST.eq(self.input.TLAST)
        with m.Elif(self.output.accepted()):
            sync += self.output.TDATA.eq(0)
            sync += self.output.TVALID.eq(0)
            sync += self.output.TLAST.eq(0)
        with m.If((self.output.TVALID == 0) | self.output.accepted()):
            comb += self.input.TREADY.eq(1)
        with m.Else():
            comb += self.input.TREADY.eq(0)
        return m

class Pipeline(Elaboratable):
    def __init__(self, input_width, stages):
        self.stages = stages
        self.widths = [input_width]
        res = Signal(input_width)
        for func in stages:
            res = func(res)
            self.widths.append(len(res))
        self.input = AxiStream(self.widths[0], Direction.FANIN, name='input')
        self.output = AxiStream(self.widths[-2], Direction.FANOUT, name='output')

    def elaborate(self, platform):
        m = Module()
        comb = m.d.comb
        modules = [PipelineStage(width, stage)
                   for width, stage in zip(self.widths[:-1], self.stages)]
        for i, stage in enumerate(modules):
            m.submodules['stage_' + str(i)] = stage
        for i in range(1,len(modules)):
            comb += modules[i].input.connect(modules[i-1].output)
        comb += modules[0].input.connect(self.input)
        comb += modules[-1].output.connect(self.output)
        return m

if __name__ == "__main__":
    stages = [lambda x: (x + x)[0:10],
              lambda x: (x + (x << 1))[0:10],
              lambda x: (x + (x >> 2))[0:10],
              lambda x: (x + x)[0:10],
              lambda x: x[0:5] + x[5::]]
    pipeline = Pipeline(10, stages)
    ports = [pipeline.input[f] for f in pipeline.input.fields]
    ports += [pipeline.output[f] for f in pipeline.output.fields]
    main(pipeline, ports=ports, name='pipeline')
