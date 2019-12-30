# Imports section
from flask import Flask, render_template, request, session, flash, url_for, redirect
from functools import wraps
import fileinput, gc
from datetime import date, datetime
from reportHelper import (
         inexTrend, expenseStats, expenseStatsBar, inexTrendAll, inexTrendYearlyAll, 
         exTrendAll, categoryStats, categoryAllGraphDot, investmentTrend
         )
from helper import ( 
         getCurrencyList, getConversionRate, getCurrencySymbol, 
         mfNAV2File, getFundNAVDict, getNAV 
         )
from dbHelper import (
         runQueriesFromFile, checkLogin, getNameofUser, addUser, 
         updatePassword, listMybankerUsers, getCategories, addCategory, 
         checkTotalAccounts, addAccountDB, getAccounts, getTransactions,
         getCategoryType, addTransactionsDB, getNetworth, getInbox,
         getInboxCount, deleteMessageDB, sendMessage, markMsgRead,
         searchTransactions, getTransactionsForCategory, getAllCategoryStatsForMonth,
         getAllCategoryStatsForYear,removeUser, checkTotalInvestmentAccounts, addInvestmentAccountDB,
         getInvestmentAccount, getInvestmentAccounts, getInvestmentTransactions,
         addSIPTransaction, updateInvestmentAccountStatus, updateInvestmentAccountDB
         )

# Initialize Flask object
app = Flask(__name__)
app.secret_key = 'i234aessser54234lajdflkjasdlkjf;oiuqaewrlrl'

# Load configuration from file
app.config.from_object('config')

# Login_required decorator
def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      return render_template('index.html', message=None)
  return decorated_function

# Index Route 
@app.route('/')
def index():
  if app.config['INITIAL_SETUP'].lower() != 'done':
    return render_template('install_welcome.html')
  else:
    return render_template('index.html', message=None)

# Login Dashboard Route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
  dashboard = 'dashboard.html'
  dashboard_admin = 'dashboard_admin.html'
  jumbomessage = None
  accounts = None
  networth = 0.00
  inexAllGraph = exAllGraph = inexYearlyAllGraph = None
  unread = None
  if not request.method == "POST":
    if 'logged_in' in session:
      if session['username'] == 'admin':
        return render_template(dashboard_admin)
      jumbomessage = dashboardMessage(session['username'])
      if checkTotalAccounts(session['username']) != 0:
        accounts = getAccounts(session['username'])
        networth = getNetworth(session['username'])
        inexAllGraph = inexTrendAll(session['username'])
        exAllGraph = exTrendAll(session['username'])
        inexYearlyAllGraph = inexTrendYearlyAll(session['username'])
      unreadCount = getInboxCount(session['username'], "unread")
      if unreadCount > 0:
        unread = unreadCount
      return render_template(dashboard, jumbomessage=jumbomessage, accounts=accounts, networth=networth, inexAllGraph=inexAllGraph, inexYearlyAllGraph=inexYearlyAllGraph, exAllGraph=exAllGraph, unread=unread)
    return render_template('index.html', message="You need to login first", mtype="warning")
  username = request.form['username']
  password = request.form['password']
  if checkLogin(username, password):
    session['logged_in'] = True
    session['username'] = username
    session['user'] = getNameofUser(username)
    if username == "admin":
      return render_template(dashboard_admin)
    else:
      # Check if user has investment accounts
      if not checkTotalInvestmentAccounts(session['username']) == 0:
        # Fetch MF NAV data to temp file
        mfNAV2File() 
      jumbomessage = dashboardMessage(username)
      if checkTotalAccounts(username) != 0:
        accounts = getAccounts(username)
        networth = getNetworth(username)
        inexAllGraph = inexTrendAll(session['username'])
        inexYearlyAllGraph = inexTrendYearlyAll(session['username'])
        exAllGraph = exTrendAll(session['username'])
      unreadCount = getInboxCount(session['username'], "unread")
      if unreadCount > 0:
        unread = unreadCount
      return render_template(dashboard, jumbomessage=jumbomessage, accounts=accounts, networth=networth, inexAllGraph=inexAllGraph, inexYearlyAllGraph=inexYearlyAllGraph, exAllGraph=exAllGraph, unread=unread)
  else:
    return render_template('index.html', message="Invalid credentials. Please try again", mtype="danger")

