# Import Section
from flask import Flask
from flask import current_app as app
from flaskext.mysql import MySQL
from hashlib import sha256
from operator import itemgetter
import calendar
import gc

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL()
mysql.init_app(app)

# Method to load and run all queries from a file
# Run queries one by one and return on first failure
def runQueriesFromFile(queryfile):

  conn = mysql.connect()
  cursor = conn.cursor()

  # Read all queries first
  with open (queryfile, "r") as myFile:
    loadQuery = myFile.readlines()

  # Run query one by one and return on first failure
  for query in loadQuery:
    if query:
      try:
        cursor.execute(query)
        conn.commit()
      except Exception as e:
        return str(e)
  conn.close()
  gc.collect() 
  return "Success"

# Method to validate login credentials entered
def checkLogin(username, password):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    cursor.execute('SELECT password FROM users WHERE username = "%s"' % username)
    for row in cursor.fetchall():
      if sha256(password).hexdigest() == row[0]:
        return True
      else:
        return False
  except Exception as e:
    return False
  finally:
    conn.close()
    gc.collect()

# Get Name from Username
def getNameofUser(username):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    cursor.execute('SELECT name FROM users WHERE username = "%s"' % username)
    return cursor.fetchone()[0]
  except Exception as e:
    return False
  finally:
    conn.close()
    gc.collect()

# Method to add new user
def addUser(name, username, password, email):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "INSERT INTO users VALUES('%s', '%s', '%s', '%s', '%s', CURDATE())" % (name, username, 'no', sha256(password).hexdigest(), email)
    cursor.execute(query)
    conn.commit()
    # Send a welcome email to the new user
    mailSubject = "Welcome to MyBanker!"
    mailMsg = """
              Hi %s,
  
              Welcome to MyBanker, the Personal Finance Tracker.
              Please add new accounts and start tracking your incomes and expenses.

              Note:
              If you would like a new category that is not already listed, please send a message to the MyBanker admin \
              who will then be able to add the category for you

              Thanks,
              MyBanker Admin
              (The Super User)
              """ % name
    sendMessage("admin", mailSubject, mailMsg, username)
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()
  return "User %s added successfully" % name

# Method to update admin password
def updatePassword(username, currentpassword, newpassword):
  if currentpassword == newpassword:
    return "Funny! Idea here is to change password not set the same password again"
  conn = mysql.connect()
  cursor = conn.cursor()
  currentPW = sha256(currentpassword).hexdigest()
  newPW = sha256(newpassword).hexdigest()
  try:
    if checkLogin(username, currentpassword):
      query = "UPDATE users SET password='%s' WHERE username='%s' AND password='%s'" % (newPW, username, currentPW)
      cursor.execute(query)
      conn.commit()
      return "Password for %s updated successfully" % username
    else:
      return "Operation failed! Password didn't match"
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()

# List all users and send as dictionary
def listMybankerUsers():
  conn = mysql.connect()
  cursor = conn.cursor()
  userdict = []
  try:
    cursor.execute('SELECT * FROM users')
    userdict = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return userdict
    
# Get list of categories
def getCategories():
  conn = mysql.connect()
  cursor = conn.cursor()
  inc_categories = []
  exp_categories = []
  try:
    cursor.execute('SELECT name FROM categories WHERE type="IN"')
    for item in cursor.fetchall():
      inc_categories.append(item[0])
    cursor.execute('SELECT name FROM categories WHERE type="EX"')
    for item in cursor.fetchall():
      exp_categories.append(item[0])
  except:
    return None
  finally:
    conn.close()
    gc.collect()
  return inc_categories, exp_categories

# Add a new category
def addCategory(name, cat_type):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "INSERT INTO categories VALUES('%s', '%s')" % (name.upper(), cat_type)
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) == 0:
      conn.commit()
      returnstring = "New category %s added" % name
    else:
      returnstring = str(data[0])
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()
  return returnstring

