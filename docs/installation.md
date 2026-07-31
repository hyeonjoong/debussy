# Installation

DEBUSSY requires Python ≥ 3.10.

## From PyPI

```bash
pip install debussy-audio
```

The core install pulls in `librosa`, `mosqito`, `soundfile`, `numpy` and `scipy`.

## Optional extras

```bash
pip install "debussy-audio[plot]"   # matplotlib figures (spectrogram, radar, tiers)
pip install "debussy-audio[test]"   # pytest + pytest-cov
pip install "debussy-audio[dev]"    # test + plot + ruff + mkdocs-material
```

## System dependency: ffmpeg (optional)

Reading WAV/FLAC/OGG needs only `libsndfile` (bundled with the `soundfile`
wheel). For MP3/M4A or other formats not covered by your libsndfile build,
install `ffmpeg` and transcode to WAV first — see
[Troubleshooting](troubleshooting.md).

```bash
# macOS
brew install ffmpeg
# Debian/Ubuntu
sudo apt-get install -y ffmpeg libsndfile1
```

## From source

```bash
git clone https://github.com/hyeonjoong/debussy
cd debussy
pip install -e ".[dev]"
pytest -q
```

## Verify

```bash
python -c "import debussy; print(debussy.__version__)"
debussy --help
```