def dashboardMessage(username):
  jumbomessage = []
  # Check how many accounts the user has got
  accounts = checkTotalAccounts(username)
  if accounts == 0:
    jumbomessage.append("You don't have any accounts setup. Please add a new account to manage and start tracking.")
  else:
    jumbomessage.append("You have %s accounts configured." % accounts)
  return jumbomessage

# Setup MyBanker Route
@app.route('/setup', methods=['GET', 'POST'])
def setup():
  # Check if the application is already configured
  if app.config['INITIAL_SETUP'] == 'done':
    return render_template('setupdone.html')

  queryResult = runQueriesFromFile("templates/mybanker-initial.sql")
  if not "Success" in queryResult:
    flash("Error while trying to populate database : %s" % queryResult)
    return render_template('install_welcome.html')

  app.config['INITIAL_SETUP'] = 'done'
  
  # Update config file to mark initial setup as complete
  for line in fileinput.input("config.py", inplace=True):
    print(line.replace("pending", "done")),

  return render_template('install_complete.html')

# Logout Route
@app.route('/logout')
@login_required
def logout():
  session.clear()
  return render_template('index.html', message="You have been logged out!", mtype="info")

# Add User route
@app.route('/adduser', methods=['GET', 'POST'])
@login_required
def adduser():
  if request.method == "POST":
    name = request.form['name']
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    data = addUser(name, username, password, email)
    flash(data)
  return render_template('adduser.html')

# Remove User route
@app.route('/removeuser/<username>')
@login_required
def removeuser(username):
  message=None
  if username:
    user = getNameofUser(username)
    if user:
      if removeUser(username):
        message = "User %s successfully removed from MyBanker" % user
      else:
        message = "Something wasn't quite right. Removing %s account failed." % user
  userdict = listMybankerUsers()
  return render_template('listuser.html', userdict=userdict, message=message, mtype="info")

# Change Admin Password route
@app.route('/changePass', methods=['GET', 'POST'])
@login_required
def changePass():
  if request.method == "POST":
    currentPW = request.form['currentpw']
    newPW = request.form['newpw']
    data = updatePassword(session['username'], currentPW, newPW)
    flash(data)
  return render_template('change_pass.html', username=session['username'])

# List User Route
@app.route('/listuser')
@login_required
def listuser():
  userdict = listMybankerUsers()
  return render_template('listuser.html', userdict=userdict, message=None)

# Manage categories Route
@app.route('/managecategories', methods=['GET', 'POST'])
@login_required
def managecategories():
  if request.method == "POST":
    if 'incategory' in request.form:
      data = addCategory(request.form['incategory'], 'IN')
    else:
      data = addCategory(request.form['excategory'], 'EX')
    flash(data)
  inc_categories, exp_categories = getCategories()
  return render_template('managecategories.html', inc_categories=inc_categories, exp_categories=exp_categories)

# Add Account Route
@app.route('/addaccount', methods=['GET', 'POST'])
@login_required
def addaccount():
  if request.method == "POST":
    accinfo = {}
    accinfo['name'] = request.form['accountname']
    accinfo['owner'] = session['username']
    accinfo['balance'] = request.form['accountbalance']
    accinfo['notes'] = request.form['accountnotes']
    accinfo['exclude'] = 'no'
    if 'exclude' in request.form:
      accinfo['exclude'] = 'yes'
    accinfo['type'] = 'A'
    if request.form['accounttype'] == 'liability':
      accinfo['type'] = 'L'
    flash(addAccountDB(accinfo))
  return render_template('addaccount.html')

# Account Transactions Route
@app.route('/<username>/account/<accountname>/<period>', methods=['GET', 'POST'])
@login_required
def account_transactions(username, accountname, period):
  transactions = year = month = None
  curyear = datetime.now().year
  if username and accountname and period:
    if request.method == "POST":
      year = request.form['year']
      month = request.form['month']
    transactions = getTransactions(username, accountname, period, year, month)
    accinfo = getAccounts(username, accountname)
  return render_template('account-transactions.html', username=username, accinfo=accinfo, transactions=transactions, curyear=curyear)