# Check how many accounts a user has got
def checkTotalAccounts(username):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "SELECT COUNT(*) FROM accounts WHERE owner = '%s'" % username
    cursor.execute(query)
    accountsTotal = cursor.fetchone()[0]
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return accountsTotal

# Add a new account
def addAccountDB(accinfo):
  conn = mysql.connect()
  cursor = conn.cursor()
  # Hardcoded to GBP at the moment. Need to revisit
  currency = "GBP"
  try:
    query = "INSERT INTO accounts VALUES('%s','%s',%s,'%s',CURDATE(),CURDATE(),'%s','%s','%s')" % \
             (accinfo['name'], accinfo['owner'], accinfo['balance'], accinfo['notes'], accinfo['exclude'], currency, accinfo['type'])
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) == 0:
      conn.commit()
      returnString = "New account %s added" % accinfo['name']
    else:
      returnString = str(data[0])
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()
  return returnString

# Get accounts for dashboard table
def getAccounts(username, account="all"):
  conn = mysql.connect()
  cursor = conn.cursor()
  appendquery = ""
  if account != "all":
    appendquery = "AND name = '%s'" % account
  try:
    query = "SELECT name, balance, lastoperated, created, type, description, excludetotal FROM accounts WHERE owner = '%s' %s" % (username, appendquery)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get account transactions
def getTransactions(username, accountname, period, year, month):
  conn = mysql.connect()
  cursor = conn.cursor()
  advQuery = limitQuery = ''

  if 'normal' in period:
    limitQuery = 'LIMIT 20'

  if 'PRE_' in period:
    if 'thisweek' in period:
      advQuery = "AND YEARWEEK(opdate) = YEARWEEK(NOW())"
    elif 'lastweek' in period:
      advQuery = "AND YEARWEEK(opdate) = YEARWEEK(NOW())-1"
    elif 'thismonth' in period:
      advQuery = "AND YEAR(opdate) = YEAR(CURDATE()) AND MONTH(opdate) = MONTH(NOW())"
    elif 'lastmonth' in period:
      advQuery = "AND YEAR(opdate) = YEAR(CURDATE()) AND MONTH(opdate) = MONTH(NOW())-1"
    elif 'last5days' in period:
      advQuery = "AND opdate >= DATE_SUB(CURDATE(), INTERVAL 5 DAY)"
    elif 'last30days' in period:
      advQuery = "AND opdate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
  elif 'selective' in period:
    advQuery ="AND YEAR(opdate) = %s AND MONTH(opdate) = %s" % (year, month)

  try:
    query = "SELECT opdate, description, credit, debit, category \
             FROM transactions \
             WHERE owner = '%s' AND account = '%s' %s \
             ORDER BY opdate DESC %s" \
            % (username, accountname, advQuery, limitQuery)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get account transactions for a category
def getTransactionsForCategory(username, category, period=None, year=None, month=None):
  conn = mysql.connect()
  cursor = conn.cursor()
  advQuery = limitQuery = ''

  if period:
    if 'thisweek' in period:
      advQuery = "AND YEARWEEK(opdate) = YEARWEEK(NOW())"
    elif 'lastweek' in period:
      advQuery = "AND YEARWEEK(opdate) = YEARWEEK(NOW())-1"
    elif 'thismonth' in period:
      advQuery = "AND YEAR(opdate) = YEAR(CURDATE()) AND MONTH(opdate) = MONTH(NOW())"
    elif 'lastmonth' in period:
      advQuery = "AND YEAR(opdate) = YEAR(CURDATE()) AND MONTH(opdate) = MONTH(NOW())-1"
    elif 'last5days' in period:
      advQuery = "AND opdate >= DATE_SUB(CURDATE(), INTERVAL 5 DAY)"
    elif 'last30days' in period:
      advQuery = "AND opdate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
  else:
    if year and month:
      advQuery ="AND YEAR(opdate) = %s AND MONTH(opdate) = %s" % (year, month)
    else:
      limitQuery = "LIMIT 20"

  try:
    query = "SELECT opdate, description, credit, debit, account \
             FROM transactions \
             WHERE owner = '%s' AND category = '%s' %s \
             ORDER BY opdate DESC %s" \
            % (username, category, advQuery, limitQuery)
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) == 0:
      data = None
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Check category type
def getCategoryType(category):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "SELECT type FROM categories WHERE name = '%s'" % category
    cursor.execute(query)
    data = cursor.fetchone()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data[0]

