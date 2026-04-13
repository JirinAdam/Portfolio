import sqlite3
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple


class BaseMapper(ABC):
    """
    Abstract base class pro všechny database mappery/cleanery
    Template method pattern pro konzistentní chování
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.cursor = conn.cursor()
        self.updated_count = 0
        self.blank_to_null_count = 0

    @abstractmethod
    def get_mapper_name(self) -> str:
        """Vrať název mapperu pro logging"""
        pass

    @abstractmethod
    def get_emoji(self) -> str:
        """Vrať emoji pro logging"""
        pass

    @abstractmethod
    def get_column_name(self) -> str:
        """Vrať jméno sloupce, který se čistí"""
        pass

    @abstractmethod
    def get_select_query(self) -> str:
        """Vrať SELECT query pro získání dat k čištění"""
        pass

    @abstractmethod
    def get_update_query(self) -> str:
        """Vrať UPDATE query pro aktualizaci dat"""
        pass

    @abstractmethod
    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        """Zpracuj jeden řádek a vrať update data nebo None"""
        pass

    @abstractmethod
    def prepare_update_params(self, update_data: Dict[str, Any]) -> tuple:
        """Připrav parametry pro UPDATE query"""
        pass

    @abstractmethod
    def show_example(self, index: int, data: Dict[str, Any]):
        """Zobraz jeden příklad aktualizace"""
        pass

    @abstractmethod
    def show_statistics(self, updates_data: List[Dict[str, Any]], unchanged_count: int):
        """Zobraz custom statistiky"""
        pass

    # ========== BLANK → NULL CONVERSION ==========

    def convert_blank_to_null(self) -> int:
        """
        Převeď prázdné stringy '' na NULL v aktuálním sloupci
        Vrať počet konvertovaných řádků
        """
        column = self.get_column_name()

        self.cursor.execute(f'''
            SELECT COUNT(*) FROM job_offers 
            WHERE {column} = ''
        ''')

        blank_count = self.cursor.fetchone()[0]

        if blank_count == 0:
            return 0

        self.cursor.execute(f'''
            UPDATE job_offers 
            SET {column} = NULL 
            WHERE {column} = ''
        ''')

        self.conn.commit()
        self.blank_to_null_count = blank_count

        return blank_count

    # ========== LOGGING METODY ==========

    def log_header(self):
        """Zobraz hlavičku pro tento mapper"""
        print("\n" + "=" * 100)
        print(f"{self.get_emoji()} ČIŠTĚNÍ {self.get_mapper_name().upper()}")
        print("=" * 100 + "\n")

    def log_blank_conversion(self, count: int):
        """Zobraz informaci o BLANK → NULL konverzi"""
        if count > 0:
            print(f"🔄 BLANK → NULL konverze: {count} řádků")
            print()

    def get_rows_to_process(self) -> List[tuple]:
        """Získej všechny řádky k zpracování"""
        self.cursor.execute(self.get_select_query())
        return self.cursor.fetchall()

    def process_all_rows(self, rows: List[tuple]) -> Tuple[List[Dict[str, Any]], int]:
        """Zpracuj všechny řádky a vrať seznam update dat + počet beze změn"""
        updates_data = []
        unchanged_count = 0

        for row in rows:
            update_data = self.process_row(row)
            if update_data:
                updates_data.append(update_data)
            else:
                unchanged_count += 1

        return updates_data, unchanged_count

    def confirm_update(self) -> bool:
        """Potvrď aktualizaci od uživatele"""
        print("=" * 100)
        user_input = input(
            f"👉 POKRAČOVAT V UPDATU {self.get_mapper_name().upper()}? (y/n): "
        ).strip().lower()
        print("=" * 100 + "\n")
        return user_input == 'y'

    def update_database(self, updates_data: List[Dict[str, Any]]):
        """Proved aktualizaci databáze"""
        print("📾 UPDATUJU DATA...\n")

        for update_data in updates_data:
            params = self.prepare_update_params(update_data)

            # ✅ Převeď prázdné stringy na NULL před uložením
            clean_params = tuple(None if isinstance(p, str) and p.strip() == '' else p for p in params)

            self.cursor.execute(self.get_update_query(), clean_params)
            self.updated_count += 1

        self.conn.commit()
        print(f"✅ Aktualizováno {self.updated_count} řádků\n")

    def show_examples(self, updates_data: List[Dict[str, Any]], limit: int = 10):
        """Zobraz příklady aktualizací"""
        print("=" * 100)
        print(f"📋 PRVNÍCH {min(limit, len(updates_data))} PŘÍKLADŮ - {self.get_mapper_name().upper()}")
        print("=" * 100 + "\n")

        for i, data in enumerate(updates_data[:limit], 1):
            self.show_example(i, data)

    def clean_data(self) -> int:
        """
        Hlavní metoda pro čištění dat
        Template method pattern
        """
        self.log_header()

        # 1. Konvertuj BLANK → NULL
        blank_count = self.convert_blank_to_null()
        self.log_blank_conversion(blank_count)

        # 2. Získej řádky k zpracování
        rows = self.get_rows_to_process()

        if not rows:
            print(f"✅ Žádné řádky k updatu pro {self.get_mapper_name()}\n")
            return self.blank_to_null_count

        print(f"📌 Nalezeno {len(rows)} řádků k analýze\n")
        print(f"📊 ZPRACOVÁVÁM DATA...\n")

        # 3. Zpracuj řádky
        updates_data, unchanged_count = self.process_all_rows(rows)

        if not updates_data:
            print(f"✅ Všech {unchanged_count} řádků jsou již OK\n")
            return self.blank_to_null_count

        # 4. Zobraz statistiky
        self.show_statistics(updates_data, unchanged_count)

        # 5. Potvrď od uživatele
        if not self.confirm_update():
            print(f"❌ {self.get_mapper_name()} update zrušen\n")
            return self.blank_to_null_count

        # 6. Update databáze
        self.update_database(updates_data)

        # 7. Zobraz příklady
        self.show_examples(updates_data)



        return self.blank_to_null_count + self.updated_count