# Add a new transaction Route
@app.route('/addtransaction', methods=['GET', 'POST'])
@login_required
def addtransaction():
  if checkTotalAccounts(session['username']) == 0:
    flash("Please add an account first before trying to add a transaction!!")
    jumbomessage = dashboardMessage(session['username'])
    return render_template('dashboard.html', jumbomessage=jumbomessage)
  inc_categories, exp_categories = getCategories()
  categories = exp_categories + inc_categories
  accounts = getAccounts(session['username'])
  if request.method == "POST":
    account = request.form['account']
    category = request.form['category']
    amount = request.form['amount']
    date = request.form['date']
    notes = request.form['notes']
    flash(addTransactionsDB(date, notes, amount, category, account, session['username']))
  return render_template('addtransaction.html', categories=categories, accounts=accounts)

# Transfer funds Route
@app.route('/transferfunds', methods=['GET', 'POST'])
@login_required
def transferfunds():
  if checkTotalAccounts(session['username']) == 0:
    flash("Please add some accounts first before trying to transfer funds!!")
    jumbomessage = dashboardMessage(session['username'])
    return render_template('dashboard.html', jumbomessage=jumbomessage)
  accounts = getAccounts(session['username'])
  if request.method == "POST":
    fromacc = request.form['fromaccount']
    toacc = request.form['toaccount']
    amount = request.form['amount']
    date = request.form['date']
    notes = request.form['notes']
    addTransactionsDB(date, notes, amount, "TRANSFER OUT", fromacc, session['username'])
    addTransactionsDB(date, notes, amount, "TRANSFER IN", toacc, session['username'])
    flash("Funds transferred from %s to %s successfully" % (fromacc, toacc))
  return render_template('transferfunds.html', accounts=accounts)

# Search Route
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
  searchresults = listresults = None
  curyear = datetime.now().year
  if request.method == "POST":
    if request.form['searchForm'] == "search":
      keyword = request.form['keyword']
      searchresults = searchTransactions(session['username'], keyword)
    else:
      category = request.form['listcategory']
      period = request.form['period']
      year = request.form['year']
      month = request.form['month']
      if category == "Select":
        flash("Please choose a category")
      else:
        if "Select" in period and "Select" in year and "Select" in month:
          listresults = getTransactionsForCategory(session['username'], category, None, None, None)
        elif not "Select" in period:
          listresults = getTransactionsForCategory(session['username'], category, period, None, None)
        elif not "Select" in year and not "Select" in month:
          listresults = getTransactionsForCategory(session['username'], category, None, year, month)
        else:
          flash("Please choose period carefully. If you didn't select one of the predefined period, you have to select both year and month")
        if listresults is None:
          flash("No transacations to list")
  categories = getCategories()
  return render_template('searchtransactions.html', searchresults=searchresults, listresults=listresults, categories=categories, curyear=curyear)


# Current vs Previous month expenses Route
@app.route('/curvsprevexpenses', methods=['GET'])
@login_required
def curvsprevexpenses():
  if checkTotalAccounts(session['username']) == 0:
    flash("No reports as you don't have any accounts setup. Please start adding your accounts")
    jumbomessage = dashboardMessage(session['username'])
    return render_template('dashboard.html', jumbomessage=jumbomessage)
  prevmnthexpenses = getAllCategoryStatsForMonth(session['username'], 1)
  curmnthexpenses = getAllCategoryStatsForMonth(session['username'], 0)
  return render_template('curvsprevmonthexpenses.html',
                          prevmnthexpenses=prevmnthexpenses,
                          curmnthexpenses=curmnthexpenses)

# Category stats Route
@app.route('/categorystats', methods=['GET', 'POST'])
@login_required
def categorystats():
  if checkTotalAccounts(session['username']) == 0:
    flash("No reports as you don't have any accounts setup. Please start adding your accounts")
    jumbomessage = dashboardMessage(session['username'])
    return render_template('dashboard.html', jumbomessage=jumbomessage)
  categoryStatsGraph = categoryStatsGraphYearly = None
  categoryStatsData = categoryStatsDataYearly = None
  categoryAllGraph = None
  if request.method == "POST":
    statcategory = request.form['statcategory']
    categoryStatsGraph, categoryStatsData = categoryStats(session['username'], statcategory, "YEAR_MONTH")
    categoryStatsGraphYearly, categoryStatsDataYearly = categoryStats(session['username'], statcategory, "YEAR")
    categoryAllGraph = categoryAllGraphDot(session['username'], statcategory)
  categoriesRaw = getCategories()
  categories = ([x for x in categoriesRaw[0] if x != "TRANSFER IN"], [x for x in categoriesRaw[1] if x != "TRANSFER OUT"])
  return render_template('categorystats.html',
                          categories=categories,
                          categoryStatsGraph=categoryStatsGraph,
                          categoryStatsData=categoryStatsData,
                          categoryStatsGraphYearly=categoryStatsGraphYearly,
                          categoryStatsDataYearly=categoryStatsDataYearly,
                          categoryAllGraph=categoryAllGraph)