# Add transaction
def addTransactionsDB(date, notes, amount, category, account, owner):
  conn = mysql.connect()
  cursor = conn.cursor()
  credit, debit, updatetype = ["NULL", amount, "debit"]
  if getCategoryType(category) == "IN":
    credit, debit, updatetype = [amount, "NULL", "credit"]
  try:
    query = "INSERT INTO transactions VALUES('%s', '%s', '%s', %s, %s, '%s', '%s')" % \
             (date, notes, category, credit, debit, account, owner)
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) == 0:
      conn.commit()
      if updateAccounts(account, owner, amount, updatetype):
        returnString = "Transaction added successfully"
      else:
        returnString = "Failed to update accounts table. But transaction recorded"
    else:
      returnString = str(data[0])
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()
  return returnString

# Get account Type
def checkAccountType(account, owner):
  conn = mysql.connect()
  cursor = conn.cursor()
  isassetAcc = True
  try:
    query = "SELECT type FROM accounts WHERE name = '%s' AND owner = '%s'" % \
             (account, owner)
    cursor.execute(query)
    data = cursor.fetchone()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  if data[0] == "L":
    isassetAcc = False
  return isassetAcc

# Update Balance in Accounts table
def updateAccounts(name, owner, amount, updatetype):
  conn = mysql.connect()
  cursor = conn.cursor()
  sign,operator = ["+", "-"]
  isassetAcc = checkAccountType(name, owner)
  if not isassetAcc:
    sign = "-"
  if updatetype == "credit":
    operator = "+"
  try:
    query = "UPDATE accounts \
             SET balance = balance %s %s%s, lastoperated = CURDATE() \
             WHERE name = '%s' AND owner = '%s'" % \
             (operator, sign, amount, name, owner)
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    return False
  finally:
    conn.close()
    gc.collect()
  return True

# Get networth of a user
def getNetworth(username):
  networth = 0.00
  accounts = getAccounts(username)
  for account in accounts:
    if 'yes' in account[6]:
      continue
    if 'L' in account[4]:
      networth = networth - float(account[1])
    else:
      networth = networth + float(account[1])
  return networth

