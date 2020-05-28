# Import Section
from flask import Flask
from flask import current_app as app
from flaskext.mysql import MySQL
import gc

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL()
mysql.init_app(app)


# Check total investment accounts
def checkTotalInvestmentAccounts(username):
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        query = "SELECT COUNT(*) FROM investmentaccounts WHERE owner = '%s'" % username
        cursor.execute(query)
        accountsTotal = cursor.fetchone()[0]
    except Exception:
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
            (accinfo['accid'], accinfo['owner'], accinfo['name'], accinfo['plan'], accinfo['folio'],
             accinfo['schemecode'], accinfo['company'], accinfo['email'], accinfo['phone'],
             accinfo['address'], accinfo['linkedbank'], accinfo['sipstart'], accinfo['sipend'],
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
            (accinfo['name'], accinfo['plan'], accinfo['company'], accinfo['email'], accinfo['phone'],
             accinfo['address'], accinfo['linkedbank'], accinfo['sipstart'], accinfo['sipend'],
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
    except Exception:
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
    except Exception:
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
    except Exception:
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
    except Exception:
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
            msg = updateInvestmentAccounts(
                sipinfo['accid'], sipinfo['owner'], sipamount, newBalanceUnits, sipinfo['sipdate'])
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
    except Exception:
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
    except Exception:
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
    except Exception:
        return None
    finally:
        conn.close()
        gc.collect()
    return data
