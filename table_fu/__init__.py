#! /usr/bin/env python
"""
This is a Python version of Propublica's TableFu Ruby library.

TableFu parses, sorts and formats table-like streams, like CSVs,
and outputs tables in HTML. It's meant as a utility to make 
getting tabular on the web easier.
"""
import csv
import urllib2


class TableFu(object):
    """
    A table, to be manipulated like a spreadsheet.
    
    TableFu reads in an open CSV file, parsing it 
    into a table property, Row and Datum objects.
    
    Usage:
    
    # test.csv
    
    Author,Best Book,Number of Pages,Style
    Samuel Beckett,Malone Muert,120,Modernism
    James Joyce,Ulysses,644,Modernism
    Nicholson Baker,Mezannine,150,Minimalism
    Vladimir Sorokin,The Queue,263,Satire
    
    >>> spreadsheet = TableFu(open('../tests/test.csv'))
    >>> len(spreadsheet.rows)
    4
    >>> spreadsheet.columns
    ['Author', 'Best Book', 'Number of Pages', 'Style']
    >>> spreadsheet.columns = ['Style', 'Author']
    
    
    """
    def __init__(self, table, **options):
        """
        Takes a table argument and optional keyword arguments.

        The 'table' argument should be a two-dimensional array,
        either a list or tuple, or an open file that can be
        parsed by Python's csv module (using csv.reader)
        """
        if isinstance(table, file):
            reader = csv.reader(table)
            self.table = [row for row in reader]
        else:
            self.table = table
        self.default_columns = self.table.pop(0)
        self._columns = options.get('columns', [])
        self.deleted_rows = []
        self.faceted_by = None
        self.totals = {}
        self.options = options

    def __getitem__(self, row_num):
        """
        Return one row in the table
        """
        return Row(self.table[row_num], row_num, self)

    def __len__(self):
        return len(self.table[1:])

    def add_rows(self, *rows):
        for row in rows:
            self.table.append(row)

    @property
    def rows(self):
        return [Row(row, i, self) for i, row in enumerate(self.table)]

    def _get_columns(self):
        if self._columns:
            return self._columns
        return self.default_columns

    def _set_columns(self, columns):
        self._columns = self.options['columns'] = list(columns)

    columns = property(_get_columns, _set_columns)

    def delete_row(self, row_num):
        self.deleted_rows.append(self.table[row_num])
        del self.table[row_num]
    
    def sort(self, column_name):
        if column_name not in self.default_columns:
            raise ValueError("%s isn't a column in this table" % column_name)
        index = self.default_columns.index(column_name)
        self.table.sort(key = lambda row: row[index])

    def values(self, column_name):
        if column_name not in self.default_columns:
            raise ValueError("%s isn't a column in this table" % column_name)
        index = self.default_columns.index(column_name)
        return [row[index] for row in self.table]
    
    def total(self, column_name):
        if column_name not in self.default_columns:
            raise ValueError("%s isn't a column in this table" % column_name)
        
        try:
            values = [float(v) for v in self.values(column_name)]
        except ValueError:
            raise ValueError('Column %s contains non-numeric values' % column_name)
        
        return sum(values)

    def facet_by(self, column):
        """
        Faceting creates new TableFu instances with rows matching
        each possible value.
        """
        faceted_spreadsheets = {}
        for row in self.rows:
            if row[column]:
                faceted_spreadsheets[row[column].value] = []
                faceted_spreadsheets[row[column].value].append(row.cells)

        # create a new TableFu instance for each facet
        tables = []
        for k, v in faceted_spreadsheets.items():
            v.insert(0, self.default_columns)
            table = TableFu(v)
            table.faceted_on = k
            table.options = self.options
            tables.append(table)

        tables.sort(key=lambda t: t.faceted_on)
        return tables



class Row(object):
    """
    A row in a table

    Rows act like dictionaries, but look more like lists.
    Calling row['column'] returns a column lookup based on
    the default set of columns.
    """
    def __init__(self, cells, row_num, table):
        self.table = table
        self.row_num = row_num
        self.cells = list(cells)

    def __eq__(self, other):
        if not type(other) == type(self):
            return False
        return self.cells == other.cells

    def __len__(self):
        return len(self.cells)

    def __getitem__(self, column_name):
        if not column_name in self.table.default_columns:
            raise KeyError("%s isn't a column in this table" % column_name)
        index = self.table.columns.index(column_name)
        return Datum(self.cells[index], self.row_num, column_name, self.table)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, ', '.join([str(cell) for cell in self.cells]))


class Datum(object):
    """
    A piece of data, with a table, row and column
    """
    def __init__(self, value, row_num, column_name, table):
        self.value = value
        self.row_num = row_num
        self.column_name = column_name
        self.table = table

    def __repr__(self):
        return "<%s: %s>" % (self.column_name, self.value)
        
    def __str__(self):
        return self.value
