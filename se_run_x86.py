import argparse, m5
from m5.objects import *
from m5.stats import dump as stats_dump, reset as stats_reset, enable as stats_enable

def _bp(n):
    return {"LocalBP":LocalBP,"LTAGE":LTAGE,"TAGE_SC_L":TAGE_SC_L}.get(n,TournamentBP)()

def _l1():
    c=Cache();c.size="32kB";c.assoc=2;c.tag_latency=c.data_latency=c.response_latency=2;c.mshrs=8;c.tgts_per_mshr=16;return c
def _l2():
    c=Cache();c.size="256kB";c.assoc=8;c.tag_latency=c.data_latency=c.response_latency=10;c.mshrs=16;c.tgts_per_mshr=16;return c

def build(a):
    s=System()
    s.clk_domain=SrcClockDomain();s.clk_domain.clock=a.cpu_clock;s.clk_domain.voltage_domain=VoltageDomain()
    s.mem_mode='timing';s.mem_ranges=[AddrRange(a.mem_size)]
    s.membus=SystemXBar(); l2bus=L2XBar()
    s.cpu=DerivO3CPU();s.cpu.branchPred=_bp(a.bp)
    for w in ["fetch","decode","issue","commit"]: setattr(s.cpu,w+"Width",a.width)
    s.cpu.numThreads=max(1,a.smt)
    s.cpu.icache=_l1();s.cpu.dcache=_l1()
    s.cpu.icache_port=s.cpu.icache.cpu_side;s.cpu.dcache_port=s.cpu.dcache.cpu_side
    s.cpu.icache.mem_side=l2bus.slave;s.cpu.dcache.mem_side=l2bus.slave
    s.l2=_l2(); s.l2.cpu_side=l2bus.master;s.l2.mem_side=s.membus.slave
    try: s.cpu.createInterruptController();s.cpu.itb.walker.port=s.membus.slave;s.cpu.dtb.walker.port=s.membus.slave
    except: pass
    s.mem_ctrl=MemCtrl();s.mem_ctrl.dram=DDR3_1600_8x8();s.mem_ctrl.dram.range=s.mem_ranges[0];s.mem_ctrl.port=s.membus.master
    s.system_port=s.membus.slave
    s.workload=SEWorkload.init_compatible(a.cmd);p=Process(cmd=[a.cmd]);s.cpu.workload=p;s.cpu.createThreads()
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cmd",required=True);ap.add_argument("--bp",default="TournamentBP")
    ap.add_argument("--width",type=int,default=2);ap.add_argument("--smt",type=int,default=1)
    ap.add_argument("--cpu-clock",default="2GHz");ap.add_argument("--mem-size",default="512MB")
    a=ap.parse_args()

    sys=build(a);root=m5.objects.Root(full_system=False,system=sys)
    m5.instantiate()

    # Enable stats before running
    stats_enable(); stats_reset()

    # Force simulate fixed ticks to accumulate stats
    limit_ticks = 20_000_000   # 20 million ticks
    ev = m5.simulate(limit_ticks)

    print("Stopped @", m5.curTick(), "cause:", ev.getCause())

    # dump stats
    stats_dump()
    # finalize
    try: m5.simulate(1)
    except: pass

if __name__=="__main__": main()
