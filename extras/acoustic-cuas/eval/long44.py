import glob, collections, numpy as np, os, warnings
warnings.filterwarnings("ignore")
import bench
C=bench.C
g=collections.defaultdict(list)
for p in sorted(glob.glob("/workspace/acoustic-data/ood/neaptide_*/*/*.wav")):
    g[os.path.basename(p).rsplit("_",1)[0]].append(p)
det=0
for k,ps in g.items():
    xs=[bench.read(p) for p in ps]; sr=xs[0][1]; x=np.concatenate([a for a,_ in xs])
    r=C.UAVAcousticOrchestrator(sr=sr).analyze_stream(x, flyby_window_s=None); det+=r.uav_detected
    print(k, sr, r.uav_detected, r.signal_quality["snr_post_dsp_db"], r.kinematics_doppler["Intrinsic_BPF0_Hz"], r.propulsion_physics["estimated_blades_nb"])
print("det",det,len(g))