# Get income/expense monthly/or since beginning for a user
def getInEx(username, year, period="selective"):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    if period == "selective":
      query = """
              SELECT name, COALESCE(SUM_DATA.credit, 0.00) AS credit, COALESCE(SUM_DATA.debit, 0.00) AS debit
              FROM months
              LEFT JOIN (
               SELECT MONTH(opdate) AS mnth, SUM(credit) AS credit, SUM(debit) AS debit
               FROM transactions
               WHERE owner = '%s'
                     AND YEAR(opdate) = %s
                     AND account NOT IN (%s)
                     AND category NOT IN ('OPENING BALANCE','TRANSFER IN','TRANSFER OUT')
               GROUP BY MONTH(opdate)
              ) SUM_DATA
              ON months.name = SUM_DATA.mnth
              ORDER BY months.name
              """ % (username, year, getIgnoredAccounts(username))
    else:
      query = """
              SELECT EXTRACT(YEAR_MONTH FROM opdate) AS period, SUM(credit) AS credit, SUM(debit) AS debit
              FROM transactions
              WHERE owner = '%s'
                    AND account NOT IN (%s)
                    AND category NOT IN ('OPENING BALANCE','TRANSFER IN','TRANSFER OUT')
              GROUP BY period
              ORDER BY period
              """ % (username, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get expense monthly since beginning for a user
def getEx(username):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = """
            SELECT YEAR(opdate), SUM(debit)
            FROM transactions
            WHERE owner = '%s'
                  AND YEAR(opdate) > 2013
                  AND account NOT IN (%s)
                  AND category NOT IN ('TRANSFER IN','TRANSFER OUT')
            GROUP BY EXTRACT(YEAR_MONTH FROM opdate)
            ORDER BY EXTRACT(YEAR_MONTH FROM opdate)
            """ % (username, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get income/expense yearly since beginning for a user
def getInExYearly(username):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = """
            SELECT YEAR(opdate), SUM(credit), SUM(debit)
            FROM transactions
            WHERE owner = '%s'
                  AND YEAR(opdate) > 2013
                  AND account NOT IN (%s)
                  AND category NOT IN ('OPENING BALANCE','TRANSFER IN','TRANSFER OUT')
            GROUP BY YEAR(opdate)
            ORDER BY YEAR(opdate)
            """ % (username, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get expense stats for a specific year
def getExpenseStats(username, year):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = """
            SELECT category, SUM(debit) AS debit
            FROM transactions t1
            INNER JOIN (
              SELECT name
              FROM categories
              WHERE type = 'EX' AND name NOT IN ('TRANSFER OUT')
            ) t2
            ON t1.category = t2.name
            WHERE YEAR(t1.opdate) = %s AND t1.owner = '%s' AND account NOT IN (%s)
            GROUP BY t1.category
            ORDER BY debit DESC
            """ % (year, username, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get category stats for specific category for specific user
def getCategoryStats(username, category, period="YEAR_MONTH"):
  conn = mysql.connect()
  cursor = conn.cursor()
  optype = "debit"
  if getCategoryType(category) == "IN":
    optype = "credit"
  try:
    query = """
            SELECT EXTRACT(%s FROM opdate) AS period, SUM(%s) AS %s
            FROM transactions
            WHERE owner = '%s'
                  AND category = '%s'
                  AND account NOT IN (%s)
                  AND category NOT IN ('TRANSFER IN','TRANSFER OUT')
            GROUP BY period
            ORDER BY period
            """ % (period, optype, optype, username, category, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get category stats for specific category for specific user for specific year for dot graph
def getCategoryStatsForYear(username, category, year):
  conn = mysql.connect()
  cursor = conn.cursor()
  optype = "debit"
  if getCategoryType(category) == "IN":
    optype = "credit"
  try:
    query = """
            SELECT SUM_DATA.year, COALESCE(SUM_DATA.%s, 0.00) AS %s
            FROM months
            LEFT JOIN (
              SELECT YEAR(opdate) AS year, MONTH(opdate) AS month, SUM(%s) AS %s
              FROM transactions
              WHERE owner = '%s'
                    AND YEAR(opdate) = %s
                    AND category = '%s'
                    AND category NOT IN ('TRANSFER IN','TRANSFER OUT')
                    AND account NOT IN (%s)
              GROUP BY MONTH(opdate)
            ) SUM_DATA
            ON months.name = SUM_DATA.month
            ORDER BY months.name
            """ % (optype, optype, optype, optype, username, year, category, getIgnoredAccounts(username))
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get distinct year where we have transactions for the give category
def getTransactionYearsCategory(username, category):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = """
            SELECT DISTINCT(YEAR(opdate))
            FROM transactions
            WHERE owner = '%s'
                  AND category = '%s'
                  AND YEAR(opdate) > 2013
            ORDER BY YEAR(opdate) DESC
            """ % (username, category)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get category stats for each year in a separate list for all years
# It will be list of lists
def getCategoryStatsAllYears(username, category):
  years = getTransactionYearsCategory(username, category)
  data = []
  if years:
    for year in years:
      data.append(getCategoryStatsForYear(username, category, year[0]))
    return data
  else:
    return None

# Get category stats to fill previous and current month expenses in reports
def getAllCategoryStatsForMonth(username, month):
  # month: 0 - current, 1 - previous
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = """
            SELECT category, SUM(debit) AS debit
            FROM transactions
            WHERE owner = '%s'
                  AND EXTRACT(YEAR_MONTH FROM opdate) = EXTRACT(YEAR_MONTH FROM CURDATE() - INTERVAL %s MONTH)
                  AND debit IS NOT NULL
                  AND category NOT IN ('TRANSFER OUT')
            GROUP BY category
            ORDER BY debit DESC
            """ % (username, month)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get category stats to fill previous and current month expenses in reports
def getAllCategoryStatsForYear(username, year):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = """
            SELECT category, SUM(debit) AS debit
            FROM transactions
            WHERE owner = '%s'
                  AND YEAR(opdate) = '%s'
                  AND debit IS NOT NULL
                  AND category NOT IN ('TRANSFER OUT')
            GROUP BY category
            ORDER BY debit DESC
            """ % (username, year)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get accounts that are excluded
def getIgnoredAccounts(username):
  ignoreAccounts = []
  accounts = getAccounts(username)
  for account in accounts:
    if account[6] == 'yes':
      ignoreAccounts.append('"%s"' % account[0])
  return ",".join(ignoreAccounts)

# Do some maths to get more detailed category stats
def getDetailedCategoryStats(data, period="YEAR_MONTH"):
  if data is None:
    return None
  else:
    # Find total spent in this category since beginning
    totalSpent = sum(item[1] for item in data)
    periodAvg = float(totalSpent) / float(len(data))
    periodAvg = "%.2f" % periodAvg
    sortedData = sorted(data, key=itemgetter(1))
    if period == "YEAR_MONTH":
      lowestPeriod = "%s %s" % (calendar.month_name[sortedData[0][0] % 100], str(sortedData[0][0])[:-2])
      highestPeriod = "%s %s" % (calendar.month_name[sortedData[-1][0] % 100], str(sortedData[-1][0])[:-2])
    else:
      lowestPeriod = sortedData[0][0]
      highestPeriod = sortedData[-1][0]
    lowest = [lowestPeriod, sortedData[0][1]]
    highest = [highestPeriod, sortedData[-1][1]]
    categoryStatsData = [totalSpent, periodAvg, highest, lowest]
    return categoryStatsData

# Get transactions for keyword search
def searchTransactions(username, keyword):
  conn = mysql.connect()
  cursor = conn.cursor()

  try:
    query = "SELECT opdate, description, credit, debit, category, account \
             FROM transactions \
             WHERE owner = '%s' AND description like '%%%s%%' \
             ORDER BY opdate DESC" \
            % (username,keyword)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get messages for a user
def getInbox(username, msgid=None):
  conn = mysql.connect()
  cursor = conn.cursor()
  extraQuery = ""
  if msgid:
    extraQuery = "AND id = %s" % msgid
  try:
    query = "SELECT * FROM messages WHERE owner = '%s' %s ORDER BY indate DESC" % (username, extraQuery)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get total messages and unread count for a user
def getInboxCount(username, msgtype="total"):
  conn = mysql.connect()
  cursor = conn.cursor()
  extraQuery = ""
  if msgtype == "read":
    extraQuery = "AND status = 'R'"
  elif msgtype == "unread":
    extraQuery = "AND status = 'N'"
  try:
    query = "SELECT COUNT(*) FROM messages WHERE owner = '%s' %s" % (username, extraQuery)
    cursor.execute(query)
    data = cursor.fetchone()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data[0]

# Delete a given message
def deleteMessageDB(msgid):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "DELETE FROM messages WHERE id = %s" % msgid
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return True 

# Upload message sent to database
def sendMessage(owner, subject, message, touser):
  conn = mysql.connect()
  cursor = conn.cursor()
  returnString = "Message successfully sent to %s" % touser
  try:
    query = "INSERT INTO messages VALUES (NULL, CURDATE(), '%s', '%s', '%s', '%s', 'N')" % (touser, subject, message.replace("\n", "<br>"), getNameofUser(owner))
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) == 0:
      conn.commit()
    else:
      returnString = str(data[0])
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()
  return returnString

# Mark message read
def markMsgRead(msgid):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "UPDATE messages SET status = 'R' WHERE id = %s" % msgid
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return True

# Delete user accounts - delete all data from database
def removeUser(user=None):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    cursor.execute("DELETE FROM accounts WHERE owner = '%s'" % user)
    cursor.execute("DELETE FROM messages WHERE owner = '%s'" % user)
    cursor.execute("DELETE FROM transactions WHERE owner = '%s'" % user)
    cursor.execute("DELETE FROM users WHERE username = '%s'" % user)
    conn.commit()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return True 

# Check total investment accounts
def checkTotalInvestmentAccounts(username):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "SELECT COUNT(*) FROM investmentaccounts WHERE owner = '%s'" % username
    cursor.execute(query)
    accountsTotal = cursor.fetchone()[0]
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return accountsTotal

# Add a new investment account
def addInvestmentAccountDB(accinfo):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "INSERT INTO investmentaccounts \
             VALUES(%s, '%s', '%s', '%s', '%s', '%s', \
                   '%s', '%s', '%s', '%s', '%s', '%s', \
                   '%s', 0.00, 0.00, 'Active', CURDATE(), \
                   '%s', '%s', '%s', '%s', 0.00)" % \
             (accinfo['accid'], accinfo['owner'], accinfo['name'], accinfo['plan'], accinfo['folio'], \
              accinfo['schemecode'], accinfo['company'], accinfo['email'], accinfo['phone'], \
              accinfo['address'], accinfo['linkedbank'], accinfo['sipstart'], accinfo['sipend'], \
              accinfo['url'], accinfo['urluser'], accinfo['urlpass'], accinfo['notes'])
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) == 0:
      conn.commit()
      returnString = "New account %s added" % accinfo['name']
    else:
      returnString = str(data[0])
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()
  return returnString

# Add a new investment account
def updateInvestmentAccountDB(accinfo):
  conn = mysql.connect()
  cursor = conn.cursor()
  try:
    query = "UPDATE investmentaccounts \
             SET name='%s', \
                 plan='%s', \
                 company='%s', \
                 email='%s', \
                 phone='%s', \
                 address='%s', \
                 linkedbank='%s', \
                 sipstart='%s', \
                 sipend='%s', \
                 url='%s', \
                 urluser='%s', \
                 urlpass='%s', \
                 notes='%s' \
             WHERE accid=%s" % \
             (accinfo['name'], accinfo['plan'], accinfo['company'], accinfo['email'], accinfo['phone'], \
              accinfo['address'], accinfo['linkedbank'], accinfo['sipstart'], accinfo['sipend'], \
              accinfo['url'], accinfo['urluser'], accinfo['urlpass'], accinfo['notes'], accinfo['accid'])
    cursor.execute(query)
    conn.commit()
    returnString = "Account updated successfully"
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()
  return returnString

# Get investment accounts for dashboard table
def getInvestmentAccounts(username, accounttype="All"):
  conn = mysql.connect()
  cursor = conn.cursor()
  appendQuery = ""

  if accounttype == "ActiveOrHold":
    appendQuery = "AND status in ('Active', 'Holding')"
  elif accounttype != "All":
    appendQuery = "AND status = '%s'" % accounttype

  try:
    query = "SELECT accid, name, invested, balanceunits, lastoperated, schemecode, closingvalue \
             FROM investmentaccounts \
             WHERE owner = '%s' %s \
             ORDER BY lastoperated DESC" % (username, appendQuery)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get a specific investment account information
def getInvestmentAccount(username, accid):
  conn = mysql.connect()
  cursor = conn.cursor()

  try:
    query = "SELECT * \
             FROM investmentaccounts \
             WHERE owner = '%s' AND accid = %s \
             ORDER BY accid" % (username, accid)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get investment account transactions
def getInvestmentTransactions(username, accid):
  conn = mysql.connect()
  cursor = conn.cursor()

  try:
    query = "SELECT * \
             FROM investmenttransactions \
             WHERE owner = '%s' AND accid = '%s' \
             ORDER BY opdate DESC" \
            % (username, accid)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

# Get balance units for given investment
def getBalanceUnitsMF(username, accid):
  conn = mysql.connect()
  cursor = conn.cursor()

  try:
    query = "SELECT balanceunits \
             FROM investmentaccounts \
             WHERE owner = '%s' AND accid = '%s'" \
             % (username, accid)
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data[0][0]

# Add sip transactions
def addSIPTransaction(sipinfo):
  conn = mysql.connect()
  cursor = conn.cursor()

  origBalanceUnits = getBalanceUnitsMF(sipinfo['owner'], sipinfo['accid'])
  purchasedUnits = float(sipinfo['units'])
  newBalanceUnits = float(origBalanceUnits) + purchasedUnits

  sipamount = float(sipinfo['amount'])

  try:
    query = "INSERT INTO investmenttransactions VALUES(%s, '%s', %d, %0.3f, %0.3f, '%s')" \
            % (sipinfo['accid'], sipinfo['sipdate'], sipamount, purchasedUnits, newBalanceUnits, sipinfo['owner'])
    cursor.execute(query)
    data = cursor.fetchall()
    if len(data) == 0:
      conn.commit()
      returnString = "Sip transaction added "
      msg = updateInvestmentAccounts(sipinfo['accid'], sipinfo['owner'], sipamount, newBalanceUnits, sipinfo['sipdate'])
      returnString = returnString + msg
    else:
      returnString = str(data[0])
  except Exception as e:
    return str(e)
  finally:
    conn.close()
    gc.collect()
  return returnString

# Update investment accounts after adding sip transactions
def updateInvestmentAccounts(accid, owner, amount, balanceunits, opdate):
  conn = mysql.connect()
  cursor = conn.cursor()

  try:
    query = "UPDATE investmentaccounts \
             SET invested=invested+%d, \
                 balanceunits=%0.3f, \
                 lastoperated='%s' \
             WHERE accid='%s' AND owner='%s'" \
             % (amount, balanceunits, opdate, accid, owner)
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    return "Exception occurred while updating investment accounts"
  finally:
    conn.close()
    gc.collect()
  return "Investment account updated!"

# Update status of Investment accounts
def updateInvestmentAccountStatus(accid, owner, status, closingvalue=0.00):
  conn = mysql.connect()
  cursor = conn.cursor()

  try:
    query = "UPDATE investmentaccounts \
             SET status='%s', \
                 closingvalue=%s, \
                 notes=CONCAT(notes, ' [Account status changed to %s ', CURDATE(), ']') \
             WHERE accid='%s' AND owner='%s'" \
             % (status, closingvalue, status, accid, owner)
    cursor.execute(query)
    conn.commit()
  except Exception as e:
    return "Exception occurred while updating status of the account"
  finally:
    conn.close()
    gc.collect()
  return "Account status changed to %s!!" % status

# Get monthly investments made
# To be fed to the line chart in investment dashboard
def getMonthlyInvestments(username):
  conn = mysql.connect()
  cursor = conn.cursor()

  try:
    query = "SELECT EXTRACT(YEAR_MONTH FROM opdate) AS Period, SUM(sipamount) AS Amount \
             FROM investmenttransactions \
             WHERE owner = '%s' \
             GROUP BY Period \
             ORDER BY Period" \
            % username
    cursor.execute(query)
    data = cursor.fetchall()
  except Exception as e:
    return None
  finally:
    conn.close()
    gc.collect()
  return data

