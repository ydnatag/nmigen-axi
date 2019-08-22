import os
from nmigen_axi.axi_stream.fifo import AxiStreamFifo
from .driver import AxiStream
from nmigen_cocotb import run, get_clock_signal, get_reset_signal

try:
    import cocotb
    from cocotb.triggers import Timer, RisingEdge, Combine, Join
    from cocotb.clock import Clock
except:
    pass

CD_I = 'input'
CD_O = 'output'

def init_axis_signals(axi, direction):
    if direction == 'input':
        axi.bus.TVALID <= 0
        axi.bus.TDATA <= 0
        axi.bus.TLAST <= 0
    elif direction == 'output':
        axi.bus.TREADY <= 0

def start_clock(dut, dommain, period=10, units='ns'):
    clk = get_clock_signal(dut, dommain)
    cocotb.fork(Clock(clk, period, units).start())

@cocotb.coroutine
def reset_pulse(dut, domain, cycles=10, logic='positive'):
    rst = get_reset_signal(dut, domain)
    clk = get_clock_signal(dut, domain)
    rst <= (0 if logic == 'negative' else 1)
    for _ in range(cycles):
        yield RisingEdge(clk)
    rst <= (1 if logic == 'negative' else 0)

@cocotb.test()
def fast_to_slow(dut):
    axi_input = AxiStream(dut, 'input_', get_clock_signal(dut, CD_I))
    axi_output = AxiStream(dut, 'output_', get_clock_signal(dut, CD_O))
    init_axis_signals(axi_input, 'input')
    init_axis_signals(axi_output, 'output')

    start_clock(dut, CD_I, 10, 'ns')
    start_clock(dut, CD_O, 20, 'ns')

    yield Combine(reset_pulse(dut, CD_I), reset_pulse(dut, CD_O))

    yield Timer(100, 'ns')

def get_ports(m):
    ports = [m.input[f] for f in m.input.fields]
    ports += [m.output[f] for f in m.output.fields]
    return ports


if __name__ == '__main__':
    fifo = AxiStreamFifo(width=50, depth=256, cd_i=CD_I, cd_o=CD_O)
    run(fifo, 'nmigen_axi.test.axi_stream.test_fifo', ports=get_ports(fifo), vcd_file='output.vcd')
