import sqlite3
from pathlib import Path
from mappers.salary_mapper import SalaryMapper
from mappers.monthly_salary_mapper import MonthlySalaryMapper
from mappers.region_mapper import RegionMapper
from mappers.work_modes_mapper import WorkModesMapper
from mappers.work_schedules_mapper import WorkSchedulesMapper
from mappers.employment_type_mapper import EmploymentTypeMapper
from mappers.position_levels_mapper import PositionLevelsMapper
from mappers.industry_mapper import IndustryMapper
from mappers.language_mapper import LanguageMapper

class DatabaseCleaner:
    """
    Hlavní třída pro čištění databáze job offers
    Orchestruje všechny mappery
    """

    def __init__(self, db_path: str = None):
        # pokud uživatel nepředal db_path, najdi DB v rootu projektu (parent of db_cleaner/)
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'job_database.db'

        self.db_path = Path(db_path).resolve()
        self.conn = None
        self.mappers = []
        self.results = {}

    def __enter__(self):
        """Context manager - otevři connection"""
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)
        self._initialize_mappers()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - zavři connection"""
        if self.conn:
            self.conn.close()

    def _initialize_mappers(self):
        """Inicializuj všechny mappery"""
        self.mappers = [
            SalaryMapper(self.conn),
            MonthlySalaryMapper(self.conn),
            RegionMapper(self.conn),
            WorkModesMapper(self.conn),
            WorkSchedulesMapper(self.conn),
            EmploymentTypeMapper(self.conn),
            PositionLevelsMapper(self.conn),
            IndustryMapper(self.conn),
            LanguageMapper(self.conn), # Poslední - přidá sloupce v __init__
        ]

    def clean_all(self):
        """Spusť všechny mappery"""
        print("\n" + "=" * 100)
        print("🧹 DATABASE CLEANER - JOB OFFERS")
        print("=" * 100)

        total_updated = 0

        for i, mapper in enumerate(self.mappers, 1):
            print(f"\n🔄 KROK {i}/{len(self.mappers)}: {mapper.get_mapper_name()}")

            try:
                updated_count = mapper.clean_data()
                self.results[mapper.get_mapper_name()] = updated_count
                total_updated += updated_count

            except Exception as e:
                print(f"❌ Chyba v {mapper.get_mapper_name()}: {e}")
                import traceback
                traceback.print_exc()
                self.results[mapper.get_mapper_name()] = 0

        self._show_final_summary(total_updated)

        return self.results

    def _show_final_summary(self, total_updated: int):
        """Zobraz finální souhrn"""
        print("\n" + "=" * 100)
        print("🎉 ČIŠTĚNÍ DOKONČENO")
        print("=" * 100)

        for mapper_name, count in self.results.items():
            print(f"✅ {mapper_name:30} {count:,} řádků")

        print(f"✅ {'TOTAL UPDATES':30} {total_updated:,} řádků")
        print("=" * 100 + "\n")


def main():
    """Main entry point"""
    try:
        with DatabaseCleaner() as cleaner:
            cleaner.clean_all()

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()