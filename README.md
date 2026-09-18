# b3313-Navigator-Fork
An overhauled, AI/vibecoded fork of the original navigator for the sm64 ROM hack b3313.

An interactive Python navigation engine and pathfinder designed to help players navigate the massive, interconnected map of the *Super Mario 64* creepypasta ROM hack, **B3313**. 

By parsing stage layouts and warp relationships, this script functions like a GPS, providing clear, chronological step-by-step instructions from your starting room to your destination.

---

## 📜 Project History & Credits

Since I had the original file from the wiki and archive sitting on my hard drive and it didn't work anymore, I figured I'd just make it work again. 


This repository is an updated and repaired continuation of the original B3313 navigator. 

* **The Original Work:** This tool was originally developed by an anonymous creator.
  👉 [Original Files](https://github.com/creeper3010/b3313-Navigator-Fork/tree/Original-Internet-Archive-files)
* **The Archive Source:** The original source script was preserved and can be referenced via the historical backup hosted on the Internet Archive:  
  👉 [Internet Archive - B3313 Navigator Item Record](https://archive.org/details/b3313-navigator)
* **Wiki Reference:** The script was historically recognized and linked directly under the official wiki's **Enhance Your Gameplay** section:  
  👉 [Official B3313 Wiki - Enhance Your Gameplay](https://miraheze.org)

* **What's New in this Version:** 
  * Fixed a fundamental `dijkstar` math layout routing error that previously resulted in a permanent "Unable to find path".
  * Reversed the pathfinder algorithm logic so instructions are presented **forward/chronologically** (from the player's walking perspective) rather than backwards.
  * Implemented an inline, real-time terminal progress bar for the initial database building process.

---

## 🛠️ Features

* 📍 **Chronological Tracking:** Gives clear directional descriptions moving forward from stage to stage.
* 🛑 **Custom Constraints:** Options to skip paths requiring RNG, item caps (Vanish/Metal/Wing), or mandatory game deaths.
* 📦 **Smart Cache System:** Downloads and maps the network configuration from the wiki once, saving it to a local `map` binary for instant subsequent launches.
* ⏳ **Visual Progress Bar:** Real-time feedback during the initial deep-scan map compilation.

---

## 🚀 Getting Started

### Prerequisites
You need Python 3.10+ and a few third-party libraries. Install the dependencies via your terminal:

```bash
pip install networkx matplotlib beautifulsoup4 requests dijkstar regex
```

### Running the Tool
Run the script from your project directory:

```bash
python nav.py
```
*Note: On the very first launch, the tool will automatically crawl the wiki to compile its local map database . This may take a minute or two. Subsequent boots are instant.*

---

## ⚖️ License & Disclaimer
This project is shared purely for educational, archival, and tool-preservation purposes within the custom gaming community. All data is scraped from the public community-driven B3313 Wiki.