# Year at a glance Route
@app.route('/yearataglance', methods=['GET', 'POST'])
@login_required
def yearataglance():
  if checkTotalAccounts(session['username']) == 0:
    flash("No reports as you don't have any accounts setup. Please start adding your accounts")
    jumbomessage = dashboardMessage(session['username'])
    return render_template('dashboard.html', jumbomessage=jumbomessage)
  year = curyear = date.today().year
  if request.method == "POST":
      year = request.form['year']
  yearexpenses = getAllCategoryStatsForYear(session['username'], year)
  inexGraph = inexTrend(session['username'], year)
  expenseGraph = expenseStats(session['username'], year)
  expenseBarGraph = expenseStatsBar(session['username'], year)
  return render_template('yearataglance.html',
                          inexGraph=inexGraph,
                          expenseGraph=expenseGraph,
                          expenseBarGraph=expenseBarGraph,
                          yearexpenses=yearexpenses,
                          curyear=curyear, year=year)

# Messages Route
@app.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
  mails = getInbox(session['username'])
  unread = getInboxCount(session['username'], "unread")
  tousers = listMybankerUsers()
  users = [name for name in tousers if name[1] != session['username']]
  return render_template('messages.html', mails=mails, unread=unread, users=users)

# Delete message Route
@app.route('/deletemessage/<msgid>')
@login_required
def deletemessage(msgid):
  if deleteMessageDB(msgid):
    flash("Message deleted")
  else:
    flash("Delete operation failed")
  return redirect(url_for('messages'))

# Send message Route
@app.route('/sendmessage', methods=['GET', 'POST'])
@login_required
def sendmessage():
  if request.method == "POST":
    subject = request.form['subject']
    message = request.form['message']
    touser = request.form['touser']
    flash(sendMessage(session['username'], subject, message, touser))
    return redirect(url_for('messages'))
  else:
    return redirect(url_for('messages'))

# View Message Route
@app.route('/viewmessage/<msgid>')
@login_required
def viewmessage(msgid):
  mail = getInbox(session['username'], msgid)
  markMsgRead(msgid)
  return render_template('viewmessage.html', mail=mail)

# Currency Rates Route
@app.route('/currencyrates', methods=['GET', 'POST'])
@login_required
def currencyrates():
  currencyList = getCurrencyList()
  conversion_result = None
  if request.method == "POST":
    amount = float(request.form['amount'])
    if "fromcur" in request.form and "tocur" in request.form:
      fromcur = request.form['fromcur']
      tocur = request.form['tocur']
      if fromcur == tocur:
        flash("From and To currencies identical. Please choose carefully.")
      else:
        conversion_result = getConversionRate(fromcur, tocur, amount)
    else:
      flash("Please choose desired currency from the dropdown!")
  return render_template('currencyrates.html', currencyList=currencyList, conversion_result=conversion_result)

# Investments Route
@app.route('/investments')
@login_required
def investments():
  # Currency symbol hardcoded for INR. Revisit for dynamic feature
  currencySymbol = getCurrencySymbol('INR')
  totalAccounts = checkTotalInvestmentAccounts(session['username'])
  accountsAvailable = activeAccounts = holdingAccounts = closedAccounts = None
  investmentTrendGraph = None
  navdict = None
  if totalAccounts == 0:
    flash("You don't have any investment accounts\nPlease add your investment details")
  else:
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

# Add new investment Route
@app.route('/addinvestment', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def investment_transactions(username, accid, action):
  nav = 0.00
  closingvalue = 0.00
  if request.method == "POST":
    closingvalue = request.form['amount']
    if closingvalue == "":
      flash("Please re-try with closing amount entered!!")
    else:
      flash(updateInvestmentAccountStatus(accid, username, action, closingvalue))
  if action == "Holding":
    flash(updateInvestmentAccountStatus(accid, username, action, closingvalue))
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
@login_required
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
  app.run(host="0.0.0.0", port=8003, debug=True, threaded=True)
