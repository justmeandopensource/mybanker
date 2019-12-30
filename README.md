## MyBanker New Edition
The new MyBanker Personal Finance Application

### Description
A web application written in Python using Flask framework. Its a personal finance application which you can use to track your day-to-day expenses. Some of the things you can do with it are

* Add/modify/delete accounts
* Record income and expenses
* Transfer funds between accounts
* Add/Remove expense/income categories
* View list of transactions
* View graphs for various reports
* Change user profile information

### Why I am developing this?
I had been using the original MyBanker web application which I wrote in HTML and PHP. The code was a complete mess and adding more features to the application consumed lot of time. I have not incorporated code reusability which makes things more difficult when it comes to adding new features.

So decided to completely start from the scratch and write in python this time. I am using Python Flask framework to develop this application.

### Note
*Please note that I am not a professional software developer. Just out of my interest in Python and Linux, I have started working on it.*

### How to setup MyBanker
* Clone this repo
* Install pip and inside the repo install all the python requirements using **sudo pip install -r requirements.cfg**
  * When I did this on a CentOS server, I had to install the following additional pacakges on the system
    * mariadb-devel
    * gcc
* Make sure you have a MySQL server that you can connect to and privilege to create database
* From the root of the repo run **python \_\_init\_\_.py**. It will start the web server on port **8888**. You can change this if you want in \_\_init\_\_.py
* You can access MyBanker at http://127.0.0.1:8888 or http://localhost:8888 or http://ipaddress:8888 from any other machine
* Or install Apache and configure it as reverse proxy to proxy the requests to 8003 on localhost. The other option is to go by wsgi script which I haven't included
