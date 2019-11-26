import os
dia = 'mysql'
dri = 'pymysql'
username = 'root'
password = 'F=mdv/dt123'
host = '127.0.0.1'
port = '3306'
database = 'PTCG'

SQLALCHEMY_DATABASE_URI="{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(dia,dri,username,password,host,port,database)

SQLALCHEMY_TRACK_MODIFICATIONS=True

Debug=True

# SECRET_KEY=os.urandom(24)
SECRET_KEY=b'-=&\xa3\xf4\xc2\x0e\xa0\x82\xe4\xdc\x01_v\x82\xdd\xe5\xd3\xe3\xd5\xceWCN'