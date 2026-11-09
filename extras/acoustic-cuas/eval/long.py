import glob, collections, numpy as np, os, warnings, json
warnings.filterwarnings("ignore")
import bench
C=bench.C
g=collections.defaultdict(list)
for p in sorted(glob.glob("/workspace/acoustic-data/ood/neaptide_*/*/*.wav")):
    b=os.path.basename(p).rsplit("_",1)[0]; g[b].append(p)
out=[]
d=bench.fz()
for k,ps in g.items():
    x=np.concatenate([bench.to8k(*bench.read(p)) for p in ps])
    r=C.UAVAcousticOrchestrator(sr=8000).analyze_stream(x, flyby_window_s=None)
    probs=[d.score(x[s:s+8000].astype(np.float32))[0] for s in range(0,len(x)-8000+1,4000)]
    out.append((k, round(len(x)/8000,1), r.uav_detected, r.signal_quality["snr_post_dsp_db"], r.signal_quality["median_spectral_flatness"], r.kinematics_doppler["Intrinsic_BPF0_Hz"], round(float(np.mean(np.array(probs)>=d.m.thr)),2)))
for o in out: print(o)
print("CUAS det", sum(o[2] for o in out), "/", len(out))
