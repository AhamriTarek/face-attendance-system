# Use mysqlclient (MySQLdb) when available (local dev). On the cloud build where
# only the pure-Python PyMySQL is installed, transparently use it as MySQLdb so
# the Django mysql backend works without compiling C extensions.
try:
    import MySQLdb  # noqa: F401  (mysqlclient — local)
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()
