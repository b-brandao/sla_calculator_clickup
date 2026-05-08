from datetime import datetime, timedelta, time
import holidays


class SLACalculator:
    """
    Calcula SLA em horas úteis (08:00 às 20:00),
    desconsiderando finais de semana e feriados brasileiros.
    """

    WORK_START = time(8, 0)
    WORK_END = time(20, 0)
    DAILY_WORK_HOURS = 12  # 20 - 8

    def __init__(self):
        self.br_holidays = holidays.Brazil()

    def is_business_day(self, d: datetime) -> bool:
        if d.weekday() >= 5:  # 5=sáb, 6=dom
            return False
        if d.date() in self.br_holidays:
            return False
        return True

    def business_seconds_between(self, start_dt: datetime, end_dt: datetime) -> int:
        """Retorna o total de SEGUNDOS úteis entre dois datetimes."""
        if end_dt <= start_dt:
            return 0

        total_seconds = 0.0
        current = start_dt

        while current.date() <= end_dt.date():
            if self.is_business_day(current):
                day_start = datetime.combine(current.date(), self.WORK_START)
                day_end = datetime.combine(current.date(), self.WORK_END)

                interval_start = max(current, day_start)
                interval_end = min(end_dt, day_end)

                if interval_end > interval_start:
                    total_seconds += (interval_end - interval_start).total_seconds()

            # próximo dia 00:00
            current = datetime.combine(current.date() + timedelta(days=1), time(0, 0))

        return int(total_seconds)

    @staticmethod
    def seconds_to_hhmmss(total_seconds: int) -> str:
        """Converte segundos para o formato HH:MM:SS (suporta mais de 24h)."""
        if total_seconds is None or total_seconds < 0:
            return "00:00:00"

        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def calculate_sla(self, date_created_ms: str, reference_dt: datetime = None) -> str:
        """
        Calcula o SLA em horas úteis no formato HH:MM:SS,
        a partir do date_created (timestamp em ms) até o momento de referência (default: agora).
        """
        if not date_created_ms:
            return "00:00:00"

        created = datetime.fromtimestamp(int(date_created_ms) / 1000)
        ref = reference_dt or datetime.now()

        total_seconds = self.business_seconds_between(created, ref)
        return self.seconds_to_hhmmss(total_seconds)