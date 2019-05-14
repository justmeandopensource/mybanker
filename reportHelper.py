from flask import current_app as app
import pygal
import calendar
from pygal.style import LightColorizedStyle
from dbHelper import (
                       getInEx, getInExYearly, getEx, getExpenseStats, getCategoryStats, 
                       getCategoryStatsAllYears, getDetailedCategoryStats, getMonthlyInvestments
                     )

# Generate bar chart for income/expense for the selected year
def inexTrend(username, year):
  chart = pygal.Bar(legend_at_bottom=True, show_y_labels=False, pretty_print=True, tooltip_border_radius=10, height=750)
  chart.x_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  income_data = []
  expense_data = []
  inexdata = getInEx(username, year)
  if inexdata:
    for row in inexdata:
      income_data.append(row[1])
      expense_data.append(row[2])
    chart.add('Income', income_data)
    chart.add('Expense', expense_data)
  else:
    chart.add('line', [])
  return chart.render_data_uri()

# Generate pie chart for expense stats for the selected year
def expenseStats(username, year):
  chart = pygal.Pie(legend_at_bottom=True, tooltip_border_radius=10, height=750, inner_radius=.4)
  expensedata = getExpenseStats(username, year)
  if expensedata:
    for row in expensedata:
      chart.add(row[0], row[1])
  else:
    chart.add('line',[])
  return chart.render_data_uri()

# Generate bar chart for expense stats for the selected year
def expenseStatsBar(username, year):
  chart = pygal.HorizontalBar(legend_at_bottom=True, tooltip_border_radius=10, height=750)
  expensedata = getExpenseStats(username, year)
  if expensedata:
    for row in expensedata:
      chart.add(row[0], row[1])
  else:
    chart.add('line',[])
  return chart.render_data_uri()

# Generate line chart for income expense trend since beginning for a user
def inexTrendAll(username):
  chart = pygal.Line(legend_at_bottom=True, pretty_print=True, tooltip_border_radius=10, fill=True, height=400, style=LightColorizedStyle, dots_size=1, x_label_rotation=270)
  income_data = []
  expense_data = []
  labelSeries = []
  inexAllData = getInEx(username, None, "all")
  if inexAllData:
    for row in inexAllData:
      (year,month) = (str(row[0])[:4], str(row[0])[4:])
      labelSeries.append("%s %s" % (year, calendar.month_abbr[int(month)]))
      income_data.append(row[1])
      expense_data.append(row[2])
    chart.x_labels = labelSeries
    chart.add('Income', income_data)
    chart.add('Expense', expense_data)
  else:
    chart.add('line', [])
  return chart.render_data_uri()

# Generate line chart for income expense yearly trend since beginning for a user
def inexTrendYearlyAll(username):
  chart = pygal.Bar(legend_at_bottom=True, legend_at_bottom_columns=3, pretty_print=True, tooltip_border_radius=10, height=300, style=LightColorizedStyle)
  income_data = []
  expense_data = []
  savings_data = []
  labelSeries = []
  inexAllYearlyData = getInExYearly(username)
  if inexAllYearlyData:
    for row in inexAllYearlyData:
      labelSeries.append(row[0])
      income_data.append(row[1])
      expense_data.append(row[2])
      savings_data.append(row[1] - row[2])
    chart.x_labels = labelSeries
    chart.add('Income', income_data)
    chart.add('Expense', expense_data)
    chart.add('Savings', savings_data)
  else:
    chart.add('line', [])
  return chart.render_data_uri()

# Generate dot chart for expense trend since beginning for a user
def exTrendAll(username):
  chart = pygal.Dot(show_legend=False)
  exAllData = getEx(username)
  chart.x_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'AVG']
  if exAllData:
    yearList = set(x[0] for x in exAllData)
    for year in reversed(sorted(yearList)):
      expenses = [x[1] for x in exAllData if x[0] == year]
      if len(expenses) == 12:
        expenses.append(int(sum(expenses)/len(expenses)))
      chart.add('%s' % year, expenses)
  else:
    chart.add('line', [])
  return chart.render_data_uri()

# Generate line chart for category
def categoryStats(username, category, period="YEAR_MONTH"):
  chart = pygal.Line(tooltip_border_radius=10, fill=True, style=LightColorizedStyle, height=350, dot_size=1, x_label_rotation=270, show_legend=False)
  periodAbr = "Yearly"
  periodAbr = "Monthly" if "MONTH" in period else periodAbr
  chart.title = "(%s) Stats for category: %s" % (periodAbr, category)
  dataSeries = []
  labelSeries = []
  statsdata = None
  data = getCategoryStats(username, category, period)
  if data:
    statsdata = getDetailedCategoryStats(data, period)
    for row in data:
      if period == "YEAR_MONTH":
        (year,month) = (str(row[0])[:4], str(row[0])[4:])
        labelSeries.append("%s %s" % (year, calendar.month_abbr[int(month)]))
      else:
        labelSeries.append(row[0])
      dataSeries.append(row[1])
    chart.x_labels = labelSeries
    maxY = int(max(dataSeries))
    maxYRounded = (int(maxY / 100) + 1) * 100
    chart.y_labels = [0, maxYRounded]
    chart.add(category, dataSeries)
  else:
    chart.add('line',[])  
  return chart.render_data_uri(), statsdata

# Generate Dot graph for give category all year since beginning
def categoryAllGraphDot(username, category):
  chart = pygal.Dot(show_legend=False)
  data = getCategoryStatsAllYears(username, category)
  chart.x_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'AVG']
  if data:
    for row in data:
      if row:
        year = set(x[0] for x in row if x[0] is not None)
        expenses = [x[1] for x in row]
        expenses.append(int(sum(expenses)/len(expenses)))
        chart.add('%s' % next(iter(year)), expenses)
  else:
    chart.add('line',[])
  return chart.render_data_uri()

# Generate line chart for investment trend since beginning for a user
def investmentTrend(username):
  chart = pygal.Line(show_legend=False, pretty_print=True, show_y_guides=False, x_labels_major_every=5, x_labels_major_count=15, show_minor_x_labels=False, tooltip_border_radius=10, fill=True, height=350, style=LightColorizedStyle, dots_size=1, x_label_rotation=270)
  investment_data = []
  labelSeries = []
  investmentAllData = getMonthlyInvestments(username)
  if investmentAllData:
    for row in investmentAllData:
      (year,month) = (str(row[0])[:4], str(row[0])[4:])
      labelSeries.append("%s %s" % (year, calendar.month_abbr[int(month)]))
      investment_data.append(row[1])
    chart.x_labels = labelSeries
    chart.add('Investments', investment_data)
  else:
    chart.add('line', [])
  return chart.render_data_uri()

