from flask import Flask
from flask import current_app as app
from forex_python.converter import CurrencyRates, CurrencyCodes
from urllib.request import urlopen
from urllib.error import URLError
import os
import re
from dbHelper import ( getInvestmentAccounts )

# Load configuration from file
app = Flask(__name__)
app.config.from_object('config')

# Get currency list
def getCurrencyList():
  c = CurrencyRates()
  currencies = []
  curRates = c.get_rates('GBP')
  for item in curRates.keys():
    currencies.append(item)
  currencies.append('GBP')
  return sorted(currencies)

# Get conversion rate
def getConversionRate(fromcur, tocur, amount):
  c = CurrencyRates()
  codes = CurrencyCodes()
  converted = c.convert(fromcur, tocur, amount)
  fromSymbol = codes.get_symbol(fromcur)
  toSymbol = codes.get_symbol(tocur)
  conversion_result = "%s %0.2f = %s %0.2f" % (fromSymbol, amount, toSymbol, converted)
  return conversion_result

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
    mfnav = response.read()
    response.close()
    with open(nav_file, 'w') as f:
      f.write(mfnav)
  except URLError as e:
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
  return [nav,navDate]

# Get Nav for all active and holding accounts in a dictionary for the given user
def getFundNAVDict(username):
  accounts = getInvestmentAccounts(username, "ActiveOrHold")
  navDict = {}
  for account in accounts:
    navDict[account[5]] = getNAV(account[5])
  return navDict
