import psycopg2
from psycopg2 import sql
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CSVtoPostgresLoader:
    def __init__(self, db_name, csv_directory):
        self.db_name = db_name
        self.csv_directory = csv_directory
        self.admin_conn = None
        self.table_conn = None

    def create_database(self):
        """Create new PostgreSQL database"""
        try:
            self.admin_conn = psycopg2.connect(
                host=os.getenv('PG_HOST', 'localhost'),
                user=os.getenv('PG_USER', 'postgres'),
                password=os.getenv('PG_PASSWORD'),
                port=os.getenv('PG_PORT', '5432')
            )
            self.admin_conn.autocommit = True  # Required for DB creation
            
            with self.admin_conn.cursor() as cur:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(self.db_name)))
                print(f"Database {self.db_name} created successfully")
                
        except psycopg2.Error as e:
            print(f"Database creation error: {e}")
            raise
        finally:
            if self.admin_conn:
                self.admin_conn.close()

    def process_files(self):
        """Process all CSV files in directory"""
        try:
            self.table_conn = psycopg2.connect(
                host=os.getenv('PG_HOST', 'localhost'),
                dbname=self.db_name,
                user=os.getenv('PG_USER', 'postgres'),
                password=os.getenv('PG_PASSWORD'),
                port=os.getenv('PG_PORT', '5432')
            )

            for file in os.listdir(self.csv_directory):
                if file.endswith('.csv'):
                    filepath = os.path.join(self.csv_directory, file)
                    table_name = os.path.splitext(file)[0].lower()
                    self.create_table_from_csv(filepath, table_name)
                    self.import_csv_data(filepath, table_name)
                    
        except Exception as e:
            print(f"Error processing files: {e}")
            raise
        finally:
            if self.table_conn:
                self.table_conn.close()

    def create_table_from_csv(self, filepath, table_name):
        """Create table with inferred schema"""
        try:
            df = pd.read_csv(filepath, nrows=1)  # Just read header
            with self.table_conn.cursor() as cur:
                columns = []
                for col, dtype in df.dtypes.items():
                    pg_type = 'TEXT'  # Default
                    if 'int' in str(dtype):
                        pg_type = 'INTEGER'
                    elif 'float' in str(dtype):
                        pg_type = 'FLOAT'
                    elif 'date' in str(dtype):
                        pg_type = 'DATE'
                    columns.append(f"{col} {pg_type}")
                
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                cur.execute(create_sql)
                self.table_conn.commit()
                print(f"Created table {table_name}")
                
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
            self.table_conn.rollback()
            raise

    def import_csv_data(self, filepath, table_name):
        """Bulk import CSV data using COPY"""
        try:
            with self.table_conn.cursor() as cur:
                with open(filepath, 'r') as f:
                    cur.copy_expert(
                        f"COPY {table_name} FROM STDIN WITH CSV HEADER",
                        f
                    )
                self.table_conn.commit()
                print(f"Imported data to {table_name}")
                
        except Exception as e:
            print(f"Error importing to {table_name}: {e}")
            self.table_conn.rollback()
            raise

if __name__ == "__main__":
    # Example usage
    loader = CSVtoPostgresLoader(
        db_name="medical",
        csv_directory = os.getenv('CSVDIRECTORY'),
    )
    
    try:
        loader.create_database()
        loader.process_files()
    except Exception as e:
        print(f"Pipeline failed: {e}")
    finally:
        print("Process completed")