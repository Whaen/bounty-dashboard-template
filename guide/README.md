## Steps
1. Download python 3.10, Open your cloned repo with vscode and choose python 3.10 as your python file version
2. Create virtual env, `python -m venv .venv`
3. Activate virtual env, `.venv\Scripts\activate` | Deactivate, `deactivate`
4. Install package, `pip install -r requirements.txt`
5. Edit `cfg/setting.yaml`:
   * `blockchain-list`:
      * The `Key` element in `blockchain-list` must same as the Header 3 (###) title as your blockchain name in `README.md`
      * Fill the payout tokens in each blockchain, the chain name must unique to the tokens name
   * `API`:
      * This is the api-code name of a tokens on Coingecko
      * The `Key` element name must same as the tokens name in `blockchain-list`
   * `year`:
      * Set the year, the year must same as the Header 2 (##) title as your year in `README.md`
6. Record the payout on `README.md`
7. Run Streamlit Webpage, `streamlit run app.py`
8. If something wrong on the charts, please find `whaen`, he will guide you on how to edit the charts config.

> NOTE: dataframe is save in `data` folder, it contains the sum, take a look