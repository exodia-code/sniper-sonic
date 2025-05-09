# Sniper (Sonic Network)

## Supported DEX
- [Shadow Exchange](https://www.shadow.so/)
- [Metropolis](https://metropolis.exchange/)

## Featured
- Scan new deployed tokens (real-time)

# Installation

## Termux Installation (Recommended: use VPN)

1. Install proot-distro Environment.
```bash
pkg update && pkg upgrade
pkg install proot-distro git
```

2. Install Ubuntu in the Environment.
```bash
proot-distro install ubuntu
proot-distro login ubuntu
```

3. Install Fundamental Dependencies.
```bash
apt update && apt upgrade
apt install python3 python3-pip build-essential git
```

4. Clone the repository and install core dependencies.
```bash
git clone https://github.com/exodia-code/sniper-sonic
cd sniper-sonic
pip install -r requirements.txt
```

5. Enjoy the App.
```bash
python3 main.py
```

## Linux Installation

1. Update and upgrade system.
```bash
apt update && apt upgrade
```

2. Clone the repository and install dependencies.
```bash
git clone https://github.com/exodia-code/sniper-sonic
cd sniper-sonic
pip install -r requirements.txt
```

3. Run the application.
```bash
python3 main.py
```