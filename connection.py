import pyodbc
from sqlalchemy import create_engine
from urllib.parse import quote_plus

def get_engine():
    """
    Creates and returns a SQLAlchemy engine for the database connection.
    """
    # Define the raw connection string for pyodbc
    raw_connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=sjbiosqldevn04.na.gilead.com;"
        "Database=MACRO;"
        "UID=macro;"
        "PWD=8B&y86y^ffwp;"
        "TrustServerCertificate=yes;"
    )
    #raw_connection_string = f'mssql+pyodbc:///?odbc_connect=Driver%%3D%%7BODBC+Driver+17+for+SQL+Server%%7D%%3BDATABASE%%3DMACRO%%3BUID%%3Dmacro%%3BSERVER%%3Dsjbiosqldevn04.na.gilead.com%%3BPWD%%3D8B%%26y86y%%5Effwp'
    # Test the connection using pyodbc
    try:
        conn = pyodbc.connect(raw_connection_string)
        print("Connection successful using pyodbc!")
        conn.close()
    except Exception as e:
        print(f"Connection failed using pyodbc: {e}")
        raise

    # URL-encode the connection string for SQLAlchemy
    encoded_connection_string = quote_plus(raw_connection_string)

    # Create the SQLAlchemy connection string
    sqlalchemy_connection_string = f"mssql+pyodbc:///?odbc_connect={encoded_connection_string}"

    # Create and return the SQLAlchemy engine
    try:
        engine = create_engine(sqlalchemy_connection_string)
        print("SQLAlchemy engine created successfully!")
        return engine
    except Exception as e:
        print(f"Failed to create SQLAlchemy engine: {e}")
        raise