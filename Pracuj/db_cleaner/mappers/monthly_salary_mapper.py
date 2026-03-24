from typing import Optional, Dict, Any, List

from base_mapper import BaseMapper


class MonthlySalaryMapper(BaseMapper):
    """
    Mapper pro výpočet monthly_max_salary z salary_max / salary_min.

    Logika:
      salary_max IS NOT NULL:
        < 1000  → salary_max * 160  (hodinová → měsíční)
        >= 1000 → salary_max        (již měsíční)

      salary_max IS NULL, salary_min IS NOT NULL:
        >= 5000 → salary_min        (fallback)
        <  5000 → None              (filtr kvality dat)

      obojí NULL → None
    """

    HOURLY_THRESHOLD = 1000    # PLN — hodnoty pod tímto limitem = hodinová sazba
    HOURS_PER_MONTH = 160      # 8 h/den × 20 pracovních dnů
    SALARY_MIN_THRESHOLD = 5000

    def __init__(self, conn):
        super().__init__(conn)
        self._ensure_column_exists()

    # ──────────────────────────────────────────────
    # DB schema
    # ──────────────────────────────────────────────

    def _ensure_column_exists(self):
        """Přidá sloupec monthly_max_salary do job_offers, pokud neexistuje."""
        self.cursor.execute("PRAGMA table_info(job_offers)")
        existing_columns = [row[1] for row in self.cursor.fetchall()]
        if "monthly_max_salary" not in existing_columns:
            self.cursor.execute("ALTER TABLE job_offers ADD COLUMN monthly_max_salary REAL")
            self.conn.commit()
            print("➕ Sloupec 'monthly_max_salary' byl přidán do tabulky job_offers")

    # ──────────────────────────────────────────────
    # BaseMapper API
    # ──────────────────────────────────────────────

    def get_mapper_name(self) -> str:
        return "MONTHLY SALARY DATA"

    def get_emoji(self) -> str:
        return "📊"

    def get_column_name(self) -> str:
        return "monthly_max_salary"

    def get_select_query(self) -> str:
        return """
            SELECT partition_id, company, url, salary_min, salary_max
            FROM job_offers
            WHERE (salary_max IS NOT NULL OR salary_min IS NOT NULL)
              AND monthly_max_salary IS NULL
        """

    def get_update_query(self) -> str:
        return """
            UPDATE job_offers
            SET monthly_max_salary = ?
            WHERE partition_id = ?
        """

    def process_row(self, row: tuple) -> Optional[Dict[str, Any]]:
        partition_id, company, url, salary_min, salary_max = row

        monthly = self._compute_monthly_max_salary(salary_max, salary_min)
        if monthly is None:
            return None

        return {
            "partition_id": partition_id,
            "company": company,
            "url": url,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "monthly_max_salary": monthly,
        }

    def prepare_update_params(self, update_data: Dict[str, Any]) -> tuple:
        return (update_data["monthly_max_salary"], update_data["partition_id"])

    # ──────────────────────────────────────────────
    # Core logic
    # ──────────────────────────────────────────────

    def _compute_monthly_max_salary(self, salary_max, salary_min) -> Optional[float]:
        """
        Transformuje salary na monthly_max_salary.
        Identická logika jako v nerds_db_filter.compute_monthly_max_salary.
        """
        try:
            if salary_max is not None:
                val_max = float(salary_max)
                if val_max < self.HOURLY_THRESHOLD:
                    return round(val_max * self.HOURS_PER_MONTH, 2)
                else:
                    return val_max

            elif salary_min is not None:
                val_min = float(salary_min)
                if val_min > self.SALARY_MIN_THRESHOLD:
                    return val_min
                else:
                    return None

            else:
                return None

        except (TypeError, ValueError):
            return None

    # ──────────────────────────────────────────────
    # Output / logging
    # ──────────────────────────────────────────────

    def show_example(self, index: int, data: Dict[str, Any]):
        sal_min = data["salary_min"]
        sal_max = data["salary_max"]
        monthly = data["monthly_max_salary"]

        source = f"{sal_min:,.0f} - {sal_max:,.0f}" if sal_max else f"{sal_min:,.0f} (min only)"
        print(f"[{index}] Company: {data['company'][:50]}")
        print(f"    URL:     {data['url']}")
        print(f"    Salary:  {source}")
        print(f"    Monthly: {monthly:,.2f}\n")

    def show_statistics(self, updates_data: List[Dict[str, Any]], unchanged_count: int):
        from_max = sum(1 for d in updates_data if d["salary_max"] is not None)
        from_min_fallback = sum(1 for d in updates_data if d["salary_max"] is None)
        hourly_converted = sum(
            1 for d in updates_data
            if d["salary_max"] is not None and float(d["salary_max"]) < self.HOURLY_THRESHOLD
        )
        kept_as_is = from_max - hourly_converted

        print("=" * 100)
        print(f"📈 VÝSLEDKY ANALÝZY - {self.get_mapper_name()}")
        print("=" * 100)
        print(f"✅ Nalezeno {len(updates_data)} řádků k updatu:")
        print(f"   • Ze salary_max (kept as-is, >= {self.HOURLY_THRESHOLD}):  {kept_as_is}")
        print(f"   • Ze salary_max (hourly × {self.HOURS_PER_MONTH}):          {hourly_converted}")
        print(f"   • Fallback ze salary_min (>= {self.SALARY_MIN_THRESHOLD}):  {from_min_fallback}")
        print(f"   • Přeskočeno (nelze vypočítat):        {unchanged_count}")
        print(f"\n   Celkem k updatu: {len(updates_data)} řádků\n")
