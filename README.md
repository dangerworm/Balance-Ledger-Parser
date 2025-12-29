# Balance-Ledger-Parser

A script which aims to parse a bound merchant ledger dating to circa 1770

## Usage

In Ubuntu: create a venv + install Kraken

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

python3 -m venv ~/venvs/kraken
source ~/venvs/kraken/bin/activate

pip install --upgrade pip
pip install pytorch
pip install "kraken[pdf]"
```

### Advice from ChatGPT

A typical “one image → text” flow is:

- Binarize (optional but often helps old paper)
- Segment (lines)
- Recognize using a model

You’ll need a model (.mlmodel). If you don’t have one yet, you can:

- try an existing model that’s “close enough” (Latin handwriting / historical print), then
- fine-tune on your own hand later (best results)

### Run

```bash
source ~/venvs/kraken/bin/activate
python kraken_batch_zip.py "/mnt/c/Path/To/ledger.zip" --model "/mnt/c/Path/To/model.mlmodel"
```
