import pygal
import calendar
from pygal.style import LightColorizedStyle
from dbHelper import getMonthlyInvestments


# Generate line chart for investment trend since beginning for a user
def investmentTrend(username):
    chart = pygal.Line(
      show_legend=False, pretty_print=True, show_y_guides=False,
      x_labels_major_every=5, x_labels_major_count=15,
      show_minor_x_labels=False,
      tooltip_border_radius=10, fill=True, height=350,
      style=LightColorizedStyle, dots_size=1, x_label_rotation=270
      )
    investment_data = []
    labelSeries = []
    investmentAllData = getMonthlyInvestments(username)
    if investmentAllData:
        for row in investmentAllData:
            (year, month) = (str(row[0])[:4], str(row[0])[4:])
            labelSeries.append("%s %s" % (year, calendar.month_abbr[int(month)]))
            investment_data.append(row[1])
        chart.x_labels = labelSeries
        chart.add('Investments', investment_data)
    else:
        chart.add('line', [])
    return chart.render_data_uri()
