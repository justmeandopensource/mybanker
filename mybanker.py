# Imports section
from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from dbHelper import (addInvestmentAccountDB, addSIPTransaction,
                      checkTotalInvestmentAccounts, getInvestmentAccount,
                      getInvestmentAccounts, getInvestmentTransactions,
                      updateInvestmentAccountDB, updateInvestmentAccountStatus)
from helper import getCurrencySymbol, getFundNAVDict, getNAV, mfNAV2File
from reportHelper import investmentTrend

# Initialize Flask object
app = Flask(__name__)
app.secret_key = 'i234aessser54234lajdflkjasdlkjf;oiuqaewrlrl'

# Load configuration from file
app.config.from_object('config')


# Investments Route
@app.route('/')
def investments():
    session['username'] = 'venkatn'
    # Currency symbol hardcoded for INR. Revisit for dynamic feature
    currencySymbol = getCurrencySymbol('INR')
    totalAccounts = checkTotalInvestmentAccounts(session['username'])
    accountsAvailable = activeAccounts = holdingAccounts = closedAccounts = None
    investmentTrendGraph = None
    navdict = None
    if totalAccounts == 0:
        flash("You don't have any investment accounts\nPlease add your investment details")
    else:
        #mfNAV2File()
        accountsAvailable = "yes"
        activeAccounts = getInvestmentAccounts(session['username'], 'Active')
        holdingAccounts = getInvestmentAccounts(session['username'], 'Holding')
        closedAccounts = getInvestmentAccounts(session['username'], 'Closed')
        investmentTrendGraph = investmentTrend(session['username'])
        navdict = getFundNAVDict(session['username'])
    return render_template('investments.html',
                           accountsAvailable=accountsAvailable,
                           activeAccounts=activeAccounts,
                           holdingAccounts=holdingAccounts,
                           closedAccounts=closedAccounts,
                           currencySymbol=currencySymbol,
                           investmentTrendGraph=investmentTrendGraph,
                           navdict=navdict)


# Refresh stocks
@app.route('/refreshstocks')
def refreshstocks():
    mfNAV2File()
    return redirect(url_for('investments'))


# Add new investment Route
@app.route('/addinvestment', methods=['GET', 'POST'])
def addinvestment():
    if request.method == "POST":
        accinfo = {}
        accinfo['accid'] = request.form['accountid']
        accinfo['owner'] = session['username']
        accinfo['name'] = request.form['accountname']
        accinfo['plan'] = request.form['plan']
        accinfo['folio'] = request.form['folio']
        accinfo['schemecode'] = request.form['schemecode']
        accinfo['company'] = request.form['company']
        accinfo['email'] = request.form['email']
        accinfo['phone'] = request.form['phone']
        accinfo['address'] = request.form['address']
        accinfo['linkedbank'] = request.form['bank']
        accinfo['sipstart'] = request.form['sipstart']
        accinfo['sipend'] = request.form['sipend']
        accinfo['url'] = request.form['url']
        accinfo['urluser'] = request.form['urluser']
        accinfo['urlpass'] = request.form['urlpass']
        accinfo['notes'] = request.form['notes']
        flash(addInvestmentAccountDB(accinfo))
    return render_template('addinvestment.html')


# Edit existing Investment Route
@app.route('/editinvestment', methods=['POST'])
@app.route('/editinvestment/<accid>', methods=['GET'])
def editinvestment(accid=None):
    if request.method == "GET":
        acc_details = getInvestmentAccount(session['username'], accid)
        return render_template('editinvestment.html', acc_details=acc_details)
    else:
        accinfo = {}
        accinfo['accid'] = request.form['accountid']
        accinfo['owner'] = session['username']
        accinfo['name'] = request.form['accountname']
        accinfo['plan'] = request.form['plan']
        accinfo['folio'] = request.form['folio']
        accinfo['schemecode'] = request.form['schemecode']
        accinfo['company'] = request.form['company']
        accinfo['email'] = request.form['email']
        accinfo['phone'] = request.form['phone']
        accinfo['address'] = request.form['address']
        accinfo['linkedbank'] = request.form['bank']
        accinfo['sipstart'] = request.form['sipstart']
        accinfo['sipend'] = request.form['sipend']
        accinfo['url'] = request.form['url']
        accinfo['urluser'] = request.form['urluser']
        accinfo['urlpass'] = request.form['urlpass']
        accinfo['notes'] = request.form['notes']
        flash(updateInvestmentAccountDB(accinfo))
        return redirect(url_for('investment_transactions', username=session['username'], accid=accinfo['accid'], action='list'))


# Investment individual account details Route
@app.route('/<username>/investments/<accid>/<action>', methods=['GET', 'POST'])
def investment_transactions(username, accid, action):
    nav = 0.00
    closingvalue = 0.00
    if request.method == "POST":
        closingvalue = request.form['amount']
        if closingvalue == "":
            flash("Please re-try with closing amount entered!!")
        else:
            flash(updateInvestmentAccountStatus(
                accid, username, action, closingvalue))
    if action == "Holding":
        flash(updateInvestmentAccountStatus(
            accid, username, action, closingvalue))
    currencySymbol = getCurrencySymbol('INR')
    transactions = accinfo = None
    if username and accid:
        transactions = getInvestmentTransactions(username, accid)
        accinfo = getInvestmentAccount(username, accid)
        nav = getNAV(accinfo[0][5])
    return render_template('investment-transactions.html',
                           transactions=transactions,
                           accinfo=accinfo,
                           currencySymbol=currencySymbol,
                           nav=nav)


# Add SIP Transaction Route
@app.route('/addsip', methods=['GET', 'POST'])
def addsip():
    activeAccounts = None
    if request.method == "POST":
        sipinfo = {}
        sipinfo['owner'] = session['username']
        sipinfo['accid'] = request.form['accid']
        sipinfo['amount'] = request.form['amount']
        sipinfo['units'] = request.form['units']
        sipinfo['sipdate'] = request.form['sipdate']
        flash(addSIPTransaction(sipinfo))
    totalAccounts = checkTotalInvestmentAccounts(session['username'])
    if totalAccounts == 0:
        flash("You don't have any investment accounts\nPlease add your investment details")
    else:
        activeAccounts = getInvestmentAccounts(session['username'], 'Active')
    return render_template('addsip.html', accounts=activeAccounts)


# Main Function
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True, threaded=True)
