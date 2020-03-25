import psycopg2

class Database:
    """
    provides a simple interface to the databse
    """

    def __init__(self, db_url):
        self.db = psycopg2.connect(db_url, sslmode='require')
        self.cursor = self.db.cursor()
        

    def add(self, table, key, value):
        self.cursor.execute("insert into {} values(%s,%s)".format(table), (key, value))
        self.db.commit()
    
    def edit(self, table, pk_name, key, value):
        self.remove(table, pk_name, key)
        self.add(table, key, value)
    
    def remove(self, table, pk_name, key):
        self.cursor.execute("delete from {} where {}=%s".format(table, pk_name), [key])
        self.db.commit()
    
    def get(self, table, pk_name, value_name, key):
        self.cursor.execute("select {} from {} where {}=%s".format(value_name, table, pk_name), [key])
        fetch = self.cursor.fetchall()
        if fetch:
            return fetch[0][0]
        else:
            raise KeyError
    
    def get_all_keys(self, table, pk_name):
        """
        table - the name of the table
        this function return a list of all of the available keys of the table specified
        """
        # this will return a list of tuples of names
        self.cursor.execute("select {} from {}".format(pk_name, table))
        # this takes the list of tuples and converts it to a list of keys and then sorts it alphabetically
        return sorted(x[0] for x in cursor.fetchall())


# wrappers for specific tables

class TableWrapper:
    """
    A generic wrapper around a table in the db.
    every other wrapper should inherit from this.
    """

    def __init__(self, db, table_name, pk_name, value_name):
        self.db = db
        self.table_name = table_name
        self.pk_name = pk_name
        self.value_name = value_name
    
    def add(self, key, value):
        self.db.add(self.table_name, key, value)
    
    def edit(self, key, value):
        self.db.edit(self.table_name, self.pk_name, key, value)
    
    def remove(self, key):
        self.db.remove(self.table_name, self.pk_name, key)
    
    def get(self, key):
        return self.db.get(self.table_name, self.pk_name, self.value_name, key)
    
    def get_all_keys(self):
        return self.db.get_all_keys(self.table_name, self.pk_name)

    def __contains__(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        if key in self:
            self.edit(key, value)
        else:
            self.add(key, value)
