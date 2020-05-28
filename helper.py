from flask import Flask
from flask import current_app as app
from urllib.request import urlopen
from urllib.error import URLError
from dbHelper import getInvestmentAccounts
from forex_python.converter import CurrencyCodes
import re

# Load configuration from file
app = Flask(__name__)
app.config.from_object('config')


# Get currency symbol
def getCurrencySymbol(currencycode):
    codes = CurrencyCodes()
    symbol = codes.get_symbol(currencycode)
    return symbol


# Get Mutual Fund NAVs and store it in session
def mfNAV2File():
    nav_url = app.config['MFNAV_LINK']
    nav_file = app.config['MFNAV_FILE']
    try:
        response = urlopen(nav_url)
        mfnav = response.read().decode()
        response.close()
        with open(nav_file, 'w') as f:
            f.write(mfnav)
    except URLError:
        return None
    return True


# Get Nav of the given MF scheme code
def getNAV(code):
    nav = None
    if code:
        with open(app.config['MFNAV_FILE']) as f:
            data = f.read()
        navdetails = re.findall("%s.*" % code, data)
        nav = navdetails[0].split(';')[4]
        navDate = navdetails[0].split(';')[5]
    return [nav, navDate]


# Get Nav for all active and holding accounts for the given user
def getFundNAVDict(username):
    accounts = getInvestmentAccounts(username, "ActiveOrHold")
    navDict = {}
    for account in accounts:
        navDict[account[5]] = getNAV(account[5])
    return navDict
