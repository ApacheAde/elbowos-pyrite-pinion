# Pyrite Pinion

Full-colour **Python 3** neon gear-ride arcade for [ElbowOS](https://x.com/ElbowOS).

Spin interlocking brass and teal pinions, hop the ember orb between rims, and scoop gold nuggets. Rust spikes break your combo and drop you back to the drive gear.

Featured: **https://x.com/ElbowOS**

Reel (9:16 MP4): [PYRITE_PINION_ElbowOS.mp4 on Google Drive](https://drive.google.com/file/d/1vypomoEAOKYtWE2d9_IKcIFiU08MzYta/view?usp=drivesdk)

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 pyrite_pinion.py --play
```

- A / D or arrows — spin the gear train
- Space — hop to a neighbouring pinion
- R — reset
- Esc — quit

Needs Python 3.10+ and a desktop window (pygame + SDL).

## Record a 15s autoplay reel

```bash
ELBOWOS_RECORD=1 python3 pyrite_pinion.py
```

Writes `/home/workdir/artifacts/PYRITE_PINION_ElbowOS.mp4` (1080×1920, H.264).
