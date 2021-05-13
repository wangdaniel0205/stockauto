from datetime import datetime, timedelta

x = datetime.today() - timedelta(days=200)

print(x.strftime("%Y%m%d"))
